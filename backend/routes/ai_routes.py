from automation.twilio_service import send_sms, make_call

@router.post("/analyze")
def analyze_case(case: CaseInput, db: Session = Depends(get_db)):

    questions = generate_questions(case.drug_name, case.reaction, case.language)
    risk = classify_risk(case.reaction, case.hospitalized)

    if risk == "HIGH RISK":
        send_sms(
            case.phone,
            "URGENT: You reported a serious reaction. Please seek medical attention immediately."
        )
        make_call(case.phone)

    else:
        send_sms(
            case.phone,
            "Thank you for reporting your reaction. We will follow up shortly."
        )

    # store case
    db_case = PVCase(
        patient_id=case.patient_id,
        drug_name=case.drug_name,
        reaction=case.reaction,
        hospitalized=case.hospitalized,
        risk_level=risk
    )

    db.add(db_case)
    db.commit()

    return {
        "follow_up_questions": questions,
        "risk_level": risk,
        "automation_triggered": True
    }
