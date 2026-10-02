import re

with open('frontend/confirm.html', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """        async function saveAndRegister() {
            const keys = ['name', 'rch_id', 'husband_name', 'age', 'address', 'mobile', 'lmp', 'edd', 'gravida', 'para', 'visit_date', 'weight_kg', 'bp_systolic', 'bp_diastolic', 'hemoglobin'];
            let missingRequired = false;
            const requiredFields = ['name', 'rch_id', 'age', 'visit_date', 'bp_systolic', 'bp_diastolic', 'weight_kg'];
            
            keys.forEach(k => {
                const el = document.getElementById(`field-${k}`);
                if (el) {
                    let val = el.value !== '' ? (el.type === 'number' || !isNaN(el.value) ? Number(el.value) : el.value) : null;
                    draft[k] = val;
                    if (requiredFields.includes(k) && (val === null || val === '')) {
                        missingRequired = true;
                        el.classList.add('border-rose-500'); // Highlight missing field
                    } else {
                        el.classList.remove('border-rose-500');
                    }
                }
            });

            if (missingRequired) {
                alert("Please fill out all required fields (Name, RCH ID, Age, Visit Date, Weight, and BP).");
                return;
            }

            const symInput = document.getElementById('field-symptoms');
            if(symInput) draft.symptoms = symInput.value.split(',').map(s => s.trim()).filter(Boolean);

            try {
                const result = await apiConfirmVisit(draft);
                localStorage.removeItem(DRAFT_KEY);
                alert("Visit successfully confirmed and saved to official register!");
                window.location.href = "register.html";
            } catch (e) {
                alert("Failed to save to database. Check server logs.");
            }
        }"""

content = re.sub(r'async function saveAndRegister\(\) \{.*window\.location\.href = "register\.html";\s*\}\s*catch[^\}]+\}\s*\}', replacement, content, flags=re.DOTALL)

with open('frontend/confirm.html', 'w', encoding='utf-8') as f:
    f.write(content)
