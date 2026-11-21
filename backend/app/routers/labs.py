from typing import Optional
from fastapi import APIRouter, Depends
from app.models.api_models import (
    LabCatalogResponse,
    LaunchLabRequestBody,
    LaunchLabResponseBody,
    LabSessionStatusResponse,
    TerminateLabSessionResponse,
    AuthUser
)
from app.services.auth_service import get_optional_user
from app.services.lab_service import LabService

router = APIRouter(prefix="/labs", tags=["Interactive Labs"])

@router.get("", response_model=LabCatalogResponse)
def get_lab_catalog() -> LabCatalogResponse:
    return LabService.get_catalog()

@router.post("/{lab_id}/launch", response_model=LaunchLabResponseBody)
def launch_lab(
    lab_id: str,
    body: LaunchLabRequestBody,
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> LaunchLabResponseBody:
    return LabService.launch_session(lab_id=lab_id, body=body, user=user)

@router.get("/sessions/{session_id}", response_model=LabSessionStatusResponse)
def get_session_status(session_id: str) -> LabSessionStatusResponse:
    return LabService.get_session_status(session_id=session_id)

@router.post("/sessions/{session_id}/terminate", response_model=TerminateLabSessionResponse)
def terminate_session(session_id: str) -> TerminateLabSessionResponse:
    return LabService.terminate_session(session_id=session_id)

