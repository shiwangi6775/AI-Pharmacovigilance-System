from database import SessionLocal
from models.case_db_model import PVCase

@router.get("/all")
def get_all_cases():
    db = SessionLocal()
    cases = db.query(PVCase).all()
    db.close()
    return cases
