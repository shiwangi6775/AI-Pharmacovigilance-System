from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.sql import func
from database import Base

class PatientComparison(Base):
    __tablename__ = "patient_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    patient_initials = Column(String)
    contact_no = Column(String, index=True)
    missing_fields = Column(Text)  # JSON
    questions = Column(Text)  # JSON
    complete_data = Column(Text)  # JSON
    incomplete_data = Column(Text)  # JSON
    status = Column(String, default="pending")
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PatientResponse(Base):
    __tablename__ = "patient_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    field_name = Column(String)
    question = Column(Text)
    patient_answer = Column(Text)
    expected_answer = Column(Text)
    is_correct = Column(Boolean, default=False)
    responded_at = Column(DateTime(timezone=True), server_default=func.now())
    
class PatientSummary(Base):
    __tablename__ = "patient_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    patient_initials = Column(String)
    contact_no = Column(String, index=True)
    total_questions = Column(Integer, default=0)
    answered_correctly = Column(Integer, default=0)
    pending_questions = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    risk_assessment = Column(String, default="NOT_ASSESSED")  # HIGH_RISK, LOW_RISK, NOT_ASSESSED
    assessment_date = Column(DateTime(timezone=True), nullable=True)
