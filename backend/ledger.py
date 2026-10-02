import hashlib
import os
from typing import Dict, Any, List

def compute_record_hash(prev_hash: str, rch_id: str, visit_date: str, 
                        bp_sys: Any, bp_dia: Any, weight: Any, hb: Any, 
                        symptoms: str, hrp_flag: int, alerts: str) -> str:
    payload = f"{prev_hash}|{rch_id}|{visit_date}|{bp_sys}|{bp_dia}|{weight}|{hb}|{symptoms}|{hrp_flag}|{alerts}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def get_last_hash() -> str:
    from backend.database import get_db
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
    with get_db() as conn:
        cursor = conn.execute("SELECT hash FROM visits ORDER BY visit_id DESC LIMIT 1")
        row = cursor.fetchone()
        if row and row["hash"]:
            return row["hash"]
    return GENESIS_HASH

def sign_visit_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """Adds prev_hash and hash to the visit data dict"""
    import json
    prev_hash = get_last_hash()
    
    symptoms_str = json.dumps(data.get("symptoms", []))
    alerts_str = json.dumps(data.get("alerts", []))
    hrp_flag = 1 if data.get("hrp_flag") else 0
    
    current_hash = compute_record_hash(
        prev_hash=prev_hash,
        rch_id=data.get("rch_id", ""),
        visit_date=data.get("visit_date", ""),
        bp_sys=data.get("bp_systolic"),
        bp_dia=data.get("bp_diastolic"),
        weight=data.get("weight_kg"),
        hb=data.get("hemoglobin"),
        symptoms=symptoms_str,
        hrp_flag=hrp_flag,
        alerts=alerts_str
    )
    
    data["prev_hash"] = prev_hash
    data["hash"] = current_hash
    return data

def verify_ledger() -> Dict[str, Any]:
    """
    Cryptographically verifies the SHA-256 blockchain tamper-proof chain.
    """
    from backend.database import get_db, init_db
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
    init_db()
    
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM visits ORDER BY ROWID ASC")
        rows = cursor.fetchall()
        
    expected_prev = GENESIS_HASH
    for r in rows:
        recalc_hash = compute_record_hash(
            prev_hash=r["prev_hash"],
            rch_id=r["rch_id"],
            visit_date=r["visit_date"],
            bp_sys=r["bp_systolic"],
            bp_dia=r["bp_diastolic"],
            weight=r["weight_kg"],
            hb=r["hemoglobin"],
            symptoms=r["symptoms"],
            hrp_flag=r["hrp_flag"],
            alerts=r["alerts"]
        )
        if r["prev_hash"] != expected_prev:
            return {
                "is_valid": False,
                "error": f"Broken chain link at Visit #{r['visit_id']}. Previous hash mismatch."
            }
        if r["hash"] != recalc_hash:
            return {
                "is_valid": False,
                "error": f"Tampered record detected at Visit #{r['visit_id']}. Content hash mismatch."
            }
        expected_prev = r["hash"]

    return {
        "is_valid": True,
        "total_records": len(rows),
        "status": "Ledger verified: All records cryptographically authentic and tamper-free."
    }

def get_ledger_stats() -> Dict[str, Any]:
    from backend.database import get_db, init_db
    init_db()
    with get_db() as conn:
        total_visits = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        high_risk_cases = conn.execute("SELECT COUNT(*) FROM visits WHERE hrp_flag = 1").fetchone()[0]
        
    # Since incentives aren't strictly stored in DB in this version, we approximate
    # by running calculate_incentive over all visits.
    from backend.rules import calculate_incentive
    from backend.database import get_all_visits
    total_incentives = 0.0
    for v in get_all_visits():
        inc = calculate_incentive(v)
        total_incentives += inc["total_amount"]
        
    return {
        "total_visits": total_visits,
        "high_risk_cases": high_risk_cases,
        "total_incentives": total_incentives
    }
