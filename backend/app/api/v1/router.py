from fastapi import APIRouter

from app.api.v1 import assets, auth, health, organizations

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
router.include_router(assets.router, prefix="/assets", tags=["assets"])
