from sqlalchemy import Column, Integer, String
from database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    drug_name = Column(String)
    reaction = Column(String)
    risk_level = Column(String)
    follow_up_answers = Column(String)   
    phone = Column(String)
    response_count = Column(Integer, default=0)
    language: str = "en"

