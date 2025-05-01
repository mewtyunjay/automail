from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with frontend domain in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
