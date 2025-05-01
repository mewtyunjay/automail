# backend/app/api/email.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_email():
    return {"msg": "Reply endpoint working"}