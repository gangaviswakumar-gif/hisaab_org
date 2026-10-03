import re

with open('frontend/confirm.html', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """        let draft = getCurrentDraft();
        if (!draft) {
            draft = {}; // Empty fallback if opened directly without a voice note
        }
        
        // Always force visit_date to today, ignoring any voice-extracted date
        draft.visit_date = new Date().toISOString().split('T')[0];

        // Populate form"""

# Regex to find the draft block up to the populate comment
content = re.sub(
    r'let draft = getCurrentDraft\(\);.*?// Populate form', 
    replacement, 
    content, 
    flags=re.DOTALL
)

with open('frontend/confirm.html', 'w', encoding='utf-8') as f:
    f.write(content)
