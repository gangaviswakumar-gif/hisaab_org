# test_database.py
from database import init_db, find_patient, create_patient, save_visit, get_all_visits

init_db()
print("Tables created.")

# Try creating a fake patient
create_patient({
    "rch_id": "TEST001", "name": "Test Patient", "husband_name": "Test Husband",
    "age": 25, "address": "Test Address", "mobile": "9999999999",
    "lmp": "2026-01-01", "edd": "2026-10-01", "gravida": 1, "para": 0
})
print("Patient created.")

# Check lookup works
found = find_patient("TEST001")
print("Found patient:", found)

print("All visits:", get_all_visits())