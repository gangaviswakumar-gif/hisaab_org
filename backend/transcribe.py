import os
import torch
from faster_whisper import WhisperModel
from typing import Dict, Any

_model = None

def get_whisper_model(model_size: str = "large-v3-turbo"):
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"Loading faster-whisper '{model_size}' on {device} ({compute_type})...")
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("faster-whisper model loaded.")
    return _model

def transcribe_audio(file_path: str, model_size: str = "large-v3-turbo") -> Dict[str, Any]:
    """
    Transcribes audio and translates it directly into English.
    Returns: {"transcript", "detected_language", "language_confidence"}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
        
    model = get_whisper_model(model_size)
    
    domain_prompt = (
        "ASHA worker antenatal care visit. "
        "Patient name, pregnant woman, blood pressure, BP 120/80, headache, fever, swelling, weight, kilograms, weeks."
    )
    
    segments, info = model.transcribe(
        file_path,
        task="translate",
        language=None,
        initial_prompt=domain_prompt,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        beam_size=5
    )
    
    translated_text = " ".join([seg.text.strip() for seg in segments])
    
    return {
        "transcript": translated_text.strip(),
        "detected_language": info.language,
        "language_confidence": info.language_probability
    }