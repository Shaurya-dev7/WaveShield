import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# We look for a DATABASE_URL in .env, fallback to our default Docker configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:disaster_admin_123@localhost:5432/disaster_intel")

# Connection pooling ensures the API doesn't crash under high concurrent load
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800 # Recycle connections every 30 mins to prevent stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency generator for FastAPI endpoints to securely inject database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
