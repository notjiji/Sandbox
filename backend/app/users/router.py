from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.responses import success_response
from app.users.models import User
from app.users.schemas import UpdateUserProfileRequest
from app.users.services import user_service

router = APIRouter()


@router.get("/me")
def get_me(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    profile = user_service.get_user_profile(db, current_user)
    return success_response(data=profile.model_dump(), request=request)


@router.patch("/me")
def patch_me(
    request: Request,
    body: UpdateUserProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    profile = user_service.update_profile(db, current_user, body=body)
    return success_response(data=profile.model_dump(), request=request)
