from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from typing import Optional

def setup(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with frontend domain in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class Settings(BaseSettings):
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    secret_key: Optional[str] = None
    database_url: Optional[str] = None
    mongo_uri: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"
    
settings = Settings()