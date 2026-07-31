from fastapi import APIRouter

from app.assets.router import router as assets_router
from app.auth.router import router as auth_router
from app.core.health import router as health_router
from app.members.router import router as members_router
from app.organizations.router import router as organizations_router
from app.projects.router import router as projects_router
from app.users.router import router as users_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
router.include_router(members_router, prefix="/organizations", tags=["members"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
