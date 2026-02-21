from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
from database import SessionLocal
from models.patient_comparison_model import PatientComparison, PatientResponse

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PatientResponseInput(BaseModel):
    response_id: int
    patient_answer: str

class PHNLookupInput(BaseModel):
    phn_no: str

class ComparisonResult(BaseModel):
    case_id: str
    patient_initials: str
    contact_no: str
    missing_fields: dict
    questions: List[dict]
    completion_percentage: float

class PatientQuestion(BaseModel):
    response_id: int
    case_id: str
    patient_initials: str
    contact_no: str
    field_name: str
    question: str
    expected_answer: str

@router.post("/run-comparison")
async def run_comparison():
    """Run the CSV comparison and populate database"""
    try:
        from patient_data_comparator import PatientDataComparator
        
        comparator = PatientDataComparator(
            main_csv_path="/home/shaluchan/ai-docker/pharma-covigilance/syoms1.csv",
            missing_csv_path="/home/shaluchan/ai-docker/pharma-covigilance/missed_converted.csv",
            db_path="/home/shaluchan/ai-docker/pharma-covigilance/AI-Pharmacovigilance-System/pv.db"
        )
        
        results = comparator.run_comparison()
        
        return {
            "status": "success",
            "message": f"Comparison completed for {len(results)} patients",
            "total_patients": len(results),
            "total_questions": sum(len(r['questions']) for r in results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lookup-phn")
async def lookup_phn(phn_data: PHNLookupInput, db: Session = Depends(get_db)):
    """Lookup patient by PHN number and return their questions"""
    patient = db.query(PatientComparison).filter(PatientComparison.contact_no == phn_data.phn_no).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found with this PHN number")
    
    # Get unanswered questions
    responses = db.query(PatientResponse).filter(
        PatientResponse.case_id == patient.case_id
    ).all()
    
    questions = []
    all_questions = json.loads(patient.questions) if patient.questions else []
    
    for q in all_questions:
        response = next((r for r in responses if r.field_name == q['field']), None)
        
        if response and not response.is_correct:
            questions.append({
                "response_id": response.id,
                "case_id": patient.case_id,
                "patient_initials": patient.patient_initials,
                "contact_no": patient.contact_no,
                "field_name": q['field'],
                "question": q['question'],
                "expected_answer": q['expected_answer'],
                "is_answered": bool(response.patient_answer and response.patient_answer.strip()),
                "is_correct": response.is_correct
            })
        elif not response:
            # Create response record if it doesn't exist
            new_response = PatientResponse(
                case_id=patient.case_id,
                field_name=q['field'],
                question=q['question'],
                expected_answer=str(q['expected_answer']),
                is_correct=False
            )
            db.add(new_response)
            db.commit()
            db.refresh(new_response)
            
            questions.append({
                "response_id": new_response.id,
                "case_id": patient.case_id,
                "patient_initials": patient.patient_initials,
                "contact_no": patient.contact_no,
                "field_name": q['field'],
                "question": q['question'],
                "expected_answer": q['expected_answer'],
                "is_answered": False,
                "is_correct": False
            })
    
    # Calculate progress
    total_questions = len(all_questions)
    answered_correctly = db.query(PatientResponse).filter(
        PatientResponse.case_id == patient.case_id,
        PatientResponse.is_correct == True
    ).count()
    
    completion = (answered_correctly / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "patient_info": {
            "case_id": patient.case_id,
            "patient_initials": patient.patient_initials,
            "contact_no": patient.contact_no,
            "completion_percentage": round(completion, 1),
            "total_questions": total_questions,
            "answered_correctly": answered_correctly
        },
        "questions": questions
    }

@router.post("/submit-response")
async def submit_response(response_data: PatientResponseInput, db: Session = Depends(get_db)):
    """Submit patient response and save without validation"""
    response = db.query(PatientResponse).filter(PatientResponse.id == response_data.response_id).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Save response without validation
    response.patient_answer = response_data.patient_answer
    response.is_correct = None  # No immediate validation
    
    db.commit()
    
    # Update patient completion percentage
    case_id = response.case_id
    total_responses = db.query(PatientResponse).filter(PatientResponse.case_id == case_id).count()
    answered_responses = db.query(PatientResponse).filter(
        PatientResponse.case_id == case_id,
        PatientResponse.patient_answer.isnot(None),
        PatientResponse.patient_answer != ""
    ).count()
    
    completion = (answered_responses / total_responses * 100) if total_responses > 0 else 0
    
    patient = db.query(PatientComparison).filter(PatientComparison.case_id == case_id).first()
    if patient:
        patient.completion_percentage = completion
        if completion == 100.0:
            # Classify risk when all questions are answered
            risk_level = classify_patient_risk(case_id, db)
            patient.status = risk_level
        db.commit()
    
    return {
        "status": "success",
        "completion_percentage": round(completion, 1),
        "message": "Response saved successfully!",
        "is_completed": completion == 100.0
    }

def classify_patient_risk(case_id: str, db: Session) -> str:
    """Classify patient as HIGH RISK or LOW RISK based on syoms data comparison"""
    try:
        # Get patient responses
        responses = db.query(PatientResponse).filter(
            PatientResponse.case_id == case_id,
            PatientResponse.patient_answer.isnot(None),
            PatientResponse.patient_answer != ""
        ).all()
        
        # Get expected answers from patient comparison
        patient = db.query(PatientComparison).filter(PatientComparison.case_id == case_id).first()
        if not patient:
            return "UNKNOWN"
        
        complete_data = json.loads(patient.complete_data) if patient.complete_data else {}
        
        # Check for high-risk indicators
        high_risk_indicators = 0
        total_indicators = 0
        
        for response in responses:
            expected_answer = str(response.expected_answer).strip().lower()
            patient_answer = str(response.patient_answer).strip().lower()
            
            # Check specific high-risk fields
            if response.field_name == 'Serious (Y/N)':
                total_indicators += 1
                if expected_answer == 'y' and patient_answer == 'y':
                    high_risk_indicators += 1
                elif expected_answer == 'y' and patient_answer != 'y':
                    # Patient downplays seriousness - could be high risk
                    high_risk_indicators += 1
                    
            elif response.field_name == 'Outcome':
                total_indicators += 1
                if 'fatal' in expected_answer.lower() or 'severe' in expected_answer.lower():
                    high_risk_indicators += 1
                    
            elif response.field_name == 'Describe Reaction(s)':
                total_indicators += 1
                severe_reactions = ['anaphylaxis', 'breathlessness', 'severe allergic', 'hepatotoxicity']
                if any(reaction in expected_answer.lower() for reaction in severe_reactions):
                    high_risk_indicators += 1
        
        # Calculate risk percentage
        if total_indicators == 0:
            return "LOW RISK"
            
        risk_percentage = (high_risk_indicators / total_indicators) * 100
        
        return "HIGH RISK" if risk_percentage >= 30 else "LOW RISK"
        
    except Exception as e:
        print(f"Error classifying risk: {e}")
        return "UNKNOWN"

@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """Get overall summary statistics"""
    total_patients = db.query(PatientComparison).count()
    
    if total_patients == 0:
        return {
            "total_patients": 0,
            "completed_patients": 0,
            "total_questions": 0,
            "total_answered": 0,
            "overall_completion_percentage": 0,
            "pending_patients": 0,
            "high_risk_patients": 0,
            "low_risk_patients": 0
        }
    
    # Calculate overall stats
    patients = db.query(PatientComparison).all()
    total_questions = 0
    total_answered = 0
    completed_patients = 0
    high_risk_count = 0
    low_risk_count = 0
    
    for patient in patients:
        questions = json.loads(patient.questions) if patient.questions else []
        total_questions += len(questions)
        
        answered_count = db.query(PatientResponse).filter(
            PatientResponse.case_id == patient.case_id,
            PatientResponse.patient_answer.isnot(None),
            PatientResponse.patient_answer != ""
        ).count()
        
        total_answered += answered_count
        
        if patient.completion_percentage == 100.0:
            completed_patients += 1
            if patient.status == "HIGH RISK":
                high_risk_count += 1
            elif patient.status == "LOW RISK":
                low_risk_count += 1
    
    overall_completion = (total_answered / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "total_patients": total_patients,
        "completed_patients": completed_patients,
        "total_questions": total_questions,
        "total_answered": total_answered,
        "overall_completion_percentage": round(overall_completion, 1),
        "pending_patients": total_patients - completed_patients,
        "high_risk_patients": high_risk_count,
        "low_risk_patients": low_risk_count
    }
