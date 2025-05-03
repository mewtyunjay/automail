# /Users/mrityunjay/Code/2025/automail/backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("SUPABASE_POOLER_URI")
if not DATABASE_URL:
    raise RuntimeError("SUPABASE_POOLER_URI environment variable must be set. Place it in your .env file or export it before running the app.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()