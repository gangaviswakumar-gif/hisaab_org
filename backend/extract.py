import json
import re
import socket
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import ollama
except ImportError:
    ollama = None

PROMPT_TEMPLATE = """
You are an intelligent clinical extractor for ASHA healthcare workers in India.
Your job is to extract maternal health data from the voice transcript into strict JSON matching the schema below.

Required Schema:
{{
  "visit_id": "",
  "rch_id": "",
  "name": "",
  "husband_name": "",
  "age": null,
  "address": "",
  "mobile": "",
  "lmp": "",
  "edd": "",
  "gravida": null,
  "para": null,
  "visit_date": "",
  "weight_kg": null,
  "bp_systolic": null,
  "bp_diastolic": null,
  "hemoglobin": null,
  "symptoms": [],
  "hrp_flag": false,
  "alerts": []
}}

Example 1:
Transcript: "Visited Radha Devi, age 26, husband Rajesh. Second pregnancy, 1 child before. BP 150/95, weight 58kg, hemoglobin 10.2. Complains of severe headache."
Result:
{{
  "visit_id": "",
  "rch_id": "",
  "name": "Radha Devi",
  "husband_name": "Rajesh",
  "age": 26,
  "address": "",
  "mobile": "",
  "lmp": "",
  "edd": "",
  "gravida": 2,
  "para": 1,
  "visit_date": "{today}",
  "weight_kg": 58.0,
  "bp_systolic": 150,
  "bp_diastolic": 95,
  "hemoglobin": 10.2,
  "symptoms": ["severe headache"],
  "hrp_flag": false,
  "alerts": []
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
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Defaults
    bp_sys, bp_dia, weight_kg, hb, age, gravida, para = None, None, None, None, None, None, None

    bp_match = re.search(r'(?:bp|blood pressure)?\s*[:=]?\s*(\d{2,3})\s*(?:/|over|\s+)\s*(\d{2,3})', text)
    if bp_match:
        bp_sys = int(bp_match.group(1))
        bp_dia = int(bp_match.group(2))

    weight_match = re.search(r'(?:weight\s*[:=]?\s*)?(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)', text)
    if weight_match:
        weight_kg = float(weight_match.group(1))
        
    hb_match = re.search(r'(?:hb|hemoglobin)\s*[:=]?\s*(\d+(?:\.\d+)?)', text)
    if hb_match:
        hb = float(hb_match.group(1))
        
    age_match = re.search(r'(?:age|aged)\s*(\d{2})', text)
    if age_match:
        age = int(age_match.group(1))

    symptoms = []
    for sym in KNOWN_SYMPTOMS:
        if sym in text:
            symptoms.append(sym)

    name = ""
    name_patterns = [
        r'(?:visited|saw|met|patient|checking|checked)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,\s*(?:\d+|pregnant)',
    ]
    for pattern in name_patterns:
        m = re.search(pattern, transcript)
        if m:
            name = m.group(1).strip()
            break

    return {
        "visit_id": "",
        "rch_id": "",
        "name": name,
        "husband_name": "",
        "age": age,
        "address": "",
        "mobile": "",
        "lmp": "",
        "edd": "",
        "gravida": gravida,
        "para": para,
        "visit_date": today,
        "weight_kg": weight_kg,
        "bp_systolic": bp_sys,
        "bp_diastolic": bp_dia,
        "hemoglobin": hb,
        "symptoms": symptoms,
        "hrp_flag": False,
        "alerts": []
    }

def extract_visit_data(transcript: str, model_name: str = "llama3") -> Dict[str, Any]:
    extracted = None
    today = datetime.now().strftime("%Y-%m-%d")
    
    if ollama and is_ollama_available():
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': PROMPT_TEMPLATE.format(transcript=transcript, today=today)}],
                options={'temperature': 0.1},
                format='json'
            )
            content = response['message']['content'].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            extracted = json.loads(content)
        except Exception as e:
            print(f"[Ollama] Note: {e}")

    fallback = fallback_regex_extractor(transcript)
    if not extracted or not isinstance(extracted, dict):
        return fallback

    # Backfill with regex if missing
    for key in ["name", "bp_systolic", "bp_diastolic", "weight_kg", "hemoglobin", "age"]:
        if not extracted.get(key) and fallback.get(key):
            extracted[key] = fallback[key]
            
    if not extracted.get("symptoms") and fallback.get("symptoms"):
        extracted["symptoms"] = fallback["symptoms"]
        
    if not extracted.get("visit_date"):
        extracted["visit_date"] = today

    # Ensure defaults are initialized properly
    for key in ["visit_id", "rch_id", "husband_name", "address", "mobile", "lmp", "edd"]:
        if key not in extracted or extracted[key] is None:
            extracted[key] = ""
    for key in ["hrp_flag"]:
        if key not in extracted or extracted[key] is None:
            extracted[key] = False
    for key in ["alerts"]:
        if key not in extracted or extracted[key] is None:
            extracted[key] = []

    return extracted
