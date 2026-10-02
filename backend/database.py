import sqlite3
import os
import json
import uuid
from typing import Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hisaab.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            rch_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            husband_name TEXT,
            age INTEGER,
            address TEXT,
            mobile TEXT,
            lmp TEXT,
            edd TEXT,
            gravida INTEGER,
            para INTEGER
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            visit_id TEXT PRIMARY KEY,
            rch_id TEXT,
            visit_date TEXT NOT NULL,
            weight_kg REAL,
            bp_systolic INTEGER,
            bp_diastolic INTEGER,
            hemoglobin REAL,
            symptoms TEXT,
            hrp_flag INTEGER,
            alerts TEXT,
            prev_hash TEXT,
            hash TEXT,
            FOREIGN KEY (rch_id) REFERENCES patients (rch_id)
        )
        """)
        conn.commit()

def save_patient(data: Dict[str, Any]):
    init_db()
    rch_id = data.get("rch_id")
    if not rch_id:
        rch_id = f"RCH-{str(uuid.uuid4())[:8].upper()}"
        data["rch_id"] = rch_id

    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO patients (
                rch_id, name, husband_name, age, address, mobile, lmp, edd, gravida, para
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rch_id,
            data.get("name"),
            data.get("husband_name"),
            data.get("age"),
            data.get("address"),
            data.get("mobile"),
            data.get("lmp"),
            data.get("edd"),
            data.get("gravida"),
            data.get("para")
        ))
        conn.commit()
    return rch_id

def save_visit(data: Dict[str, Any]):
    init_db()
    
    # Ensure patient exists
    save_patient(data)

    visit_id = data.get("visit_id")
    if not visit_id:
        visit_id = f"V-{str(uuid.uuid4())[:8].upper()}"
        data["visit_id"] = visit_id

    symptoms_str = json.dumps(data.get("symptoms") or [])
    alerts_str = json.dumps(data.get("alerts") or [])
    hrp_flag = 1 if data.get("hrp_flag") else 0

    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO visits (
                visit_id, rch_id, visit_date, weight_kg, bp_systolic, bp_diastolic,
                hemoglobin, symptoms, hrp_flag, alerts, prev_hash, hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            visit_id,
            data.get("rch_id"),
            data.get("visit_date"),
            data.get("weight_kg"),
            data.get("bp_systolic"),
            data.get("bp_diastolic"),
            data.get("hemoglobin"),
            symptoms_str,
            hrp_flag,
            alerts_str,
            data.get("prev_hash", ""),
            data.get("hash", "")
        ))
        conn.commit()
    return visit_id

def _dict_factory(row) -> Dict[str, Any]:
    d = dict(row)
    if "symptoms" in d and isinstance(d["symptoms"], str):
        try: d["symptoms"] = json.loads(d["symptoms"])
        except: d["symptoms"] = []
    if "alerts" in d and isinstance(d["alerts"], str):
        try: d["alerts"] = json.loads(d["alerts"])
        except: d["alerts"] = []
    if "hrp_flag" in d:
        d["hrp_flag"] = bool(d["hrp_flag"])
    return d

def get_all_visits() -> List[Dict[str, Any]]:
    init_db()
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT v.*, p.name, p.husband_name, p.age, p.address, p.mobile, 
                   p.lmp, p.edd, p.gravida, p.para
            FROM visits v
            JOIN patients p ON v.rch_id = p.rch_id
            ORDER BY v.visit_date DESC, v.visit_id DESC
        """)
        return [_dict_factory(r) for r in cursor.fetchall()]

def get_flagged_visits() -> List[Dict[str, Any]]:
    init_db()
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT v.*, p.name, p.husband_name, p.age, p.address, p.mobile, 
                   p.lmp, p.edd, p.gravida, p.para
            FROM visits v
            JOIN patients p ON v.rch_id = p.rch_id
            WHERE v.hrp_flag = 1
            ORDER BY v.visit_date DESC, v.visit_id DESC
        """)
        return [_dict_factory(r) for r in cursor.fetchall()]
