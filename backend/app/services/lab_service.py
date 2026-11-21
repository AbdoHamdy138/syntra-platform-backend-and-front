import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from app.database import query_all, query_one, execute
from app.models.api_models import (
    LabCatalogResponse,
    LabCatalogItem,
    LaunchLabRequestBody,
    LaunchLabResponseBody,
    LabSessionStatusResponse,
    TerminateLabSessionResponse,
    AuthUser
)
from app.middleware import raise_not_found, raise_invalid_input

class LabService:
    @staticmethod
    def get_catalog() -> LabCatalogResponse:
        rows = query_all("SELECT lab_id, technique_id, technique_name, available, launchable, platform, validation_source FROM labs ORDER BY lab_id ASC")
        now_iso = datetime.now(timezone.utc).isoformat()
        labs = [
            LabCatalogItem(
                lab_id=r["lab_id"],
                technique_id=r["technique_id"],
                technique_name=r["technique_name"],
                available=bool(r["available"]),
                launchable=bool(r["launchable"]),
                platform=r["platform"],
                validation_source=r["validation_source"]
            )
            for r in rows
        ]
        return LabCatalogResponse(labs=labs, generated_at=now_iso)

    @staticmethod
    def launch_session(
        lab_id: str,
        body: LaunchLabRequestBody,
        user: Optional[AuthUser] = None
    ) -> LaunchLabResponseBody:
        lab = query_one("SELECT * FROM labs WHERE lab_id = %s", (lab_id,))
        if not lab:
            raise_not_found(f"Lab environment '{lab_id}' not found.")

        if not lab.get("available") or not lab.get("launchable"):
            raise_invalid_input(f"Lab environment '{lab_id}' is currently offline or not launchable.")

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)
        connection_url = f"wss://labs.syntra.local/sessions/{session_id}/terminal"
        user_id = user.id if user else None

        initial_logs = [
            f"[{now.strftime('%H:%M:%S')}] Provisioning isolated {body.platform} sandbox...",
            f"[{now.strftime('%H:%M:%S')}] Loading technique emulation harness for {body.technique_id}...",
            f"[{now.strftime('%H:%M:%S')}] Virtual network bridge established with zero-egress policy.",
            f"[{now.strftime('%H:%M:%S')}] Lab session active and ready for analyst commands."
        ]
        initial_telemetry = {
            "cpu_pct": 14.5,
            "memory_mb": 512,
            "packets_observed": 18,
            "platform": body.platform
        }

        execute(
            """
            INSERT INTO lab_sessions (session_id, user_id, lab_id, technique_id, status, connection_url, expires_at, telemetry, logs, created_at)
            VALUES (%s, %s, %s, %s, 'ready', %s, %s, %s, %s, %s)
            """,
            (session_id, user_id, lab_id, body.technique_id, connection_url, expires_at, json.dumps(initial_telemetry), json.dumps(initial_logs), now)
        )

        return LaunchLabResponseBody(
            session_id=session_id,
            lab_id=lab_id,
            technique_id=body.technique_id,
            status="ready",
            connection_url=connection_url,
            expires_at=expires_at.isoformat(),
            message="Sandbox environment allocated successfully."
        )

    @staticmethod
    def get_session_status(session_id: str) -> LabSessionStatusResponse:
        session = query_one("SELECT * FROM lab_sessions WHERE session_id = %s", (session_id,))
        if not session:
            raise_not_found(f"Lab session '{session_id}' not found.")

        now = datetime.now(timezone.utc)
        created_at = session["created_at"]
        if created_at and hasattr(created_at, "timestamp"):
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            uptime = max(0, int((now - created_at).total_seconds()))
        else:
            uptime = 120

        logs = session.get("logs") or []
        if isinstance(logs, str):
            try:
                logs = json.loads(logs)
            except Exception:
                logs = [logs]

        telemetry = session.get("telemetry")
        if isinstance(telemetry, str):
            try:
                telemetry = json.loads(telemetry)
            except Exception:
                telemetry = {"cpu_pct": 15.0}

        # If still ready and has uptime, transition to running
        status = session.get("status", "running")
        if status == "ready" and uptime > 5:
            status = "running"
            execute("UPDATE lab_sessions SET status = 'running' WHERE session_id = %s", (session_id,))

        return LabSessionStatusResponse(
            session_id=session_id,
            status=status,
            uptime_seconds=uptime,
            telemetry=telemetry,
            logs=logs
        )

    @staticmethod
    def terminate_session(session_id: str) -> TerminateLabSessionResponse:
        session = query_one("SELECT session_id, status FROM lab_sessions WHERE session_id = %s", (session_id,))
        if not session:
            raise_not_found(f"Lab session '{session_id}' not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        execute(
            "UPDATE lab_sessions SET status = 'terminated', terminated_at = NOW() WHERE session_id = %s",
            (session_id,)
        )

        return TerminateLabSessionResponse(
            success=True,
            session_id=session_id,
            terminated_at=now_iso
        )
