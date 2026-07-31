from fastapi import APIRouter

from app.api.v1 import auth, health, organizations, projects, users

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
