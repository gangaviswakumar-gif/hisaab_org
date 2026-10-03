
import sqlite3
conn = sqlite3.connect("backend/hisaab.db")
conn.execute("UPDATE patients SET last_visit_date = '2026-08-01'")
conn.commit()
print("Updated all patient visit dates to 2026-08-01")

