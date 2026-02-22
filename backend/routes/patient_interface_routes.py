from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional
import sqlite3
import json
from datetime import datetime

router = APIRouter(prefix="/api/patient-interface", tags=["patient-interface"])

class PatientLogin(BaseModel):
    phn: str

class PatientAnswer(BaseModel):
    response_id: int
    answer: str

class PatientInterface:
    def __init__(self, db_path: str = "./pv.db"):
        self.db_path = db_path
    
    def get_patient_by_phn(self, phn: str) -> Optional[Dict]:
        """Get patient information by PHN"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT pc.case_id, pc.patient_initials, pc.contact_no,
                   COUNT(pr.id) as total_questions,
                   SUM(CASE WHEN pr.is_correct = 1 THEN 1 ELSE 0 END) as answered_submitted,
                   SUM(CASE WHEN pr.is_correct = 0 OR pr.is_correct IS NULL THEN 1 ELSE 0 END) as pending
            FROM patient_comparisons pc
            LEFT JOIN patient_responses pr ON pc.case_id = pr.case_id
            WHERE pc.contact_no = ?
            GROUP BY pc.case_id, pc.patient_initials, pc.contact_no
        ''', (phn,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'case_id': result[0],
                'patient_initials': result[1],
                'contact_no': result[2],
                'total_questions': result[3] or 0,
                'answered_submitted': result[4] or 0,
                'pending': result[5] or 0,
                'completion_percentage': ((result[4] or 0) / (result[3] or 1)) * 100
            }
        return None
    
    def get_questions_by_phn(self, phn: str) -> List[Dict]:
        """Get pending questions for a patient by PHN"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.id, pr.case_id, pr.field_name, pr.question, 
                   pr.expected_answer, pc.patient_initials
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            WHERE pc.contact_no = ? AND (pr.is_correct = 0 OR pr.is_correct IS NULL)
            ORDER BY pr.field_name
        ''', (phn,))
        
        questions = []
        for row in cursor.fetchall():
            questions.append({
                'response_id': row[0],
                'case_id': row[1],
                'field_name': row[2],
                'question': row[3],
                'expected_answer': row[4],
                'patient_initials': row[5]
            })
        
        conn.close()
        return questions
    
    def submit_answer(self, response_id: int, answer: str) -> Dict:
        """Submit patient answer and update progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get response details
        cursor.execute('''
            SELECT expected_answer, case_id FROM patient_responses WHERE id = ?
        ''', (response_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="Response not found")
        
        expected_answer = str(result[0])
        case_id = result[1]
        # Mark as submitted (1) instead of checking correctness
        is_submitted = 1
        
        # Update response
        cursor.execute('''
            UPDATE patient_responses 
            SET patient_answer = ?, is_correct = ?, responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (answer, is_submitted, response_id))
        
        # Get updated progress
        cursor.execute('''
            SELECT 
                COUNT(*) as total_questions,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as answered_submitted,
                SUM(CASE WHEN is_correct = 0 OR is_correct IS NULL THEN 1 ELSE 0 END) as pending
            FROM patient_responses
            WHERE case_id = ?
        ''', (case_id,))
        
        progress = cursor.fetchone()
        
        # Check if all questions are answered for risk assessment
        risk_assessment = None
        if progress and progress[2] == 0:  # No pending questions
            risk_assessment = self._assess_risk(case_id, conn, cursor)
        
        conn.commit()
        conn.close()
        
        return {
            'is_submitted': True,
            'total_questions': progress[0] if progress else 0,
            'answered_submitted': progress[1] if progress else 0,
            'pending': progress[2] if progress else 0,
            'completion_percentage': ((progress[1] or 0) / (progress[0] or 1)) * 100,
            'risk_assessment': risk_assessment
        }
    
    def _assess_risk(self, case_id: str, conn, cursor) -> Dict:
        """Assess patient risk based on their data"""
        cursor.execute('''
            SELECT complete_data FROM patient_comparisons WHERE case_id = ?
        ''', (case_id,))
        
        result = cursor.fetchone()
        if not result:
            return {"level": "LOW_RISK", "reason": "Insufficient data"}
        
        complete_data = json.loads(result[0])
        reaction = complete_data.get('Describe Reaction(s)', '').lower()
        outcome = complete_data.get('Outcome', '').lower()
        serious = complete_data.get('Serious (Y/N)', '').lower()
        suspect_drug = complete_data.get('Suspect Drug', '').lower()
        age = complete_data.get('Age (years)', '')
        
        # Convert age to number for comparison
        try:
            age_num = float(age) if age else 0
        except:
            age_num = 0
        
        risk_level = "LOW_RISK"
        risk_reasons = []
        risk_score = 0
        
        # High risk indicators in reactions
        high_risk_reactions = [
            'fatal', 'death', 'anaphylaxis', 'severe', 'life threatening',
            'hospitalization', 'disability', 'congenital anomaly', 'cardiac',
            'respiratory failure', 'liver failure', 'kidney failure', 'shock'
        ]
        
        # High risk drugs
        high_risk_drugs = [
            'warfarin', 'insulin', 'digoxin', 'lithium', 'chemotherapy',
            'immunosuppressant', 'steroid', 'anticoagulant'
        ]
        
        # Check for high risk indicators
        for indicator in high_risk_reactions:
            if indicator in reaction:
                risk_score += 3
                risk_reasons.append(f"High-risk reaction: '{indicator}'")
        
        # Check drug risk
        for drug in high_risk_drugs:
            if drug in suspect_drug:
                risk_score += 2
                risk_reasons.append(f"High-risk drug: '{drug}'")
        
        # Check outcome
        if 'fatal' in outcome or 'death' in outcome:
            risk_score += 4
            risk_reasons.append("Fatal outcome")
        elif 'hospitaliz' in outcome:
            risk_score += 2
            risk_reasons.append("Hospitalization required")
        
        # Check seriousness
        if serious == 'y':
            risk_score += 2
            risk_reasons.append("Marked as serious")
        
        # Age-based risk
        if age_num > 65:
            risk_score += 1
            risk_reasons.append("Elderly patient (>65)")
        elif age_num < 18:
            risk_score += 1
            risk_reasons.append("Pediatric patient (<18)")
        
        # Determine final risk level
        if risk_score >= 5:
            risk_level = "HIGH_RISK"
        elif risk_score >= 3:
            risk_level = "MEDIUM_RISK"
        else:
            risk_level = "LOW_RISK"
        
        if not risk_reasons:
            risk_reasons.append("No significant risk factors identified")
        
        return {
            "level": risk_level,
            "reasons": risk_reasons,
            "score": risk_score
        }
        
        # Store risk assessment
        cursor.execute('''
            INSERT OR REPLACE INTO patient_summaries 
            (case_id, risk_assessment, assessment_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (case_id, risk_level))
        
        return {
            "level": risk_level,
            "reasons": risk_reasons
        }
    
    def get_patient_summary(self, phn: str) -> Optional[Dict]:
        """Get complete patient summary including risk assessment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                pc.case_id, pc.patient_initials, pc.contact_no,
                COUNT(pr.id) as total_questions,
                SUM(CASE WHEN pr.is_correct = 1 THEN 1 ELSE 0 END) as answered_submitted,
                SUM(CASE WHEN pr.is_correct = 0 OR pr.is_correct IS NULL THEN 1 ELSE 0 END) as pending,
                ps.risk_assessment, ps.assessment_date
            FROM patient_comparisons pc
            LEFT JOIN patient_responses pr ON pc.case_id = pr.case_id
            LEFT JOIN patient_summaries ps ON pc.case_id = ps.case_id
            WHERE pc.contact_no = ?
            GROUP BY pc.case_id, pc.patient_initials, pc.contact_no, ps.risk_assessment, ps.assessment_date
        ''', (phn,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'case_id': result[0],
                'patient_initials': result[1],
                'contact_no': result[2],
                'total_questions': result[3] or 0,
                'answered_submitted': result[4] or 0,
                'pending': result[5] or 0,
                'completion_percentage': ((result[4] or 0) / (result[3] or 1)) * 100,
                'risk_assessment': result[6] or "NOT_ASSESSED",
                'assessment_date': result[7]
            }
        return None

# Initialize patient interface
patient_interface = PatientInterface()

@router.post("/login")
async def patient_login(login_data: PatientLogin):
    """Login patient with PHN number"""
    patient = patient_interface.get_patient_by_phn(login_data.phn)
    
    if not patient:
        raise HTTPException(
            status_code=404, 
            detail="Patient not found. Please check your PHN number."
        )
    
    return {
        "success": True,
        "patient": patient
    }

@router.get("/questions/{phn}")
async def get_patient_questions(phn: str):
    """Get pending questions for a patient"""
    questions = patient_interface.get_questions_by_phn(phn)
    
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No pending questions found for this patient"
        )
    
    return {
        "success": True,
        "questions": questions,
        "total": len(questions)
    }

@router.post("/submit-answer")
async def submit_patient_answer(answer_data: PatientAnswer):
    """Submit patient answer"""
    try:
        result = patient_interface.submit_answer(answer_data.response_id, answer_data.answer)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{phn}")
async def get_patient_summary(phn: str):
    """Get patient summary including risk assessment"""
    summary = patient_interface.get_patient_summary(phn)
    
    if not summary:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    
    return {
        "success": True,
        "summary": summary
    }

@router.put("/update-patient")
async def update_patient(patient_data: dict):
    """Update patient data"""
    conn = sqlite3.connect("./pv.db")
    cursor = conn.cursor()
    
    try:
        # Update patient comparisons table
        cursor.execute('''
            UPDATE patient_comparisons 
            SET patient_initials = ?
            WHERE contact_no = ?
        ''', (patient_data.get('patient_initials'), patient_data.get('contact_no')))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Patient data updated successfully"
        }
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update patient data: {str(e)}")

@router.get("/all-patients")
async def get_all_patients():
    """Get all patients with their progress"""
    conn = sqlite3.connect("./pv.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            pc.contact_no, pc.patient_initials, pc.case_id,
            COUNT(pr.id) as total_questions,
            SUM(CASE WHEN pr.is_correct = 1 THEN 1 ELSE 0 END) as answered_submitted,
            SUM(CASE WHEN pr.is_correct = 0 OR pr.is_correct IS NULL THEN 1 ELSE 0 END) as pending,
            ps.risk_assessment
        FROM patient_comparisons pc
        LEFT JOIN patient_responses pr ON pc.case_id = pr.case_id
        LEFT JOIN patient_summaries ps ON pc.case_id = ps.case_id
        GROUP BY pc.case_id, pc.patient_initials, pc.contact_no, ps.risk_assessment
        ORDER BY pc.patient_initials
    ''')
    
    patients = []
    for row in cursor.fetchall():
        completion_pct = ((row[4] or 0) / (row[3] or 1)) * 100
        patients.append({
            'contact_no': row[0],
            'patient_initials': row[1],
            'case_id': row[2],
            'total_questions': row[3] or 0,
            'answered_submitted': row[4] or 0,
            'pending': row[5] or 0,
            'completion_percentage': completion_pct,
            'risk_assessment': row[6] or "NOT_ASSESSED"
        })
    
    conn.close()
    
    return {
        "success": True,
        "patients": patients,
        "total": len(patients)
    }
