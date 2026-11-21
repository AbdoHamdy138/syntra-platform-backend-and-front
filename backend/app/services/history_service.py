from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
import json
from app.database import query_all, query_one, execute
from app.models.api_models import (
    HistoryListResponse,
    HistoryItemPayload,
    DeleteThreadResponse,
    AuthUser,
    HistoryThreadDetailResponse,
    HistoryTurnPayload,
    QueryResultItem,
)
from app.middleware import raise_not_found

class HistoryService:
    @staticmethod
    def get_thread_detail(thread_id: str, user: Optional[AuthUser] = None) -> HistoryThreadDetailResponse:
        thread = query_one(
            "SELECT id, investigation_id, question, preview, mode, created_at FROM threads WHERE id = %s",
            (thread_id,)
        )
        if not thread:
            raise_not_found(f"Thread '{thread_id}' not found.")

        raw_turns = query_all(
            """
            SELECT id, thread_id, question, answer, uncertainty, outcome, result_json, created_at
            FROM thread_turns
            WHERE thread_id = %s
            ORDER BY created_at ASC
            """,
            (thread_id,)
        )

        turns_payload: List[HistoryTurnPayload] = []
        for t in raw_turns:
            created_at_dt = t.get("created_at")
            if created_at_dt and hasattr(created_at_dt, "timestamp"):
                ts_ms = int(created_at_dt.timestamp() * 1000)
            else:
                ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            res_raw = t.get("result_json")
            if isinstance(res_raw, str):
                try:
                    res_raw = json.loads(res_raw)
                except Exception:
                    res_raw = []

            # Normalize to list of QueryResultItem
            results_list: List[QueryResultItem] = []
            if isinstance(res_raw, dict):
                # May have format { results: [...], answer: ... }
                dict_results = res_raw.get("results")
                if isinstance(dict_results, list):
                    for item in dict_results:
                        try:
                            results_list.append(QueryResultItem.model_validate(item))
                        except Exception:
                            pass
            elif isinstance(res_raw, list):
                for item in res_raw:
                    try:
                        results_list.append(QueryResultItem.model_validate(item))
                    except Exception:
                        pass

            turns_payload.append(
                HistoryTurnPayload(
                    id=t["id"],
                    thread_id=t["thread_id"],
                    question=t["question"] or "",
                    answer=t.get("answer"),
                    uncertainty=t.get("uncertainty"),
                    outcome=t.get("outcome") or "ok",
                    results=results_list,
                    created_at=ts_ms
                )
            )

        thread_created_dt = thread.get("created_at")
        if thread_created_dt and hasattr(thread_created_dt, "timestamp"):
            thread_ts_ms = int(thread_created_dt.timestamp() * 1000)
        else:
            thread_ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        return HistoryThreadDetailResponse(
            thread_id=thread["id"],
            investigation_id=thread.get("investigation_id") or f"inv_{thread['id'][-6:]}",
            question=thread["question"] or "",
            preview=thread.get("preview"),
            mode=thread.get("mode") or "standard",
            created_at=thread_ts_ms,
            turns=turns_payload
        )

    @staticmethod
    def get_history(user: Optional[AuthUser] = None, limit: int = 50, offset: int = 0) -> HistoryListResponse:
        now_iso = datetime.now(timezone.utc).isoformat()
        
        if user and user.role != "guest":
            threads = query_all(
                """
                SELECT id, investigation_id, question, preview, created_at
                FROM threads
                WHERE user_id = %s OR user_id IS NULL
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user.id, limit, offset)
            )
            count_rec = query_one(
                "SELECT COUNT(*) as total FROM threads WHERE user_id = %s OR user_id IS NULL",
                (user.id,)
            )
        else:
            threads = query_all(
                """
                SELECT id, investigation_id, question, preview, created_at
                FROM threads
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
            count_rec = query_one("SELECT COUNT(*) as total FROM threads")

        total = count_rec["total"] if count_rec else len(threads)

        items: List[HistoryItemPayload] = []
        for th in threads:
            created_at_dt = th["created_at"]
            if created_at_dt and hasattr(created_at_dt, "timestamp"):
                ts_ms = int(created_at_dt.timestamp() * 1000)
            else:
                ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            items.append(
                HistoryItemPayload(
                    thread_id=th["id"],
                    investigation_id=th.get("investigation_id") or f"inv_{th['id'][-6:]}",
                    question=th["question"],
                    created_at=ts_ms,
                    preview=th.get("preview") or th["question"][:80],
                    source="remote"
                )
            )

        return HistoryListResponse(
            items=items,
            total=total,
            generated_at=now_iso
        )

    @staticmethod
    def delete_thread(thread_id: str, user: Optional[AuthUser] = None) -> DeleteThreadResponse:
        thread = query_one("SELECT id FROM threads WHERE id = %s", (thread_id,))
        if not thread:
            raise_not_found(f"Thread '{thread_id}' not found.")

        # Delete turns first
        execute("DELETE FROM thread_turns WHERE thread_id = %s", (thread_id,))
        # Delete thread
        execute("DELETE FROM threads WHERE id = %s", (thread_id,))

        return DeleteThreadResponse(
            success=True,
            deleted_id=thread_id
        )

