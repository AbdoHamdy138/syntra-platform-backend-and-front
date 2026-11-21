from typing import Optional
from fastapi import APIRouter, Depends, Response
from app.models.api_models import ExportRequestBody, ExportResponseBody, AuthUser
from app.services.auth_service import get_optional_user
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["Exports & Reports"])

@router.post("", response_model=ExportResponseBody)
def create_export(
    body: ExportRequestBody,
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> ExportResponseBody:
    return ExportService.create_export(body=body, user=user)

@router.get("/download/{export_id}")
def download_export(export_id: str) -> Response:
    content, file_name, mime_type = ExportService.get_export_file(export_id)
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"'
        }
    )

