import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "nyxai.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(sessions)")
columns = cursor.fetchall()

print("Sessions table structure:")
print("-" * 80)
for col in columns:
    print(f"  {col[1]:<20} {col[2]:<15} NULL={col[3]} DEFAULT={col[4]}")

conn.close()