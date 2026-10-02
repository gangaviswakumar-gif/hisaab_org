import yaml
import os
from typing import Dict, Any, List, Optional

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
    Evaluates clinical triage & pre-eclampsia risk check rules.
    Input fields: bp_sys, bp_dia, symptoms, gestational_age_weeks, weight_kg
    """
    bp_sys = data.get("bp_sys")
    bp_dia = data.get("bp_dia")
    symptoms = [s.lower().strip() for s in (data.get("symptoms") or [])]
    ga = data.get("gestational_age_weeks")
    weight = data.get("weight_kg")

    risk_level = "NORMAL"
    risk_flags: List[str] = []
    recommendations: List[str] = []

    # Check for symptoms matching pre-eclampsia warning signs
    matched_symptoms = [s for s in symptoms if any(kw in s for kw in PREECLAMPSIA_SYMPTOMS)]

    is_hypertensive = (bp_sys is not None and bp_sys >= 140) or (bp_dia is not None and bp_dia >= 90)
    is_severe_hypertension = (bp_sys is not None and bp_sys >= 160) or (bp_dia is not None and bp_dia >= 110)

    # 1. Critical Hypertensive Crisis
    if is_severe_hypertension:
        risk_level = "CRITICAL"
        risk_flags.append(f"Severe Hypertension ({bp_sys}/{bp_dia} mmHg)")
        recommendations.append("EMERGENCY: Immediate referral to District Hospital / FRU for antihypertensive therapy.")

    # 2. Suspected Pre-eclampsia
    if is_hypertensive and matched_symptoms:
        if risk_level != "CRITICAL":
            risk_level = "HIGH_RISK"
        symptom_str = ", ".join(matched_symptoms)
        risk_flags.append(f"Suspected Pre-eclampsia: Elevated BP ({bp_sys}/{bp_dia} mmHg) with danger symptoms ({symptom_str})")
        recommendations.append("URGENT: Transfer to Community Health Centre (CHC) for urine protein check & OB-GYN evaluation.")
    elif is_hypertensive and not is_severe_hypertension:
        if risk_level == "NORMAL":
            risk_level = "MODERATE_RISK"
        risk_flags.append(f"Stage 1 Gestational Hypertension ({bp_sys}/{bp_dia} mmHg)")
        recommendations.append("Repeat BP measurement within 4 hours; advise low sodium diet and weekly follow-up.")

    # 3. Danger symptoms without high BP
    if not is_hypertensive and matched_symptoms:
        if risk_level == "NORMAL":
            risk_level = "MODERATE_RISK"
        risk_flags.append(f"Maternal Warning Signs: {', '.join(matched_symptoms)}")
        recommendations.append("Advise rest, adequate hydration, and visit PHC if symptoms persist.")

    # 4. Low Maternal Weight Check
    if weight is not None and weight > 0 and weight < 45:
        risk_flags.append(f"Low Maternal Weight ({weight} kg) - Underweight Risk")
        recommendations.append("Enroll in Supplementary Nutrition Programme (ICDS Anganwadi) and prescribe IFA tablets.")

    # 5. Normal visit
    if not risk_flags:
        recommendations.append("Routine pregnancy progression. Continue Iron-Folic Acid (IFA) & Calcium supplementation.")

    return {
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "recommendations": recommendations,
        "has_preeclampsia_risk": "Suspected Pre-eclampsia" in " ".join(risk_flags)
    }

def calculate_incentive(risk_evaluation: Dict[str, Any], visit_type: str = "anc_visit_regular") -> Dict[str, Any]:
    """
    Calculates ASHA worker incentive claim from rates.yaml
    """
    rates_data = load_rates()
    incentives_cfg = rates_data.get("incentives", {})

    base_rate = incentives_cfg.get("anc_visit_regular", {}).get("rate", 100)
    risk_level = risk_evaluation.get("risk_level", "NORMAL")

    breakdown = [
        {"item": "Routine Antenatal Care (ANC) Visit", "amount": base_rate}
    ]
    total = base_rate

    # Extra bonus for early detection & referral of high-risk cases
    if risk_level in ["HIGH_RISK", "CRITICAL"]:
        bonus_rate = incentives_cfg.get("high_risk_detection", {}).get("rate", 200)
        breakdown.append({
            "item": f"High-Risk / Pre-eclampsia Triage Incentive ({risk_level})",
            "amount": bonus_rate
        })
        total += bonus_rate

    return {
        "currency": "INR",
        "symbol": "₹",
        "breakdown": breakdown,
        "total_amount": total
    }

if __name__ == "__main__":
    sample_data = {
        "name": "Radha",
        "gestational_age_weeks": 24,
        "bp_sys": 150,
        "bp_dia": 95,
        "weight_kg": 58,
        "symptoms": ["severe headache", "swollen feet"]
    }
    risk = evaluate_risk(sample_data)
    print("Risk Assessment:", risk)
    incentive = calculate_incentive(risk)
    print("Incentive:", incentive)
