// Shared Application Logic & Mock Database for Hisaab
const STORAGE_KEY = "hisaab_visits_db";
const DRAFT_KEY = "hisaab_current_draft";

const defaultVisits = [
    {
        visit_id: "v_001",
        rch_id: "RCH-2026-8841",
        name: "Anitha Kumari",
        husband_name: "Rajesh Kumar",
        age: 26,
        address: "Pattom, Trivandrum",
        mobile: "9447123456",
        lmp: "2025-11-15",
        edd: "2026-08-22",
        gravida: 2,
        para: 1,
        visit_date: new Date().toISOString().split('T')[0],
        weight_kg: 64.5,
        bp_systolic: 148,
        bp_diastolic: 96,
        hemoglobin: 10.2,
        symptoms: ["Severe headache", "Swollen ankles"],
        hrp_flag: true,
        alerts: ["BP 148/96 + severe headache — pre-eclampsia risk", "Hemoglobin 10.2 g/dL — mild anemia"]
    },
    {
        visit_id: "v_002",
        rch_id: "RCH-2026-9023",
        name: "Priya Suresh",
        husband_name: "Suresh Babu",
        age: 24,
        address: "Kovalam, Trivandrum",
        mobile: "9847552211",
        lmp: "2025-12-01",
        edd: "2026-09-08",
        gravida: 1,
        para: 0,
        visit_date: "2026-10-01",
        weight_kg: 58.0,
        bp_systolic: 120,
        bp_diastolic: 80,
        hemoglobin: 11.8,
        symptoms: ["Mild nausea"],
        hrp_flag: false,
        alerts: []
    }
];

function getVisits() {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultVisits));
        return defaultVisits;
    }
    return JSON.parse(data);
}

function saveVisits(visits) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(visits));
}

function getCurrentDraft() {
    const data = localStorage.getItem(DRAFT_KEY);
    return data ? JSON.parse(data) : null;
}

function saveCurrentDraft(draft) {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

// Persistent Recording State Variables
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
                { name: "Divya Das", age: 29, bp_sys: 122, bp_dia: 80, weight: 65.1, hemoglobin: 12.0, symptoms: ["Back pain"] }
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
                hrp_flag: picked.bp_sys >= 140,
                alerts: picked.bp_sys >= 140 ? [`High BP recorded (${picked.bp_sys}/${picked.bp_dia} mmHg)`] : []
            };

            saveCurrentDraft(draft);
            if(onStopCallback) onStopCallback(draft);
        }, 1200);
    }
}