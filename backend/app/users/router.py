from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.users.models import User
from app.users.schemas import UpdateUserProfileRequest
from app.users.services import user_service

router = APIRouter()


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    profile = user_service.get_user_profile(db, current_user)
    return JSONResponse(status_code=200, content=profile.model_dump())


@router.patch("/me")
def patch_me(
    body: UpdateUserProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    profile = user_service.update_profile(db, current_user, body=body)
    return JSONResponse(status_code=200, content=profile.model_dump())
