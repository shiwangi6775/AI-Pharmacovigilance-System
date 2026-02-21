import joblib
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
model = joblib.load("risk_model.pkl")

def predict_risk_probability(text):
    emb = embedder.encode([text])
    prob = model.predict_proba(emb)[0][1]
    return float(prob)
