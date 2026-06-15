import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read database URL from environment or default to a local PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/climbcp")

# For SQLite, check_same_thread is required to allow multi-threaded access in FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create database engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    Closes the session automatically after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    """
    1. Enables database extensions (e.g. pgvector if using PostgreSQL).
    2. Creates all tables defined in models.
    3. Seeds default competitive programming topics if empty.
    """
    # 1. Enable pgvector extension (if using PostgreSQL)
    if DATABASE_URL.startswith("postgresql"):
        from sqlalchemy import text
        try:
            with engine.connect() as conn:
                # Enable vector extension for embedding/recommendation tasks
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("pgvector extension checked/enabled successfully.")
        except Exception as e:
            print(f"Warning: Could not enable pgvector extension (might not be PostgreSQL or lacks permission): {e}")

    # 2. Create tables
    from app.database.base import Base
    import app.models  # Ensures all models are loaded in SQLAlchemy registry before creation
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    # 3. Seed default competitive programming topics
    from app.models.topic import Topic

    DEFAULT_TOPICS = [
        "Implementation",
        "Math",
        "Greedy Algorithms",
        "Dynamic Programming",
        "Data Structures",
        "Graphs",
        "Trees",
        "Binary Search",
        "Two Pointers",
        "Sorting",
        "Bitmasking",
        "Number Theory",
        "Combinatorics",
        "Constructive Algorithms",
        "Shortest Paths",
        "String Algorithms",
        "Flows & Matchings",
        "Geometry"
    ]

    db = SessionLocal()
    try:
        existing_count = db.query(Topic).count()
        if existing_count == 0:
            print("Seeding default competitive programming topics...")
            topics = [Topic(name=name) for name in DEFAULT_TOPICS]
            db.add_all(topics)
            db.commit()
            print(f"Successfully seeded {len(DEFAULT_TOPICS)} topics.")
        else:
            print(f"Topics already seeded (found {existing_count} records). Skipping seeding.")
    except Exception as e:
        print(f"Error occurred while seeding topics: {e}")
        db.rollback()
    finally:
        db.close()
