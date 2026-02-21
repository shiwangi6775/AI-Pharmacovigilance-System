import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_followup_questions_local(
    drug,
    reaction,
    risk_probability,
    nlp_features
):
    prompt = f"""
You are a pharmacovigilance AI assistant.

Drug: {drug}
Reaction: {reaction}
Predicted risk probability: {risk_probability}

Medical features:
{nlp_features}

Generate 5 concise clinical follow-up questions
to assess seriousness of this adverse drug reaction.

Only list the questions.
"""

    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=60)

    text = response.json()["response"]

    questions = [
        q.strip("-• ").strip()
        for q in text.split("\n")
        if q.strip()
    ]

    return questions

