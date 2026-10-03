
import os
import glob
import json

frontend_dir = r"c:\Users\anugr\hisaab_org\frontend"

# 1. Create manifest.json
manifest = {
    "name": "Hisaab",
    "short_name": "Hisaab",
    "start_url": "index.html",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#059669",
    "icons": [
        {
            "src": "icon.svg",
            "sizes": "any",
            "type": "image/svg+xml"
        }
    ]
}
with open(os.path.join(frontend_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

# 2. Create icon.svg
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="112" fill="#059669"/>
  <text x="50%" y="53%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="300" fill="white" font-weight="bold">H</text>
</svg>"""
with open(os.path.join(frontend_dir, "icon.svg"), "w") as f:
    f.write(svg_content)

# 3. Add to all HTML files
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))
for filepath in html_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if '<link rel="manifest"' not in content:
        content = content.replace("</head>", "    <link rel=\"manifest\" href=\"manifest.json\">\n</head>")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

print("PWA setup complete!")

