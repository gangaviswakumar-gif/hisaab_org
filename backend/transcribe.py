import os
import torch
from faster_whisper import WhisperModel
from typing import Dict, Any
import sys

# Inject NVIDIA CUDA DLL paths for CTranslate2 on Windows
venv_base = os.path.dirname(os.path.dirname(sys.executable))
cublas_bin = os.path.join(venv_base, "Lib", "site-packages", "nvidia", "cublas", "bin")
cudnn_bin = os.path.join(venv_base, "Lib", "site-packages", "nvidia", "cudnn", "bin")
if os.path.exists(cublas_bin) and cublas_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = cublas_bin + os.pathsep + os.environ.get("PATH", "")
if os.path.exists(cudnn_bin) and cudnn_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = cudnn_bin + os.pathsep + os.environ.get("PATH", "")

_model = None

def get_whisper_model(model_size: str = "large-v3-turbo", force_cpu=False):
    global _model
    if _model is not None and not force_cpu:
        return _model
        
    device = "cpu" if force_cpu else "cuda"
    compute_type = "int8" if force_cpu else "float16"
    
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
    
    try:
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
    except Exception as e:
        print(f"Transcription failed on GPU: {e}. Falling back to CPU...")
        model = get_whisper_model(model_size, force_cpu=True)
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