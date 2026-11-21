from typing import Optional
from fastapi import APIRouter, Depends, Request
from app.models.api_models import QueryRequestBody, QueryResponseBody, AuthUser
from app.services.auth_service import get_optional_user
from app.services.query_service import QueryService
from app.middleware import get_request_id

router = APIRouter(tags=["Query & Intelligence"])

@router.post("/query", response_model=QueryResponseBody)
def post_query(
    body: QueryRequestBody,
    request: Request,
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> QueryResponseBody:
    req_id = get_request_id(request)
    return QueryService.execute_query(
        query_text=body.query,
        mode=body.mode or "standard",
        user=user,
        request_id=req_id
    )

