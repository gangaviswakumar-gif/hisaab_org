import os
import sys
import torch
from faster_whisper import WhisperModel

_model = None

def get_whisper_model(model_size: str = "large-v2"):
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "float32"

        print(f"Loading faster-whisper '{model_size}' on {device} ({compute_type})...")
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("faster-whisper model loaded.")
    return _model


def transcribe_audio(file_path: str, model_size: str = "large-v2") -> str:
    """Transcribes Malayalam audio and translates it directly into English."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    model = get_whisper_model(model_size)

    domain_prompt = (
        "Translate to English. ASHA worker antenatal care visit. "
        "Patient name, pregnant woman, blood pressure, BP 120/80, headache, fever, swelling, weight, kilograms, weeks."
    )

    segments, info = model.transcribe(
        file_path,
        task="translate",
        language="ml",
        initial_prompt=domain_prompt,
        vad_filter=True,        # skips silence; helps with long pauses in voice notes
        beam_size=5,
    )

    translated_text = " ".join(seg.text.strip() for seg in segments)
    print(f"Detected language: {info.language} (Confidence: {info.language_probability:.2f})")
    return translated_text.strip()


if __name__ == "__main__":
    # Use a path from the command line if given, otherwise default to mal.ogg
    test_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join("samples", "english.ogg")

    if os.path.exists(test_file):
        print(f"Translating {test_file}...")
        result = transcribe_audio(test_file)
        print("\n--- ENGLISH TRANSLATION ---")
        print(result)
        print("---------------------------")

        # Save to a text file next to the audio
        out_path = os.path.splitext(test_file)[0] + "_english.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved to {out_path}")
    else:
        print(f"File '{test_file}' not found. Put it in the same folder as this script.")