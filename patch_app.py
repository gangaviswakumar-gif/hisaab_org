import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
// Simulated Recording State Variables
let isRecording = false;
let recordingInterval = null;
let secondsCount = 0;

function toggleDummyRecording(onStopCallback) {
    if (!isRecording) {
        // Start recording
        isRecording = true;
        secondsCount = 0;
        
        const timerEl = document.getElementById('timerDisplay');
        const statusEl = document.getElementById('recordStatusText');
        const pulseEl = document.getElementById('pulseRing');
        const btnEl = document.getElementById('recordBtn');
        const iconEl = document.getElementById('recordBtnIcon');
        const textEl = document.getElementById('recordBtnText');

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
        // Stop recording explicitly on user click
        isRecording = false;
        clearInterval(recordingInterval);

        const pulseEl = document.getElementById('pulseRing');
        const processingEl = document.getElementById('processingOverlay');
        const btnEl = document.getElementById('recordBtn');
        const iconEl = document.getElementById('recordBtnIcon');
        const textEl = document.getElementById('recordBtnText');
        const statusEl = document.getElementById('recordStatusText');
        const timerEl = document.getElementById('timerDisplay');

        if(pulseEl) pulseEl.classList.remove('recording-pulse');
        if(processingEl) processingEl.classList.remove('hidden');

        setTimeout(() => {
            if(processingEl) processingEl.classList.add('hidden');
            btnEl.className = "relative z-10 w-28 h-28 rounded-full bg-primary-600 hover:bg-primary-700 text-white shadow-xl flex flex-col items-center justify-center transition-transform active:scale-95 focus:outline-none";
            iconEl.className = "fa-solid fa-microphone text-3xl mb-1";
            textEl.innerText = "Tap to Record";
            if(timerEl) timerEl.innerText = "0:00";
            if(statusEl) statusEl.innerText = "Ready to record";

            // Generate sample extracted schema
            const sampleNames = [
                { name: "Riya Sharma", age: 27, bp_sys: 138, bp_dia: 88, weight: 62.0, hemoglobin: 11.0, symptoms: ["Fatigue", "Mild nausea"] },
                { name: "Fathima Beevi", age: 25, bp_sys: 142, bp_dia: 92, weight: 59.4, hemoglobin: 10.5, symptoms: ["Severe headache", "Dizziness"] },
                { name: "Divya Das", age: 29, bp_sys: 85, bp_dia: 55, weight: 65.1, hemoglobin: 12.0, symptoms: ["Back pain"] }
            ];
            const picked = sampleNames[Math.floor(Math.random() * sampleNames.length)];

            const draft = {
                visit_id: "v_" + Math.floor(Math.random() * 90000 + 10000),
                rch_id: "RCH-2026-" + Math.floor(Math.random() * 9000 + 1000),
                name: picked.name,
                husband_name: "Anoop Kumar",
                age: picked.age,
                address: "Trivandrum Rural",
                mobile: "9847112233",
                lmp: "2025-11-10",
                edd: "2026-08-17",
                gravida: 1,
                para: 0,
                visit_date: new Date().toISOString().split('T')[0],
                weight_kg: picked.weight,
                bp_systolic: picked.bp_sys,
                bp_diastolic: picked.bp_dia,
                hemoglobin: picked.hemoglobin,
                symptoms: picked.symptoms,
                hrp_flag: picked.bp_sys >= 140 || picked.bp_sys <= 90,
                alerts: picked.bp_sys >= 140 ? [`High BP recorded (${picked.bp_sys}/${picked.bp_dia} mmHg)`] : (picked.bp_sys <= 90 ? [`Low BP recorded (${picked.bp_sys}/${picked.bp_dia} mmHg)`] : [])
            };

            saveCurrentDraft(draft);
            if(onStopCallback) onStopCallback(draft);
        }, 1200);
    }
}
"""

content = re.sub(r'// MediaRecorder setup for index\.html.*', replacement, content, flags=re.DOTALL)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
