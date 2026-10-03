
import sqlite3
import os
from database import get_db, init_db

def migrate_db():
    init_db()
    with get_db() as conn:
        cursor = conn.execute("PRAGMA table_info(patients)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        if "home_lat" not in existing_cols:
            conn.execute("ALTER TABLE patients ADD COLUMN home_lat REAL")
            print("Added home_lat")
        if "home_lon" not in existing_cols:
            conn.execute("ALTER TABLE patients ADD COLUMN home_lon REAL")
            print("Added home_lon")
        if "last_visit_date" not in existing_cols:
            conn.execute("ALTER TABLE patients ADD COLUMN last_visit_date TEXT")
            print("Added last_visit_date")
        
        # Seed data
        updates = [
            ("RCH-7B65B57B", "Vazhuthacaud, Trivandrum", 8.5069, 76.9581, "2026-10-02"),
            ("RCH-00A40926", "Pattom, Trivandrum", 8.5241, 76.9366, "2026-10-02"),
            ("RCH-2373F392", "Kesavadasapuram, Trivandrum", 8.5122, 76.9418, "2026-10-02"),
            ("RCH-16DE20E1", "Kazhakkoottam, Trivandrum", 8.5574, 76.8773, "2026-10-02"),
            ("RCH-2026-3321", "Kazhakkoottam, Trivandrum", 8.5574, 76.8773, "2026-10-02"),
            ("1234", "Nemom, Trivandrum", 8.4641, 76.9547, "2026-10-02"),
            ("123", "Ulloor, Trivandrum", 8.5413, 76.9116, "2026-10-02")
        ]
        
        for rch_id, addr, lat, lon, lvd in updates:
            conn.execute("""
                UPDATE patients 
                SET address = ?, home_lat = ?, home_lon = ?, last_visit_date = ? 
                WHERE rch_id = ?
            """, (addr, lat, lon, lvd, rch_id))
        
        conn.commit()
        print("Database migrated and seeded successfully.")

if __name__ == "__main__":
    migrate_db()

