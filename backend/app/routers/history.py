from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.models.api_models import HistoryListResponse, HistoryThreadDetailResponse, DeleteThreadResponse, AuthUser
from app.services.auth_service import get_optional_user
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["Investigation History"])

@router.get("", response_model=HistoryListResponse)
def get_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> HistoryListResponse:
    return HistoryService.get_history(user=user, limit=limit, offset=offset)

@router.get("/{thread_id}", response_model=HistoryThreadDetailResponse)
def get_history_thread(
    thread_id: str,
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> HistoryThreadDetailResponse:
    return HistoryService.get_thread_detail(thread_id=thread_id, user=user)

@router.delete("/{thread_id}", response_model=DeleteThreadResponse)
def delete_history_thread(
    thread_id: str,
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> DeleteThreadResponse:
    return HistoryService.delete_thread(thread_id=thread_id, user=user)

