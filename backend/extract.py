import json
import re
import socket
from typing import Dict, Any, Optional

try:
    import ollama
except ImportError:
    ollama = None

PROMPT_TEMPLATE = """
You are an intelligent clinical extractor for ASHA healthcare workers in India.
Your job is to extract maternal health data from the voice transcript into strict JSON.

Example 1:
Transcript: "Visited Radha Devi, 6 months pregnant, BP 150/95, severe headache, weight 58kg"
Result:
{{
  "name": "Radha Devi",
  "gestational_age_weeks": 26,
  "bp_sys": 150,
  "bp_dia": 95,
  "weight_kg": 58.0,
  "symptoms": ["severe headache"]
}}

Example 2:
Transcript: "Patient Sunita, 28 weeks, blood pressure 120 over 80, no complaints, weight 62 kg"
Result:
{{
  "name": "Sunita",
  "gestational_age_weeks": 28,
  "bp_sys": 120,
  "bp_dia": 80,
  "weight_kg": 62.0,
  "symptoms": []
}}

Now extract data from this transcript:
Transcript: "{transcript}"

Return ONLY the raw JSON object. Do not include markdown codeblocks or conversational text.
"""

KNOWN_SYMPTOMS = [
    "severe headache", "headache", "blurred vision", "vision problems",
    "swelling", "swollen feet", "edema", "facial swelling", "epigastric pain",
    "stomach pain", "abdominal pain", "nausea", "vomiting", "dizziness",
    "fever", "convulsions", "fits", "fatigue", "tiredness", "breathlessness"
]

def is_ollama_available(host: str = "127.0.0.1", port: int = 11434, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def fallback_regex_extractor(transcript: str) -> Dict[str, Any]:
    text = transcript.lower()
    
    # 1. Blood Pressure: e.g. "150/95", "140 over 90", "bp 130 85"
    bp_sys: Optional[int] = None
    bp_dia: Optional[int] = None
    bp_match = re.search(r'(?:bp|blood pressure)?\s*[:=]?\s*(\d{2,3})\s*(?:/|over|\s+)\s*(\d{2,3})', text)
    if bp_match:
        bp_sys = int(bp_match.group(1))
        bp_dia = int(bp_match.group(2))

    # 2. Gestational age: e.g. "6 months", "24 weeks", "second trimester"
    ga_weeks: Optional[int] = None
    week_match = re.search(r'(\d+)\s*(?:weeks?|wk)', text)
    if week_match:
        ga_weeks = int(week_match.group(1))
    else:
        month_match = re.search(r'(\d+)\s*(?:months?|mth)', text)
        if month_match:
            months = int(month_match.group(1))
            ga_weeks = int(round(months * 4.33))

    # 3. Weight: e.g. "58kg", "58 kg", "weight 60 kilograms"
    weight_kg: Optional[float] = None
    weight_match = re.search(r'(?:weight\s*[:=]?\s*)?(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)', text)
    if weight_match:
        weight_kg = float(weight_match.group(1))

    # 4. Symptoms
    symptoms = []
    for sym in KNOWN_SYMPTOMS:
        if sym in text:
            symptoms.append(sym)
    filtered_symptoms = []
    for s in symptoms:
        if not any(other != s and s in other for other in symptoms):
            filtered_symptoms.append(s)

    # 5. Patient Name
    name: Optional[str] = None
    name_patterns = [
        r'(?:visited|saw|met|patient|checking|checked)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,\s*(?:\d+|pregnant)',
    ]
    for pattern in name_patterns:
        m = re.search(pattern, transcript)
        if m:
            name = m.group(1).strip()
            break
            
    if not name:
        words = transcript.strip().split()
        if words and words[0].isalpha() and words[0].istitle():
            name = words[0]

    return {
        "name": name,
        "gestational_age_weeks": ga_weeks,
        "bp_sys": bp_sys,
        "bp_dia": bp_dia,
        "weight_kg": weight_kg,
        "symptoms": filtered_symptoms
    }

def extract_visit_data(transcript: str, model_name: str = "llama3") -> Dict[str, Any]:
    extracted = None
    if ollama and is_ollama_available():
        try:
            # Tell Ollama to strictly return JSON
            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': PROMPT_TEMPLATE.format(transcript=transcript)}],
                options={'temperature': 0.1},
                format='json'
            )
            content = response['message']['content'].strip()
            
            # Since format='json' is enabled, the output is guaranteed valid JSON
            # However, we still handle potential markdown backticks just in case
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            extracted = json.loads(content)
        except Exception as e:
            print(f"[Ollama] Note: {e}")

    # Fallback / Backfill
    fallback = fallback_regex_extractor(transcript)
    if not extracted or not isinstance(extracted, dict):
        return fallback

    # Backfill any nulls from regex heuristic
    for key in ["name", "gestational_age_weeks", "bp_sys", "bp_dia", "weight_kg"]:
        if extracted.get(key) is None and fallback.get(key) is not None:
            extracted[key] = fallback[key]

    if not extracted.get("symptoms") and fallback.get("symptoms"):
        extracted["symptoms"] = fallback["symptoms"]

    return extracted

if __name__ == "__main__":
    sample_text = "Visited Radha Devi, 6 months pregnant, BP 150/95, complains of severe headache and swollen feet, weight 58kg"
    print("Testing extraction on:", sample_text)
    result = extract_visit_data(sample_text)
    print("\nResult:")
    print(json.dumps(result, indent=2))
