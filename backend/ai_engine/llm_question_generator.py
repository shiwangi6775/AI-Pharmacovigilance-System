from deep_translator import GoogleTranslator
def generate_llm_followup_questions(
    drug,
    reaction,
    risk_probability,
    nlp_features, language="en"
):
    questions = []

    # High-risk reasoning
    if risk_probability > 0.6:
        questions.append(
            "When did the reaction begin after taking the medication?"
        )
        questions.append(
            "Did the patient require urgent or emergency medical treatment?"
        )

    # Body system reasoning
    for system in nlp_features.get("body_systems", []):
        if system == "respiratory":
            questions.append(
                "Did the patient experience shortness of breath, wheezing, or chest tightness?"
            )
            questions.append(
                "Was there any swelling of the lips, tongue, or throat?"
            )

        if system == "skin":
            questions.append(
                "Did the rash spread to other parts of the body?"
            )
            questions.append(
                "Was itching or burning sensation present?"
            )

        if system == "gastrointestinal":
            questions.append(
                "Did the patient experience persistent vomiting or abdominal pain?"
            )

    # Drug-specific reasoning
    if "amoxicillin" in drug.lower() or "penicillin" in drug.lower():
        questions.append(
            "Has the patient ever had a known allergy to penicillin or related antibiotics?"
        )

    if "paracetamol" in drug.lower():
        questions.append(
            "Was the recommended dosage exceeded at any time?"
        )

    # General clinical questions
    questions.append(
        "Did symptoms improve after stopping the medication?"
    )

    # Remove duplicates and limit
    questions = list(dict.fromkeys(questions))[:6]
   
    if language == "hi":
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source="en", target="hi")
            questions = [translator.translate(q) for q in questions]
        except Exception as e:
            print("Translation error:", e)

    return questions


    


