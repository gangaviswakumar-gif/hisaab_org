import re

with open('frontend/claim.html', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """<script>
        (async function() {
            const visits = await apiGetVisits();
            document.getElementById('claimTotalVisits').innerText = visits.length;
        })();

        async function downloadClaimPDF() {
            const success = await apiGenerateClaim();
            if (!success) alert('Failed to generate PDF. Check server logs.');
        }
    </script>"""

content = re.sub(r'<script>\s*const visits = getVisits\(\);.*?</script>', replacement, content, flags=re.DOTALL)

with open('frontend/claim.html', 'w', encoding='utf-8') as f:
    f.write(content)
