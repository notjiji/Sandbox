from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.rbac import build_roles_list_response

router = APIRouter()


@router.get("/roles")
def list_roles() -> JSONResponse:
    response = build_roles_list_response()
    return JSONResponse(status_code=200, content=response.model_dump(mode="json"))
