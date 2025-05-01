from fastapi import APIRouter
from app.api import auth, email, reply

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(email.router, prefix="/email", tags=["Email"])
router.include_router(reply.router, prefix="/reply", tags=["Reply"])
# router.include_router(memory.router, prefix="/memory", tags=["Memory"])
