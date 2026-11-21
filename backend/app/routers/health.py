from datetime import datetime, timezone
from fastapi import APIRouter
from app.database import query_one
from app.models.api_models import HealthResponse, HealthDependencies

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    now_iso = datetime.now(timezone.utc).isoformat()
    db_ok = False
    try:
        res = query_one("SELECT 1 as alive")
        db_ok = res is not None and res.get("alive") == 1
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return HealthResponse(
        status=status,
        dependencies=HealthDependencies(
            retrieval=db_ok,
            answer_generation=True,
            lab_orchestration=True
        ),
        retrieval_version="2026.3.1",
        generated_at=now_iso
    )

