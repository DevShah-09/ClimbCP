import sys
import os
from sqlalchemy import text

# Add the parent directory to the path so python can find app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import engine, create_db_and_tables

# List of tables to drop with CASCADE
TABLES = [
    "problem_topic",
    "problem_attempts",
    "contest_participations",
    "cp_profiles",
    "platform_accounts",
    "user_skills",
    "recommendations",
    "ai_reports",
    "problem_embeddings",
    "problem_clusters",
    "user_embeddings",
    "users",
    "contests",
    "problems",
    "topics"
]

def reset_db():
    print("Dropping all existing database tables with CASCADE...")
    try:
        with engine.connect() as conn:
            for table in TABLES:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    print(f"Dropped table {table} (if it existed).")
                except Exception as e:
                    print(f"Error dropping table {table}: {e}")
            conn.commit()
        print("Successfully dropped all database tables.")
    except Exception as e:
        print(f"Error during drop phase: {e}")
    
    print("Recreating database tables and seeding topics...")
    try:
        create_db_and_tables()
        print("Database tables recreated and topics seeded successfully!")
    except Exception as e:
        print(f"Failed to recreate database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_db()
