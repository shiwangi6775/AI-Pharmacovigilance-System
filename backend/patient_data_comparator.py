import pandas as pd
import sqlite3
from typing import Dict, List, Tuple
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path to import the database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from models.patient_comparison_model import PatientComparison, PatientResponse
from ai_engine.azure_question_generator import generate_azure_missing_field_questions

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

class PatientDataComparator:
    def __init__(self, main_csv_path: str, missing_csv_path: str, db_path: str):
        self.main_csv_path = main_csv_path
        self.missing_csv_path = missing_csv_path
        self.db_path = db_path
        self.main_df = None
        self.missing_df = None
        
    def load_data(self):
        """Load both CSV files"""
        self.main_df = pd.read_csv(self.main_csv_path)
        self.missing_df = pd.read_csv(self.missing_csv_path)
        print(f"Loaded {len(self.main_df)} records from main file")
        print(f"Loaded {len(self.missing_df)} records from missing file")
        
    def compare_data(self) -> List[Dict]:
        """Compare main data with missing data and identify missing fields"""
        comparison_results = []
        
        for _, missing_row in self.missing_df.iterrows():
            case_id = missing_row['Case ID']
            contact_no = missing_row['Contact no']
            
            # Find matching patient in main data
            main_match = self.main_df[
                (self.main_df['Case ID'] == case_id) | 
                (self.main_df['Contact no'] == contact_no)
            ]
            
            if main_match.empty:
                print(f"Warning: No match found for Case ID: {case_id}, Contact: {contact_no}")
                continue
                
            main_row = main_match.iloc[0]
            
            # Identify missing fields
            missing_fields = {}
            questions = []
            
            for column in self.missing_df.columns:
                missing_value = missing_row[column]
                main_value = main_row[column]
                
                # Check if data is missing (empty, NaN, or placeholder)
                if pd.isna(missing_value) or missing_value == '' or str(missing_value).strip() == '':
                    missing_fields[column] = {
                        'missing_value': missing_value,
                        'correct_value': main_value,
                        'field_name': column
                    }

            missing_field_names = list(missing_fields.keys())

            try:
                azure_questions = generate_azure_missing_field_questions(
                    patient_initials=main_row['Patient Initials'],
                    contact_no=str(contact_no),
                    missing_fields=missing_field_names,
                    language="en",
                )
            except Exception:
                azure_questions = {}

            for column in missing_field_names:
                main_value = main_row[column]
                question = azure_questions.get(column)
                if not question:
                    question = f"Please provide the {column} for patient {main_row['Patient Initials']} (PHN: {contact_no})"

                questions.append({
                    'field': column,
                    'question': question,
                    'expected_answer': main_value
                })
            
            comparison_results.append({
                'case_id': case_id,
                'patient_initials': missing_row['Patient Initials'],
                'contact_no': contact_no,
                'missing_fields': missing_fields,
                'questions': questions,
                'complete_data': main_row.to_dict(),
                'incomplete_data': missing_row.to_dict()
            })
            
        return comparison_results
    
    def _generate_question(self, field_name: str, patient_initials: str, contact_no: str) -> str:
        """Generate specific questions for missing data fields"""
        patient_identifier = f"patient {patient_initials} (PHN: {contact_no})"
        
        questions = {
            'Age (years)': f"What is the age of {patient_identifier}?",
            'Sex': f"What is the gender/sex of {patient_identifier}?",
            'Reaction Onset Date': f"When did the adverse reaction start for {patient_identifier}?",
            'Outcome': f"What was the outcome of the adverse reaction for {patient_identifier}?",
            'Serious (Y/N)': f"Was the adverse reaction serious for {patient_identifier}? (Y/N)",
            'Daily Dose': f"What was the daily dose of the suspect drug for {patient_identifier}?",
            'Indication': f"What was the indication for the suspect drug for {patient_identifier}?",
            'Therapy Start Date': f"When did the therapy start for {patient_identifier}?",
            'Therapy End Date': f"When did the therapy end for {patient_identifier}?",
            'Therapy Duration': f"What was the duration of therapy for {patient_identifier}?",
            'Abated After Stopping': f"Did symptoms abate after stopping the drug for {patient_identifier}?",
            'Rechallenge Result': f"What was the rechallenge result for {patient_identifier}?",
            'Concomitant Drug 1': f"What was the first concomitant drug for {patient_identifier}?",
            'Concomitant Drug 2': f"What was the second concomitant drug for {patient_identifier}?",
            'Medical History': f"What is the medical history of {patient_identifier}?"
        }
        
        return questions.get(field_name, f"Please provide the {field_name} for {patient_identifier}")
    
    def store_comparison_results(self, comparison_results: List[Dict]):
        """Store comparison results in database using SQLAlchemy"""
        db = SessionLocal()
        
        try:
            for result in comparison_results:
                # Check if patient comparison already exists
                existing = db.query(PatientComparison).filter(
                    PatientComparison.case_id == result['case_id']
                ).first()
                
                if existing:
                    # Update existing record
                    existing.missing_fields = json.dumps(result['missing_fields'])
                    existing.questions = json.dumps(result['questions'])
                    existing.complete_data = json.dumps(result['complete_data'])
                    existing.incomplete_data = json.dumps(result['incomplete_data'])
                    existing.status = "pending"
                    existing.completion_percentage = 0.0
                else:
                    # Create new patient comparison record
                    patient_comparison = PatientComparison(
                        case_id=result['case_id'],
                        patient_initials=result['patient_initials'],
                        contact_no=result['contact_no'],
                        missing_fields=json.dumps(result['missing_fields']),
                        questions=json.dumps(result['questions']),
                        complete_data=json.dumps(result['complete_data']),
                        incomplete_data=json.dumps(result['incomplete_data']),
                        status="pending",
                        completion_percentage=0.0
                    )
                    db.add(patient_comparison)
                
                # Commit the patient comparison first to get the ID
                db.commit()
                
                # Create individual question records
                for question_data in result['questions']:
                    # Check if response already exists
                    existing_response = db.query(PatientResponse).filter(
                        PatientResponse.case_id == result['case_id'],
                        PatientResponse.field_name == question_data['field']
                    ).first()
                    
                    if not existing_response:
                        patient_response = PatientResponse(
                            case_id=result['case_id'],
                            field_name=question_data['field'],
                            question=question_data['question'],
                            expected_answer=str(question_data['expected_answer']),
                            is_correct=False
                        )
                        db.add(patient_response)
                
                db.commit()
            
            print(f"Stored {len(comparison_results)} comparison results in database")
            
        except Exception as e:
            db.rollback()
            print(f"Error storing results: {e}")
            raise
        finally:
            db.close()
    
    def run_comparison(self):
        """Run the complete comparison process"""
        print("Starting patient data comparison...")
        self.load_data()
        
        comparison_results = self.compare_data()
        self.store_comparison_results(comparison_results)
        
        print(f"\nComparison complete! Found {len(comparison_results)} patients with missing data")
        
        # Show summary
        total_missing_fields = sum(len(r['missing_fields']) for r in comparison_results)
        print(f"Total missing fields across all patients: {total_missing_fields}")
        
        return comparison_results

if __name__ == "__main__":
    # Initialize the comparator
    comparator = PatientDataComparator(
        main_csv_path="syoms1.csv",
        missing_csv_path="missed_converted.csv",
        db_path="pv.db"
    )
    
    # Run the comparison
    results = comparator.run_comparison()
    
    # Display summary
    total_questions = sum(len(r['questions']) for r in results)
    print(f"\nGenerated {total_questions} questions for missing data")
