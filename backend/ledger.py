import sqlite3
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hisaab.db")
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            gestational_age_weeks INTEGER,
            bp_sys INTEGER,
            bp_dia INTEGER,
            weight_kg REAL,
            symptoms TEXT,
            risk_level TEXT NOT NULL,
            risk_flags TEXT,
            recommendations TEXT,
            transcript TEXT,
            audio_filename TEXT,
            incentive_amount REAL NOT NULL DEFAULT 100.0,
            prev_hash TEXT NOT NULL,
            hash TEXT NOT NULL
        )
        """)
        conn.commit()

def compute_record_hash(prev_hash: str, timestamp: str, patient_name: str, 
                        bp_sys: Optional[int], bp_dia: Optional[int], 
                        risk_level: str, incentive_amount: float, transcript: str) -> str:
    payload = f"{prev_hash}|{timestamp}|{patient_name}|{bp_sys}|{bp_dia}|{risk_level}|{incentive_amount:.2f}|{transcript}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def get_last_hash() -> str:
    with get_db() as conn:
        cursor = conn.execute("SELECT hash FROM visits ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row and row["hash"]:
            return row["hash"]
    return GENESIS_HASH

def add_visit(data: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    prev_hash = get_last_hash()
    timestamp = data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    patient_name = data.get("name") or data.get("patient_name") or "Anonymous Patient"
    gestational_age_weeks = data.get("gestational_age_weeks")
    bp_sys = data.get("bp_sys")
    bp_dia = data.get("bp_dia")
    weight_kg = data.get("weight_kg")
    
    symptoms = data.get("symptoms") or []
    if isinstance(symptoms, list):
        symptoms_str = json.dumps(symptoms)
    else:
        symptoms_str = str(symptoms)
        
    risk_level = data.get("risk_level", "NORMAL")
    
    risk_flags = data.get("risk_flags") or []
    risk_flags_str = json.dumps(risk_flags) if isinstance(risk_flags, list) else str(risk_flags)
    
    recommendations = data.get("recommendations") or []
    recs_str = json.dumps(recommendations) if isinstance(recommendations, list) else str(recommendations)
    
    transcript = data.get("transcript") or ""
    audio_filename = data.get("audio_filename") or ""
    incentive_amount = float(data.get("incentive_amount") or 100.0)

    record_hash = compute_record_hash(
        prev_hash=prev_hash,
        timestamp=timestamp,
        patient_name=patient_name,
        bp_sys=bp_sys,
        bp_dia=bp_dia,
        risk_level=risk_level,
        incentive_amount=incentive_amount,
        transcript=transcript
    )

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO visits (
                timestamp, patient_name, gestational_age_weeks, bp_sys, bp_dia,
                weight_kg, symptoms, risk_level, risk_flags, recommendations,
                transcript, audio_filename, incentive_amount, prev_hash, hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, patient_name, gestational_age_weeks, bp_sys, bp_dia,
            weight_kg, symptoms_str, risk_level, risk_flags_str, recs_str,
            transcript, audio_filename, incentive_amount, prev_hash, record_hash
        ))
        conn.commit()
        record_id = cursor.lastrowid

    return {
        "id": record_id,
        "hash": record_hash,
        "prev_hash": prev_hash,
        "patient_name": patient_name,
        "timestamp": timestamp,
        "incentive_amount": incentive_amount,
        "risk_level": risk_level
    }

def get_all_visits() -> List[Dict[str, Any]]:
    init_db()
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM visits ORDER BY id DESC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            row_dict = dict(r)
            try:
                row_dict["symptoms"] = json.loads(row_dict["symptoms"])
            except Exception:
                pass
            try:
                row_dict["risk_flags"] = json.loads(row_dict["risk_flags"])
            except Exception:
                pass
            try:
                row_dict["recommendations"] = json.loads(row_dict["recommendations"])
            except Exception:
                pass
            result.append(row_dict)
        return result

def verify_ledger() -> Dict[str, Any]:
    """
    Cryptographically verifies the SHA-256 blockchain tamper-proof chain.
    """
    init_db()
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM visits ORDER BY id ASC")
        rows = cursor.fetchall()
        
    expected_prev = GENESIS_HASH
    for r in rows:
        recalc_hash = compute_record_hash(
            prev_hash=r["prev_hash"],
            timestamp=r["timestamp"],
            patient_name=r["patient_name"],
            bp_sys=r["bp_sys"],
            bp_dia=r["bp_dia"],
            risk_level=r["risk_level"],
            incentive_amount=r["incentive_amount"],
            transcript=r["transcript"]
        )
        if r["prev_hash"] != expected_prev:
            return {
                "is_valid": False,
                "error": f"Broken chain link at Record #{r['id']}. Previous hash mismatch.",
                "record_id": r["id"]
            }
        if r["hash"] != recalc_hash:
            return {
                "is_valid": False,
                "error": f"Tampered record detected at Record #{r['id']}. Content hash mismatch.",
                "record_id": r["id"]
            }
        expected_prev = r["hash"]

    return {
        "is_valid": True,
        "total_records": len(rows),
        "status": "Ledger verified: All records cryptographically authentic and tamper-free."
    }

def get_ledger_stats() -> Dict[str, Any]:
    init_db()
    with get_db() as conn:
        total_visits = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        high_risk_cases = conn.execute("SELECT COUNT(*) FROM visits WHERE risk_level IN ('HIGH_RISK', 'CRITICAL')").fetchone()[0]
        total_incentives = conn.execute("SELECT COALESCE(SUM(incentive_amount), 0) FROM visits").fetchone()[0]
        
    return {
        "total_visits": total_visits,
        "high_risk_cases": high_risk_cases,
        "total_incentives": total_incentives
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
    sample = {
        "name": "Radha Devi",
        "gestational_age_weeks": 26,
        "bp_sys": 150,
        "bp_dia": 95,
        "weight_kg": 58.5,
        "symptoms": ["headache", "swollen feet"],
        "risk_level": "HIGH_RISK",
        "risk_flags": ["Suspected Pre-eclampsia"],
        "recommendations": ["Immediate CHC referral"],
        "transcript": "Visited Radha, 6 months pregnant, BP 150/95, severe headache.",
        "incentive_amount": 300.0
    }
    rec = add_visit(sample)
    print("Added visit:", rec)
    verification = verify_ledger()
    print("Verification:", verification)
    stats = get_ledger_stats()
    print("Stats:", stats)
