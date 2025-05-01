from fastapi import FastAPI
from app.core.config import setup
from app.api.router import router

app = FastAPI()
setup(app)
app.include_router(router)

@app.get("/")
def root():
    return {"status": "Backend live"}
