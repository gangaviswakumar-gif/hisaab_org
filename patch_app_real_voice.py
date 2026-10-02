import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
// MediaRecorder setup for index.html
let mediaRecorder;
let audioChunks = [];
let recordingInterval = null;
let secondsCount = 0;
let isRecording = false;

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.start();
        return true;
    } catch (e) {
        console.error("Microphone access denied or error:", e);
        alert("Microphone access is required to record voice notes.");
        return false;
    }
}

function stopRecording(onDataCallback) {
    if (!mediaRecorder) return;
    
    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        if (onDataCallback) onDataCallback(audioBlob);
    };
    
    mediaRecorder.stop();
}

async function processAudio(audioBlob) {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    try {
        const transcribeRes = await fetch(API_BASE + '/transcribe', {
            method: 'POST',
            body: formData
        });
        if (!transcribeRes.ok) throw new Error("Transcription failed");
        const transcribeData = await transcribeRes.json();
        
        console.log("Transcribed:", transcribeData.transcript);

        const extractRes = await fetch(API_BASE + '/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: transcribeData.transcript })
        });
        if (!extractRes.ok) throw new Error("Extraction failed");
        const extractData = await extractRes.json();
        
        console.log("Extracted:", extractData);
        return extractData;

    } catch (e) {
        console.error("Audio processing pipeline failed:", e);
        alert("Failed to process audio. Please try again.");
        return null;
    }
}

async function toggleDummyRecording(onSuccessCallback) {
    const btnEl = document.getElementById('recordBtn');
    const iconEl = document.getElementById('recordBtnIcon');
    const textEl = document.getElementById('recordBtnText');
    const statusEl = document.getElementById('recordStatusText');
    const timerEl = document.getElementById('timerDisplay');
    const pulseEl = document.getElementById('pulseRing');
    const processingEl = document.getElementById('processingOverlay');

    if (!isRecording) {
        const started = await startRecording();
        if (!started) return;

        isRecording = true;
        secondsCount = 0;
        
        btnEl.className = "relative z-10 w-28 h-28 rounded-full bg-rose-600 hover:bg-rose-700 text-white shadow-xl flex flex-col items-center justify-center transition-transform active:scale-95 focus:outline-none animate-pulse";
        iconEl.className = "fa-solid fa-stop text-3xl mb-1";
        textEl.innerText = "Stop Recording";
        statusEl.innerText = "Recording in progress... tap stop when finished.";
        if(pulseEl) pulseEl.classList.add('recording-pulse');

        recordingInterval = setInterval(() => {
            secondsCount++;
            let m = Math.floor(secondsCount / 60);
            let s = secondsCount % 60;
            if(timerEl) timerEl.innerText = `${m}:${s < 10 ? '0' : ''}${s}`;
        }, 1000);

    } else {
        isRecording = false;
        clearInterval(recordingInterval);

        if(pulseEl) pulseEl.classList.remove('recording-pulse');
        if(processingEl) processingEl.classList.remove('hidden');

        stopRecording(async (audioBlob) => {
            const extractedDraft = await processAudio(audioBlob);
            
            if(processingEl) processingEl.classList.add('hidden');
            
            btnEl.className = "relative z-10 w-28 h-28 rounded-full bg-primary-600 hover:bg-primary-700 text-white shadow-xl flex flex-col items-center justify-center transition-transform active:scale-95 focus:outline-none";
            iconEl.className = "fa-solid fa-microphone text-3xl mb-1";
            textEl.innerText = "Tap to Record";
            if(timerEl) timerEl.innerText = "0:00";
            if(statusEl) statusEl.innerText = "Ready to record";

            if (extractedDraft) {
                saveCurrentDraft(extractedDraft);
                if(onSuccessCallback) onSuccessCallback(extractedDraft);
            }
        });
    }
}
"""

content = re.sub(r'// Simulated Recording State Variables.*', replacement, content, flags=re.DOTALL)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
