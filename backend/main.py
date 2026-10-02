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
from backend.rules import evaluate_risk
from backend.database import save_visit, get_all_visits, get_flagged_visits, init_db
from backend.ledger import sign_visit_record, verify_ledger, get_ledger_stats
from backend.pdf_generator import generate_incentive_pdf

app = FastAPI(
    title="Hisaab: ASHA Voice-to-Ledger Clinical Platform",
    description="Offline voice-to-data web app for ASHA workers.",
    version="1.0.0"
)

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

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return RedirectResponse(url="/frontend/index.html")

# 1. Transcribe endpoint
@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    file_ext = os.path.splitext(file.filename or "")[1] or ".wav"
    unique_filename = f"rec_{uuid.uuid4().hex[:8]}{file_ext}"
    saved_path = os.path.join(SAMPLES_DIR, unique_filename)

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {e}")

    try:
        result = transcribe_audio(saved_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

class ExtractRequest(BaseModel):
    transcript: str

# 2. Extract endpoint
@app.post("/extract")
def extract_endpoint(req: ExtractRequest):
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript is empty")
    
    extracted_data = extract_visit_data(req.transcript)
    return extracted_data

# 3. Confirm Visit endpoint
@app.post("/confirm-visit")
def confirm_visit_endpoint(payload: Dict[str, Any]):
    # 1. Re-evaluate rules (in case user edited BP/symptoms on frontend)
    evaluated_data = evaluate_risk(payload)
    
    # 2. Sign the record cryptographically (adds hash and prev_hash)
    signed_data = sign_visit_record(evaluated_data)
    
    # 3. Save to SQLite database (creates patient if missing, adds visit)
    visit_id = save_visit(signed_data)
    
    return {"success": True, "visit_id": visit_id, "record": signed_data}

# 4. Get all visits
@app.get("/visits")
def get_visits_endpoint():
    return get_all_visits()

# 5. Get flagged visits
@app.get("/visits/flagged")
def get_flagged_visits_endpoint():
    return get_flagged_visits()

# 6. Generate Claim PDF
@app.post("/generate-claim")
def generate_claim_endpoint():
    pdf_path = os.path.join(BASE_DIR, "asha_monthly_claim_report.pdf")
    generate_incentive_pdf(
        output_filename=pdf_path,
        worker_name="Anugrah K (ASHA Worker #4102)",
        phc_name="Primary Health Centre, Ward 4"
    )
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")

    # Auto-open the PDF locally for the demo
    import platform
    if platform.system() == "Windows":
        os.startfile(pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="ASHA_Incentive_Claim_Report.pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
