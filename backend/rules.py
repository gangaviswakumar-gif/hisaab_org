import yaml
import os
from typing import Dict, Any, List

RATES_PATH = os.path.join(os.path.dirname(__file__), "rates.yaml")

def load_rates() -> Dict[str, Any]:
    if os.path.exists(RATES_PATH):
        try:
            with open(RATES_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

PREECLAMPSIA_SYMPTOMS = {
    "headache", "severe headache", "blurred vision", "vision problems",
    "swelling", "edema", "facial swelling", "swollen feet", "epigastric pain",
    "stomach pain", "nausea", "vomiting", "dizziness", "convulsions", "fits"
}

def evaluate_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates clinical triage rules.
    Input fields: bp_systolic, bp_diastolic, hemoglobin, symptoms
    Updates hrp_flag and alerts in the data dictionary.
    """
    bp_sys = data.get("bp_systolic")
    bp_dia = data.get("bp_diastolic")
    hb = data.get("hemoglobin")
    symptoms = [s.lower().strip() for s in (data.get("symptoms") or [])]
    
    hrp_flag = False
    alerts = []

    matched_symptoms = [s for s in symptoms if any(kw in s for kw in PREECLAMPSIA_SYMPTOMS)]
    is_hypertensive = (bp_sys is not None and bp_sys >= 140) or (bp_dia is not None and bp_dia >= 90)
    is_severe_hypertension = (bp_sys is not None and bp_sys >= 160) or (bp_dia is not None and bp_dia >= 110)
    is_hypotensive = (bp_sys is not None and bp_sys <= 90) or (bp_dia is not None and bp_dia <= 60)

    if is_severe_hypertension:
        hrp_flag = True
        alerts.append(f"CRITICAL: Severe Hypertension ({bp_sys}/{bp_dia} mmHg) - Immediate referral needed.")
    elif is_hypertensive:
        hrp_flag = True
        msg = f"HIGH RISK: Elevated BP ({bp_sys}/{bp_dia} mmHg)."
        if matched_symptoms:
            msg += f" Danger signs present ({', '.join(matched_symptoms)}). Suspect Pre-eclampsia."
        alerts.append(msg)
    elif is_hypotensive:
        hrp_flag = True
        alerts.append(f"WARNING: Low Blood Pressure ({bp_sys}/{bp_dia} mmHg) - Hypotension.")
        
    if not is_hypertensive and matched_symptoms:
        hrp_flag = True
        alerts.append(f"WARNING: Danger symptoms reported ({', '.join(matched_symptoms)}). Watch closely.")
        
    if hb is not None:
        if hb < 7.0:
            hrp_flag = True
            alerts.append(f"CRITICAL: Severe Anemia (Hb {hb} g/dL). Need immediate intervention.")
        elif hb < 11.0:
            hrp_flag = True
            alerts.append(f"WARNING: Moderate/Mild Anemia (Hb {hb} g/dL). Prescribe IFA tablets.")
            
    data["hrp_flag"] = hrp_flag
    data["alerts"] = alerts
    
    return data

def calculate_incentive(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates ASHA worker incentive claim from rates.yaml
    """
    rates_data = load_rates()
    incentives_cfg = rates_data.get("incentives", {})

    base_rate = incentives_cfg.get("anc_visit_regular", {}).get("rate", 100)
    
    breakdown = [{"item": "Routine Antenatal Care (ANC) Visit", "amount": base_rate}]
    total = base_rate

    if data.get("hrp_flag"):
        bonus_rate = incentives_cfg.get("high_risk_detection", {}).get("rate", 200)
        breakdown.append({
            "item": "High-Risk Pregnancy Identification & Triage",
            "amount": bonus_rate
        })
        total += bonus_rate
        
        # Check if severe hypertension is in alerts for extra bonus
        if any("CRITICAL: Severe Hypertension" in a for a in data.get("alerts", [])):
            severe_rate = incentives_cfg.get("severe_hypertension_referral", {}).get("rate", 300)
            breakdown.append({
                "item": "Critical / Emergency Referral",
                "amount": severe_rate
            })
            total += severe_rate

    return {
        "currency": "INR",
        "symbol": "₹",
        "breakdown": breakdown,
        "total_amount": total
    }
