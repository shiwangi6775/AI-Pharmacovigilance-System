#!/usr/bin/env python3
"""Create database tables for patient data system"""

import sys
import os

# Add the parent directory to the path to import the database module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import Base, engine
from models.patient_comparison_model import PatientComparison, PatientResponse, PatientSummary

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
