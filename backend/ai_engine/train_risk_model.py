import pandas as pd
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

# embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# research-grade synthetic ADR dataset
data = {
    "text": [
        "mild headache",
        "skin rash",
        "itching on arms",
        "vomiting and nausea",
        "chest tightness",
        "difficulty breathing",
        "severe allergic reaction",
        "loss of consciousness",
        "swelling of lips and face",
        "fainted suddenly"
    ],
    "label": [
        0, 0, 0, 0,
        1, 1, 1, 1, 1, 1
    ]  # 1 = serious ADR
}

df = pd.DataFrame(data)

X = embedder.encode(df["text"].tolist())
y = np.array(df["label"])

clf = LogisticRegression(max_iter=1000)
clf.fit(X, y)

joblib.dump(clf, "risk_model.pkl")

print("✅ Risk prediction model trained successfully")

