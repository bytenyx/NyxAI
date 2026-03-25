import asyncio
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "nyxai.db"


def migrate_sessions_table(cursor):
    cursor.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in cursor.fetchall()]
    
    migrations = [
        ("title", "VARCHAR(200)"),
        ("message_count", "INTEGER DEFAULT 0"),
        ("last_message", "TEXT"),
    ]
    
    for col_name, col_type in migrations:
        if col_name not in columns:
            print(f"Adding '{col_name}' column to sessions table...")
            cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added '{col_name}' column")
        else:
            print(f"✓ sessions.'{col_name}' column already exists")


def migrate_knowledge_table(cursor):
    cursor.execute("PRAGMA table_info(knowledge)")
    columns = [row[1] for row in cursor.fetchall()]
    
    migrations = [
        ("file_url", "VARCHAR(500)"),
        ("file_name", "VARCHAR(200)"),
        ("tags", "JSON"),
        ("category", "VARCHAR(100)"),
        ("reference_count", "INTEGER DEFAULT 0"),
    ]
    
    for col_name, col_type in migrations:
        if col_name not in columns:
            print(f"Adding '{col_name}' column to knowledge table...")
            cursor.execute(f"ALTER TABLE knowledge ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added '{col_name}' column")
        else:
            print(f"✓ knowledge.'{col_name}' column already exists")


def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Migrating sessions table...")
        migrate_sessions_table(cursor)
        
        print("\nMigrating knowledge table...")
        migrate_knowledge_table(cursor)
        
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