def generate_followup_questions(drug, reaction):
    drug = drug.lower()
    reaction = reaction.lower()

    questions = []

    if "rash" in reaction:
        questions.extend([
            "Did the rash spread to other body parts?",
            "Was there itching or burning?",
            "Did you notice swelling of face or lips?",
            "Did symptoms improve after stopping the drug?"
        ])

    if "breathing" in reaction:
        questions.extend([
            "Did you experience chest tightness?",
            "Was emergency treatment required?",
            "Did you have swelling of tongue or throat?",
            "Did breathing improve after stopping the drug?"
        ])

    if "paracetamol" in drug:
        questions.append(
            "Did you take more than recommended dose?"
        )

    if "amoxicillin" in drug:
        questions.append(
            "Have you ever had penicillin allergy before?"
        )

    if not questions:
        questions.append(
            "Can you describe how the reaction progressed?"
        )

    return questions
