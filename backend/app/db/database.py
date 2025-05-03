# /Users/mrityunjay/Code/2025/automail/backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get Supabase pooler URI from environment variables
# Load Supabase pooler URI from environment variables only (no default for security)
SUPABASE_POOLER_URI = os.getenv("SUPABASE_POOLER_URI")
if not SUPABASE_POOLER_URI:
    raise RuntimeError("SUPABASE_POOLER_URI environment variable must be set. Place it in your .env file or export it before running the app.")

# Use the pooler URI directly
DATABASE_URL = SUPABASE_POOLER_URI

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()