from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import Base, engine, SessionLocal
from models.case_model import Case
# from ai_engine.question_generator import generate_followup_questions
# from notification_service import send_sms, make_call
# from ai_engine.nlp_transformer import extract_medical_features
# from ai_engine.risk_predictor import predict_risk_probability
# from ai_engine.llm_question_generator import generate_llm_followup_questions
from database import Base, engine
# from models.user_model import User
from routes.excel_routes import router as excel_router
from routes.patient_routes import router as patient_router
from routes.patient_interface_routes import router as patient_interface_router





Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(excel_router)
app.include_router(patient_router, prefix="/api/patients", tags=["patients"])
app.include_router(patient_interface_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000", "file://", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class FollowUpInput(BaseModel):
    case_id: int
    answers: str

class CaseInput(BaseModel):
    drug_name: str
    reaction: str
    phone: str
    language: str = "en"

def classify_risk(reaction: str):
    reaction = reaction.lower()
    if "rash" in reaction or "breathing" in reaction:
        return "HIGH RISK"
    return "LOW RISK"

def generate_questions():
    return [
        "Did the reaction worsen?",
        "Did you consult a doctor?",
        "Did symptoms improve after stopping the drug?"
    ]

@app.post("/submit-case")
def submit_case(case: CaseInput):
    db = SessionLocal()
    # nlp_features = extract_medical_features(case.reaction)
    # print("NLP FEATURES:", nlp_features)

    # prob = predict_risk_probability(case.reaction)
    risk = "LOW RISK"  # Simplified for now
    # print("ML RISK PROBABILITY:", prob)
    # questions = generate_llm_followup_questions(
    # case.drug_name,
    # case.reaction,
    # prob,
    # nlp_features,
    # case.language 
    # )

    questions = [
        "Did the reaction worsen?",
        "Did you consult a doctor?",
        "Did symptoms improve after stopping the drug?"
    ]

    new_case = Case(
        drug_name=case.drug_name,
        reaction=case.reaction,
        risk_level=risk,
        follow_up_answers="",
        phone=case.phone
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    
    # if risk == "HIGH RISK":
    #     send_sms(
    #         case.phone,
    #         f"URGENT: Severe reaction detected for {case.drug_name}. Please seek medical attention immediately."
    #     )
    #     make_call(case.phone)

    db.close()

    return {
        "case_id": new_case.id,
        "risk_level": risk,
        "follow_up_questions": questions
    }


@app.post("/submit-followup")
def submit_followup(data: FollowUpInput):
    db = SessionLocal()

    case = db.query(Case).filter(Case.id == data.case_id).first()
    case.follow_up_answers = data.answers
    case.response_count += 1

    db.commit()
    db.close()

    db.refresh(new_case)

    return {
    "case_id": new_case.id,
    "risk_level": risk,
    "follow_up_questions": generate_questions()
}

@app.get("/cases")
def get_cases():
    db: Session = SessionLocal()
    cases = db.query(Case).all()
    db.close()
    return cases
@app.get("/leaderboard")
def leaderboard():
    db = SessionLocal()
    cases = (
        db.query(Case)
        .order_by(Case.response_count.desc())
        .limit(10)
        .all()
    )

    data = [
        {
            "id": c.id,
            "responses": c.response_count
        }
        for c in cases
    ]

    db.close()
    return data
