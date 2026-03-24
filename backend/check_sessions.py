import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "nyxai.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, title, status FROM sessions ORDER BY created_at DESC LIMIT 5")
sessions = cursor.fetchall()

print("Recent sessions:")
print("-" * 80)
for session in sessions:
    print(f"  ID: {session[0][:8]}... | Title: {session[1]} | Status: {session[2]}")

conn.close()