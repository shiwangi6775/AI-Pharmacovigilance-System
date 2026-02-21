from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

MEDICAL_CONCEPTS = {
    "respiratory": [
        "breathing difficulty",
        "shortness of breath",
        "chest tightness",
        "wheezing"
    ],
    "skin": [
        "rash",
        "itching",
        "hives",
        "redness"
    ],
    "neurological": [
        "dizziness",
        "fainted",
        "loss of consciousness"
    ],
    "gastrointestinal": [
        "vomiting",
        "nausea",
        "abdominal pain"
    ]
}

def extract_medical_features(text):
    text = text.lower()
    text_emb = model.encode(text, convert_to_tensor=True)

    detected_systems = []
    matched_phrases = []

    for system, phrases in MEDICAL_CONCEPTS.items():
        for phrase in phrases:
            phrase_emb = model.encode(phrase, convert_to_tensor=True)
            similarity = util.cos_sim(text_emb, phrase_emb).item()

            if similarity > 0.55:
                detected_systems.append(system)
                matched_phrases.append(phrase)

    return {
        "body_systems": list(set(detected_systems)),
        "matched_phrases": list(set(matched_phrases))
    }
