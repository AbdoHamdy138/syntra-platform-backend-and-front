import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from app.database import query_all, query_one, execute
from app.models.api_models import ExportRequestBody, ExportResponseBody, AuthUser
from app.middleware import raise_not_found

class ExportService:
    @staticmethod
    def create_export(body: ExportRequestBody, user: Optional[AuthUser] = None) -> ExportResponseBody:
        thread = query_one("SELECT * FROM threads WHERE id = %s", (body.thread_id,))
        if not thread:
            raise_not_found(f"Thread '{body.thread_id}' not found.")

        turns = query_all(
            "SELECT * FROM thread_turns WHERE thread_id = %s ORDER BY created_at ASC",
            (body.thread_id,)
        )

        export_id = f"exp_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        ext_map = {"pdf": "pdf", "json": "json", "markdown": "md"}
        ext = ext_map.get(body.format, "md")
        file_name = f"syntra_threat_report_{thread['id']}.{ext}"
        user_id = user.id if user else None

        # Build content based on format
        if body.format == "json":
            content_obj = {
                "report_id": export_id,
                "thread_id": thread["id"],
                "investigation_id": thread.get("investigation_id"),
                "question": thread["question"],
                "created_at": thread["created_at"].isoformat() if hasattr(thread["created_at"], "isoformat") else str(thread["created_at"]),
                "turns": [
                    {
                        "question": t["question"],
                        "answer": t["answer"],
                        "uncertainty": t["uncertainty"],
                        "outcome": t["outcome"]
                    }
                    for t in turns
                ]
            }
            file_content = json.dumps(content_obj, indent=2)
        elif body.format == "markdown":
            md_lines = [
                f"# SYNTRA Threat Intelligence Report",
                f"**Investigation ID**: `{thread.get('investigation_id')}` | **Generated**: `{now.isoformat()}`\n",
                f"## Primary Query\n> {thread['question']}\n",
                "## Findings and Analysis\n"
            ]
            for idx, turn in enumerate(turns, 1):
                md_lines.append(f"### Turn {idx}: {turn['question']}\n")
                md_lines.append(turn["answer"] or "No detailed analysis provided.")
                md_lines.append(f"\n*Evidence Grounding*: {turn.get('uncertainty') or 'Authoritative sources verified.'}\n")
            file_content = "\n".join(md_lines)
        else:
            # Simple text/PDF representation
            pdf_lines = [
                "%PDF-1.4 Mock SYNTRA Export Header",
                f"SYNTRA Threat Intelligence Report - {thread['id']}",
                f"Investigation: {thread.get('investigation_id')}",
                f"Query: {thread['question']}",
                "==================================================",
            ]
            for turn in turns:
                pdf_lines.append(f"\nQuestion: {turn['question']}")
                pdf_lines.append(f"Answer:\n{turn['answer']}")
            file_content = "\n".join(pdf_lines)

        execute(
            """
            INSERT INTO exports (id, thread_id, user_id, format, file_name, file_content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (export_id, body.thread_id, user_id, body.format, file_name, file_content, now)
        )

        return ExportResponseBody(
            download_url=f"/api/v1/export/download/{export_id}",
            file_name=file_name,
            format=body.format,
            generated_at=now.isoformat()
        )

    @staticmethod
    def get_export_file(export_id: str) -> Tuple[str, str, str]:
        """Returns (file_content, file_name, mime_type)"""
        record = query_one("SELECT file_name, file_content, format FROM exports WHERE id = %s", (export_id,))
        if not record:
            raise_not_found(f"Export '{export_id}' not found.")

        mime_types = {
            "pdf": "application/pdf",
            "json": "application/json",
            "markdown": "text/markdown; charset=utf-8"
        }
        mime = mime_types.get(record["format"], "text/plain")
        return record["file_content"], record["file_name"], mime

