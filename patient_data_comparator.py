import pandas as pd
import sqlite3
from typing import Dict, List, Tuple
import json

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
                    
                    # Generate specific questions based on field type
                    question = self._generate_question(column, main_row['Patient Initials'], contact_no)
                    if question:
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
    
    def setup_database(self):
        """Setup database tables for storing comparison results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for patient comparison results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE,
                patient_initials TEXT,
                contact_no TEXT,
                missing_fields TEXT,
                questions TEXT,
                complete_data TEXT,
                incomplete_data TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for patient responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT,
                field_name TEXT,
                question TEXT,
                patient_answer TEXT,
                expected_answer TEXT,
                is_correct BOOLEAN,
                responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES patient_comparisons (case_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database tables created/verified")
    
    def store_comparison_results(self, comparison_results: List[Dict]):
        """Store comparison results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in comparison_results:
            cursor.execute('''
                INSERT OR REPLACE INTO patient_comparisons 
                (case_id, patient_initials, contact_no, missing_fields, questions, complete_data, incomplete_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['case_id'],
                result['patient_initials'],
                result['contact_no'],
                json.dumps(result['missing_fields']),
                json.dumps(result['questions']),
                json.dumps(result['complete_data']),
                json.dumps(result['incomplete_data'])
            ))
            
            # Store individual questions for tracking
            for question_data in result['questions']:
                cursor.execute('''
                    INSERT INTO patient_responses 
                    (case_id, field_name, question, expected_answer, is_correct)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    result['case_id'],
                    question_data['field'],
                    question_data['question'],
                    str(question_data['expected_answer']),
                    False  # Initially not answered
                ))
        
        conn.commit()
        conn.close()
        print(f"Stored {len(comparison_results)} comparison results in database")
    
    def get_pending_questions(self) -> List[Dict]:
        """Get all pending questions for patients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.case_id, pc.patient_initials, pc.contact_no, 
                   pr.field_name, pr.question, pr.expected_answer
            FROM patient_responses pr
            JOIN patient_comparisons pc ON pr.case_id = pc.case_id
            WHERE pr.is_correct = 0 OR pr.is_correct IS NULL
            ORDER BY pc.case_id, pr.field_name
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'case_id': row[0],
                'patient_initials': row[1],
                'contact_no': row[2],
                'field_name': row[3],
                'question': row[4],
                'expected_answer': row[5]
            })
        
        conn.close()
        return results
    
    def run_comparison(self):
        """Run the complete comparison process"""
        print("Starting patient data comparison...")
        self.load_data()
        self.setup_database()
        
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
    
    # Display pending questions
    pending_questions = comparator.get_pending_questions()
    print(f"\nGenerated {len(pending_questions)} questions for missing data")
    
    # Show first few questions as example
    if pending_questions:
        print("\nExample questions:")
        for i, q in enumerate(pending_questions[:5]):
            print(f"{i+1}. {q['question']}")
