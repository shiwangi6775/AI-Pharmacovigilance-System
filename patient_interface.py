import sqlite3
from typing import List, Dict
import json
from datetime import datetime

class PatientInterface:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_pending_questions(self) -> List[Dict]:
        """Get all pending questions for patients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.case_id, pc.patient_initials, pc.contact_no, 
                   pr.field_name, pr.question, pr.expected_answer, pr.id
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            WHERE pr.is_correct = 0 OR pr.is_correct IS NULL
            ORDER BY pc.case_id, pr.field_name
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'response_id': row[6],
                'case_id': row[0],
                'patient_initials': row[1],
                'contact_no': row[2],
                'field_name': row[3],
                'question': row[4],
                'expected_answer': row[5]
            })
        
        conn.close()
        return results
    
    def get_questions_by_patient(self, contact_no: str) -> List[Dict]:
        """Get all pending questions for a specific patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.case_id, pc.patient_initials, pr.field_name, 
                   pr.question, pr.expected_answer, pr.id
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            WHERE pc.contact_no = ? AND (pr.is_correct = 0 OR pr.is_correct IS NULL)
            ORDER BY pr.field_name
        ''', (contact_no,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'response_id': row[5],
                'case_id': row[0],
                'patient_initials': row[1],
                'field_name': row[2],
                'question': row[3],
                'expected_answer': row[4]
            })
        
        conn.close()
        return results
    
    def _update_patient_summary(self, case_id: str):
        """Update patient summary and perform risk assessment if all questions are answered"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current response status
        cursor.execute('''
            SELECT 
                COUNT(*) as total_questions,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as answered_correctly,
                SUM(CASE WHEN is_correct = 0 OR is_correct IS NULL THEN 1 ELSE 0 END) as pending,
                pc.patient_initials,
                pc.contact_no
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            WHERE pr.case_id = ?
            GROUP BY pr.case_id, pc.patient_initials, pc.contact_no
        ''', (case_id,))
        
        result = cursor.fetchone()
        if result:
            total_questions = result[0]
            answered_correctly = result[1]
            pending = result[2]
            patient_initials = result[3]
            contact_no = result[4]
            completion_pct = (answered_correctly / total_questions * 100) if total_questions > 0 else 0
            
            # Check if patient summary exists
            cursor.execute('''
                SELECT id FROM patient_summaries WHERE case_id = ?
            ''', (case_id,))
            
            summary_result = cursor.fetchone()
            
            if summary_result:
                # Update existing summary
                cursor.execute('''
                    UPDATE patient_summaries 
                    SET total_questions = ?, answered_correctly = ?, pending_questions = ?,
                        completion_percentage = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE case_id = ?
                ''', (total_questions, answered_correctly, pending, completion_pct, case_id))
            else:
                # Create new summary
                cursor.execute('''
                    INSERT INTO patient_summaries 
                    (case_id, patient_initials, contact_no, total_questions, answered_correctly, 
                     pending_questions, completion_percentage, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (case_id, patient_initials, contact_no, total_questions, answered_correctly, 
                      pending, completion_pct))
            
            # If all questions are answered, perform risk assessment
            if pending == 0:
                risk_level = self._assess_patient_risk(case_id)
                cursor.execute('''
                    UPDATE patient_summaries 
                    SET risk_assessment = ?, assessment_date = CURRENT_TIMESTAMP
                    WHERE case_id = ?
                ''', (risk_level, case_id))
        
        conn.commit()
        conn.close()
    
    def _assess_patient_risk(self, case_id: str) -> str:
        """Assess patient risk based on their responses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get patient's complete data including reactions
        cursor.execute('''
            SELECT complete_data FROM patient_comparisons WHERE case_id = ?
        ''', (case_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return "LOW_RISK"
        
        complete_data = json.loads(result[0])
        reaction = complete_data.get('Describe Reaction(s)', '').lower()
        outcome = complete_data.get('Outcome', '').lower()
        serious = complete_data.get('Serious (Y/N)', '').lower()
        
        # Risk assessment logic
        high_risk_indicators = [
            'fatal', 'death', 'anaphylaxis', 'severe', 'life threatening',
            'hospitalization', 'disability', 'congenital anomaly'
        ]
        
        # Check for high risk indicators in reaction description
        for indicator in high_risk_indicators:
            if indicator in reaction:
                conn.close()
                return "HIGH_RISK"
        
        # Check outcome and seriousness
        if 'fatal' in outcome or serious == 'y':
            conn.close()
            return "HIGH_RISK"
        
        conn.close()
        return "LOW_RISK"
    
    def get_patient_risk_assessment(self, contact_no: str) -> Dict:
        """Get risk assessment for a specific patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ps.risk_assessment, ps.assessment_date, ps.completion_percentage,
                   pc.patient_initials, pc.case_id
            FROM patient_summaries ps
            JOIN patient_comparisons pc ON ps.case_id = pc.case_id
            WHERE pc.contact_no = ?
        ''', (contact_no,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'risk_assessment': result[0],
                'assessment_date': result[1],
                'completion_percentage': result[2],
                'patient_initials': result[3],
                'case_id': result[4]
            }
        return None
    
    def submit_response(self, response_id: int, patient_answer: str) -> bool:
        """Submit patient response and check if it's correct"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the expected answer
        cursor.execute('''
            SELECT expected_answer, case_id FROM patient_responses WHERE id = ?
        ''', (response_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
            
        expected_answer = str(result[0])
        case_id = result[1]
        is_correct = str(patient_answer).strip().lower() == expected_answer.strip().lower()
        
        # Update the response
        cursor.execute('''
            UPDATE patient_responses 
            SET patient_answer = ?, is_correct = ?, responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (patient_answer, is_correct, response_id))
        
        conn.commit()
        conn.close()
        
        # Update patient summary and check if risk assessment is needed
        self._update_patient_summary(case_id)
        
        return is_correct
    
    def get_patient_summary(self, contact_no: str) -> Dict:
        """Get summary of patient's response status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_questions,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as answered_correctly,
                SUM(CASE WHEN is_correct = 0 OR is_correct IS NULL THEN 1 ELSE 0 END) as pending,
                pc.patient_initials,
                pc.case_id
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            WHERE pc.contact_no = ?
            GROUP BY pc.case_id, pc.patient_initials
        ''', (contact_no,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'total_questions': result[0],
                'answered_correctly': result[1],
                'pending': result[2],
                'patient_initials': result[3],
                'case_id': result[4],
                'completion_percentage': (result[1] / result[0] * 100) if result[0] > 0 else 0
            }
        return None
    
    def get_all_patients_summary(self) -> List[Dict]:
        """Get summary of all patients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                pc.contact_no,
                pc.patient_initials,
                pc.case_id,
                COUNT(*) as total_questions,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as answered_correctly,
                SUM(CASE WHEN is_correct = 0 OR is_correct IS NULL THEN 1 ELSE 0 END) as pending
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            GROUP BY pc.case_id, pc.patient_initials, pc.contact_no
            ORDER BY pc.patient_initials
        ''')
        
        results = []
        for row in cursor.fetchall():
            completion_pct = (row[4] / row[3] * 100) if row[3] > 0 else 0
            results.append({
                'contact_no': row[0],
                'patient_initials': row[1],
                'case_id': row[2],
                'total_questions': row[3],
                'answered_correctly': row[4],
                'pending': row[5],
                'completion_percentage': completion_pct
            })
        
        conn.close()
        return results

def interactive_patient_session():
    """Interactive session for collecting patient responses"""
    interface = PatientInterface("/home/shaluchan/ai-docker/pharma-covigilance/AI-Pharmacovigilance-System/pv.db")
    
    print("=== Patient Data Collection System ===")
    print("1. View all patients")
    print("2. Start session for specific patient (Enter PHN)")
    print("3. View patient summary and risk assessment")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            patients = interface.get_all_patients_summary()
            print("\n=== All Patients ===")
            for patient in patients:
                print(f"Patient: {patient['patient_initials']} (PHN: {patient['contact_no']})")
                print(f"  Progress: {patient['answered_correctly']}/{patient['total_questions']} ({patient['completion_percentage']:.1f}%)")
                print(f"  Pending: {patient['pending']} questions")
                print()
        
        elif choice == '2':
            contact_no = input("Enter patient PHN (Contact No): ").strip()
            questions = interface.get_questions_by_patient(contact_no)
            
            if not questions:
                print("No pending questions found for this patient or patient not found.")
                continue
                
            patient_name = questions[0]['patient_initials']
            print(f"\n=== Starting session for {patient_name} (PHN: {contact_no}) ===")
            print(f"Total questions: {len(questions)}")
            
            for i, q in enumerate(questions, 1):
                print(f"\nQuestion {i}/{len(questions)}:")
                print(q['question'])
                
                answer = input("Your answer: ").strip()
                is_correct = interface.submit_response(q['response_id'], answer)
                
                if is_correct:
                    print("✓ Correct answer!")
                else:
                    print(f"✗ Incorrect. Expected: {q['expected_answer']}")
            
            # Check for risk assessment after completing all questions
            risk_assessment = interface.get_patient_risk_assessment(contact_no)
            if risk_assessment and risk_assessment['completion_percentage'] == 100.0:
                print(f"\n🏥 SESSION COMPLETED!")
                print(f"Risk Assessment: {risk_assessment['risk_assessment']}")
                if risk_assessment['risk_assessment'] == 'HIGH_RISK':
                    print("⚠️  HIGH RISK - Please seek immediate medical attention!")
                else:
                    print("✅ LOW RISK - Continue monitoring")
            else:
                print(f"\nSession completed for {patient_name}!")
            
        elif choice == '3':
            contact_no = input("Enter patient PHN (Contact No): ").strip()
            summary = interface.get_patient_summary(contact_no)
            risk_assessment = interface.get_patient_risk_assessment(contact_no)
            
            if summary:
                print(f"\n=== Summary for {summary['patient_initials']} (PHN: {contact_no}) ===")
                print(f"Total Questions: {summary['total_questions']}")
                print(f"Answered Correctly: {summary['answered_correctly']}")
                print(f"Pending: {summary['pending']}")
                print(f"Completion: {summary['completion_percentage']:.1f}%")
                
                if risk_assessment:
                    print(f"Risk Assessment: {risk_assessment['risk_assessment']}")
                    if risk_assessment['assessment_date']:
                        print(f"Assessed on: {risk_assessment['assessment_date']}")
                else:
                    print("Risk Assessment: Not completed yet")
            else:
                print("Patient not found.")
                
        elif choice == '4':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    interactive_patient_session()
