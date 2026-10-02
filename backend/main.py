import os
import shutil
import uuid
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.transcribe import transcribe_audio
from backend.extract import extract_visit_data
from backend.rules import evaluate_risk, calculate_incentive, load_rates
from backend.ledger import add_visit, get_all_visits, verify_ledger, get_ledger_stats, init_db
from backend.pdf_generator import generate_incentive_pdf

app = FastAPI(
    title="Hisaab: ASHA Voice-to-Ledger Clinical Platform",
    description="Offline voice-to-data web app for ASHA workers with AI clinical extraction, pre-eclampsia triage, SHA-256 tamper-proof ledger, and automated incentive claims.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Mount frontend static files
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Initialize SQLite database on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return RedirectResponse(url="/frontend/index.html")

# --- Audio Recording & AI Extraction ---

@app.post("/api/record")
async def record_audio(file: UploadFile = File(...)):
    """
    Receives voice audio from frontend MediaRecorder (or file upload),
    transcribes it with Whisper (task='translate'), extracts clinical data,
    evaluates pre-eclampsia triage rules, and returns initial draft for confirmation.
    """
    file_ext = os.path.splitext(file.filename or "")[1] or ".wav"
    unique_filename = f"rec_{uuid.uuid4().hex[:8]}{file_ext}"
    saved_path = os.path.join(SAMPLES_DIR, unique_filename)

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {e}")

    # 1. Transcribe audio to translated English
    try:
        transcript = transcribe_audio(saved_path)
    except Exception as e:
        # If whisper fails on invalid empty audio or missing ffmpeg
        transcript = f"[Transcription Notice: Processed audio from {unique_filename}]"
        print(f"[Whisper Error]: {e}")

    # 2. Extract clinical data with Ollama (or smart heuristic fallback)
    extracted = extract_visit_data(transcript)

    # 3. Clinical Risk Triage & Pre-eclampsia check
    risk = evaluate_risk(extracted)

    # 4. Calculate ASHA incentive based on rates.yaml
    incentive = calculate_incentive(risk)

    return {
        "audio_filename": unique_filename,
        "transcript": transcript,
        "extracted": extracted,
        "risk": risk,
        "incentive": incentive
    }

class TextVisitRequest(BaseModel):
    text: str

@app.post("/api/process-text")
def process_text_transcript(payload: TextVisitRequest):
    """
    Allows instant testing without microphone by directly entering voice note text.
    """
    transcript = payload.text.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript text cannot be empty.")
        
    extracted = extract_visit_data(transcript)
    risk = evaluate_risk(extracted)
    incentive = calculate_incentive(risk)

    return {
        "audio_filename": "manual_entry.txt",
        "transcript": transcript,
        "extracted": extracted,
        "risk": risk,
        "incentive": incentive
    }

@app.post("/api/evaluate-rules")
def re_evaluate_rules(data: Dict[str, Any]):
    """
    Dynamically recalculates risk triage and incentive as the user edits fields in confirm.html
    """
    risk = evaluate_risk(data)
    incentive = calculate_incentive(risk)
    return {
        "risk": risk,
        "incentive": incentive
    }

# --- Ledger & Blockchain Verification ---

class ConfirmVisitRequest(BaseModel):
    name: str
    gestational_age_weeks: Optional[int] = None
    bp_sys: Optional[int] = None
    bp_dia: Optional[int] = None
    weight_kg: Optional[float] = None
    symptoms: Optional[list] = []
    transcript: Optional[str] = ""
    audio_filename: Optional[str] = ""

@app.post("/api/confirm")
def confirm_and_sign_visit(visit_data: ConfirmVisitRequest):
    """
    Saves the user-reviewed clinical visit data into the SQLite ledger
    with a cryptographic SHA-256 blockchain hash.
    """
    data_dict = visit_data.model_dump()
    risk = evaluate_risk(data_dict)
    incentive = calculate_incentive(risk)

    data_dict["risk_level"] = risk["risk_level"]
    data_dict["risk_flags"] = risk["risk_flags"]
    data_dict["recommendations"] = risk["recommendations"]
    data_dict["incentive_amount"] = incentive["total_amount"]

    saved_record = add_visit(data_dict)
    return {
        "success": True,
        "message": "Visit successfully verified and recorded into SHA-256 ledger.",
        "record": saved_record
    }

@app.get("/api/visits")
def list_visits():
    """
    Returns all logged visits for the digital register.
    """
    return get_all_visits()

@app.get("/api/stats")
def ledger_stats():
    """
    Returns top-level KPI metrics for the ASHA worker dashboard.
    """
    stats = get_ledger_stats()
    verification = verify_ledger()
    return {
        "stats": stats,
        "verification": verification
    }

@app.get("/api/verify")
def verify_blockchain():
    """
    Cryptographically verifies the ledger hash chain.
    """
    return verify_ledger()

@app.get("/api/rates")
def get_rates():
    """
    Returns current incentive rate sheet.
    """
    return load_rates()

@app.get("/api/export-pdf")
def export_pdf(worker_name: str = "Anugrah K (ASHA Worker #4102)", phc: str = "Primary Health Centre, Ward 4"):
    """
    Generates and downloads the NHM Monthly Incentive Claim PDF.
    """
    pdf_path = os.path.join(SAMPLES_DIR, "asha_monthly_claim_report.pdf")
    generate_incentive_pdf(
        output_filename=pdf_path,
        worker_name=worker_name,
        phc_name=phc
    )
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="ASHA_Incentive_Claim_Report.pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
