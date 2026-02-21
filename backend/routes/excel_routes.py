from fastapi import APIRouter, UploadFile, File
import pandas as pd
from database import SessionLocal
from models.case_model import Case

router = APIRouter()

@router.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):

    df = pd.read_excel(file.file)

    db = SessionLocal()

    created = 0

    for _, row in df.iterrows():

        new_case = Case(
            drug_name=row.get("Suspect Drug"),
            reaction=row.get("Describe Reaction(s)"),
            phone="",
            risk_level="PENDING",
            follow_up_answers=""
        )

        db.add(new_case)
        created += 1

    db.commit()
    db.close()

    return {"message": f"{created} cases imported successfully"}
