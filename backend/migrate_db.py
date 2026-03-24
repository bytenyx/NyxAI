import asyncio
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "nyxai.db"


def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "title" not in columns:
            print("Adding 'title' column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN title VARCHAR(200)")
            print("✓ Added 'title' column")
        else:
            print("✓ 'title' column already exists")
        
        if "message_count" not in columns:
            print("Adding 'message_count' column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN message_count INTEGER DEFAULT 0")
            print("✓ Added 'message_count' column")
        else:
            print("✓ 'message_count' column already exists")
        
        if "last_message" not in columns:
            print("Adding 'last_message' column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN last_message TEXT")
            print("✓ Added 'last_message' column")
        else:
            print("✓ 'last_message' column already exists")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"❌ Database file not found at: {DB_PATH}")
        print("The database will be created automatically when you start the application.")
        exit(1)
    
    print(f"Migrating database at: {DB_PATH}")
    migrate_database()