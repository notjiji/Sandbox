from fastapi import APIRouter

from app.api.v1 import health
from app.api.v1.auth import router as auth_router
from app.api.v1.members import router as members_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.projects import router as projects_router
from app.api.v1.users import router as users_router

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
router.include_router(members_router, prefix="/organizations", tags=["members"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])