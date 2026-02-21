from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class PVCase(Base):
    __tablename__ = "pv_cases"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String)
    drug_name = Column(String)
    reaction = Column(String)
    risk_level = Column(String)
    hospitalized = Column(Boolean)
    language: str = "en"
