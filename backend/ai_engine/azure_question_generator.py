import os
import json
from typing import List, Dict

import requests


def _env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and ((value[0] == value[-1]) and value[0] in ('"', "'")):
        value = value[1:-1]
    return value.strip() or None


def _is_configured() -> bool:
    return all(
        [
            _env("AZURE_ENDPOINT"),
            _env("AZURE_OPENAI_API_KEY"),
            _env("AZURE_API_VERSION"),
            _env("AZURE_DEPLOYMENT"),
        ]
    )


def generate_azure_followup_questions(
    drug_name: str,
    reaction: str,
    *,
    language: str = "en",
    n_questions: int = 3,
    timeout_seconds: int = 30,
) -> List[str]:
    """Generate follow-up questions using Azure OpenAI (Foundry) chat completions.

    Reads configuration from environment variables:
    - AZURE_ENDPOINT (e.g. https://xxxx.openai.azure.com/)
    - AZURE_OPENAI_API_KEY
    - AZURE_API_VERSION (e.g. 2025-01-01-preview)
    - AZURE_DEPLOYMENT (deployment name)

    Returns a list of questions. Raises on HTTP/parse errors.
    """

    if not _is_configured():
        raise RuntimeError("Azure OpenAI env vars are not fully configured")

    endpoint = _env("AZURE_ENDPOINT")
    api_key = _env("AZURE_OPENAI_API_KEY")
    api_version = _env("AZURE_API_VERSION")
    deployment = _env("AZURE_DEPLOYMENT")

    endpoint = endpoint.rstrip("/")
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"

    system = (
        "You are a pharmacovigilance assistant. "
        "Generate concise, clinically relevant follow-up questions to assess an adverse drug reaction. "
        "Avoid collecting unnecessary personal data."
    )

    user = (
        f"Drug: {drug_name}\n"
        f"Reaction: {reaction}\n\n"
        f"Generate exactly {n_questions} follow-up questions in {language}. "
        "Return ONLY a JSON array of strings."
    )

    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 250,
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    resp = requests.post(
        url,
        params={"api-version": api_version},
        headers=headers,
        json=payload,
        timeout=timeout_seconds,
    )
    resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    questions = json.loads(content)
    if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
        raise ValueError("Azure model did not return a JSON array of strings")

    questions = [q.strip() for q in questions if q.strip()]
    return questions[:n_questions]


def generate_azure_missing_field_questions(
    *,
    patient_initials: str,
    contact_no: str,
    missing_fields: List[str],
    language: str = "en",
    timeout_seconds: int = 30,
) -> Dict[str, str]:
    """Generate creative questions for missing CSV fields for one patient.

    Returns a mapping of field_name -> question.
    """

    if not _is_configured():
        raise RuntimeError("Azure OpenAI env vars are not fully configured")

    if not missing_fields:
        return {}

    endpoint = _env("AZURE_ENDPOINT")
    api_key = _env("AZURE_OPENAI_API_KEY")
    api_version = _env("AZURE_API_VERSION")
    deployment = _env("AZURE_DEPLOYMENT")

    endpoint = endpoint.rstrip("/")
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"

    system = (
        "You are a pharmacovigilance data-collection assistant. "
        "Your job is to ask patients for missing report fields. "
        "Be clear, empathetic, and concise. "
        "Ask exactly one question per field. "
        "Do not ask for extra information beyond the field."
    )

    patient_identifier = f"patient {patient_initials} (PHN: {contact_no})"
    fields_json = json.dumps(missing_fields, ensure_ascii=False)

    user = (
        f"Patient: {patient_identifier}\n"
        f"Missing fields (CSV column names): {fields_json}\n\n"
        f"Write questions in {language}. "
        "Return ONLY a JSON object where each key is the exact field name and the value is the question string."
    )

    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "max_tokens": 700,
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    resp = requests.post(
        url,
        params={"api-version": api_version},
        headers=headers,
        json=payload,
        timeout=timeout_seconds,
    )
    resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    mapping = json.loads(content)
    if not isinstance(mapping, dict):
        raise ValueError("Azure model did not return a JSON object")

    cleaned: Dict[str, str] = {}
    for field in missing_fields:
        q = mapping.get(field)
        if isinstance(q, str) and q.strip():
            cleaned[field] = q.strip()

    return cleaned
