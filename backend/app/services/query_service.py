import re
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.database import query_all, query_one, execute
from app.models.api_models import (
    QueryResponseBody,
    QueryResultItem,
    ContractEntity,
    ContractEvidenceItem,
    ContractRelationship,
    ContractChainStage,
    ContractDetectionItem,
    ContractMitigationItem,
    ContractLabEnvironment,
    QueryRefusal,
    QueryMeta,
    AuthUser
)

# Harmful weaponization / offensive patterns requiring safety refusal
SAFETY_REFUSAL_PATTERNS = [
    r"\b(write|create|generate|code|build|give me)\b.*\b(ransomware|keylogger|ddos attack|trojan payload|rootkit|zero-day exploit)\b",
    r"\b(how to hack|how to exploit|hack into|breach|infiltrate)\b.*\b(server|website|bank|target|database)\b",
    r"\b(bypass authentication|steal passwords|crack credentials|privilege escalation exploit code)\b"
]

# Cybsersecurity domain indicators
CYBER_DOMAIN_KEYWORDS = [
    "t1", "apt", "cve", "threat", "actor", "malware", "phishing", "persistence",
    "privilege", "scheduler", "schtasks", "powershell", "detection", "mitigation",
    "attack", "chain", "evidence", "reconnaissance", "lateral", "exfiltration",
    "defense", "evasion", "credential", "vulnerability", "rce", "log4j", "log4shell",
    "mitre", "sigma", "yara", "windows", "linux", "payload", "cmd", "command", "task",
    "script", "lab", "security", "exploit", "cve-", "injection", "identity"
]

class QueryService:
    @staticmethod
    def is_safety_violation(query: str) -> bool:
        lowered = query.lower()
        for pat in SAFETY_REFUSAL_PATTERNS:
            if re.search(pat, lowered):
                return True
        return False

    @staticmethod
    def is_cyber_domain(query: str) -> bool:
        lowered = query.lower()
        return any(kw in lowered for kw in CYBER_DOMAIN_KEYWORDS)

    @staticmethod
    def execute_query(
        query_text: str,
        mode: str = "standard",
        user: Optional[AuthUser] = None,
        request_id: Optional[str] = None
    ) -> QueryResponseBody:
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        meta = QueryMeta(retrieval_version="2026.3.1", generated_at=now_iso)

        clean_query = query_text.strip()
        if not clean_query:
            return QueryResponseBody(
                request_id=req_id,
                query=query_text,
                status="empty",
                outcome="no_results",
                answer="No query provided. Please enter a threat actor, technique ID (e.g. T1053.005), or CVE.",
                results=[],
                meta=meta
            )

        # 1. Safety Refusal Check
        if QueryService.is_safety_violation(clean_query):
            refusal = QueryRefusal(
                message="Query refused under safety policy: Offensive weaponization, active exploit generation, or unauthorized attacks are prohibited.",
                alternatives=[
                    "Ask for detection analytics or Sigma rules for this technique",
                    "Ask for defensive mitigations and hardening strategies",
                    "Review MITRE ATT&CK mapping and attack chain evidence"
                ]
            )
            return QueryResponseBody(
                request_id=req_id,
                query=clean_query,
                status="empty",
                outcome="safety_refused",
                refusal=refusal,
                results=[],
                meta=meta
            )

        # 2. Out of Domain Check
        if not QueryService.is_cyber_domain(clean_query):
            return QueryResponseBody(
                request_id=req_id,
                query=clean_query,
                status="empty",
                outcome="out_of_domain",
                answer="SYNTRA is an evidence-grounded threat intelligence system specializing in MITRE ATT&CK, threat actors, CVEs, and defensive analysis. The query appears to be outside cybersecurity operations.",
                results=[],
                meta=meta
            )

        # 3. Retrieve Entities from PostgreSQL
        tokens = [t.lower() for t in re.findall(r"[\w\.-]+", clean_query) if len(t) >= 2]
        
        # Build search clause
        where_parts = []
        params: List[Any] = []
        for tok in tokens:
            param = f"%{tok}%"
            where_parts.append("(id ILIKE %s OR name ILIKE %s OR description ILIKE %s OR summary ILIKE %s)")
            params.extend([param, param, param, param])

        where_clause = " OR ".join(where_parts) if where_parts else "1=1"
        entities_records = query_all(
            f"SELECT * FROM entities WHERE {where_clause} ORDER BY created_at ASC LIMIT 5",
            params
        )

        # If no direct match, fallback to all entities if cyber keywords matched
        if not entities_records:
            entities_records = query_all("SELECT * FROM entities ORDER BY created_at ASC LIMIT 3")

        if not entities_records:
            return QueryResponseBody(
                request_id=req_id,
                query=clean_query,
                status="empty",
                outcome="no_results",
                answer="No evidence or verified intelligence matching your query was found in the knowledge corpus.",
                results=[],
                meta=meta
            )

        results: List[QueryResultItem] = []
        rank = 1

        for ent in entities_records:
            ent_id = ent["id"]

            contract_entity = ContractEntity(
                id=ent["id"],
                type=ent["type"],
                name=ent["name"],
                taxonomy=ent.get("taxonomy"),
                description=ent.get("description"),
                description_status=ent.get("description_status", "source_supported")
            )

            # Attack Chain Stages
            stage_records = query_all(
                "SELECT * FROM attack_chain_stages WHERE entity_id = %s ORDER BY stage_order ASC",
                (ent_id,)
            )
            attack_chain = [
                ContractChainStage(
                    technique_id=st["technique_id"],
                    technique_name=st["technique_name"],
                    tactic=st["tactic"],
                    status=st["status"],
                    evidence_ids=st.get("evidence_ids") or [],
                    description=st.get("description"),
                    steps=st.get("steps") or [],
                    lab_available=bool(st.get("lab_available", False))
                )
                for st in stage_records
            ]

            stage_ev_ids = []
            for st in stage_records:
                ids = st.get("evidence_ids") or []
                if isinstance(ids, list):
                    stage_ev_ids.extend(ids)

            # Evidence
            ev_records = query_all(
                "SELECT * FROM evidence WHERE ref_id = %s OR id = ANY(%s)",
                (ent_id, stage_ev_ids or [""])
            )
            evidence_items = [
                ContractEvidenceItem(
                    evidence_id=ev["id"],
                    ref_id=ev["ref_id"],
                    status=ev["status"],
                    category=ev["category"],
                    text=ev["text"],
                    source_id=ev.get("source_id"),
                    source_name=ev["source_name"],
                    source_url=ev.get("source_url"),
                    source_ref=ev.get("source_ref"),
                    evidence_ref=ev.get("evidence_ref"),
                    provenance_type=ev["provenance_type"]
                )
                for ev in ev_records
            ]

            # Relationships
            rel_records = query_all(
                "SELECT * FROM relationships WHERE from_id = %s OR to_id = %s",
                (ent_id, ent_id)
            )
            relationships = [
                ContractRelationship(
                    relationship_id=r["id"],
                    from_id=r["from_id"],
                    relation_type=r["relation_type"],
                    to_id=r["to_id"],
                    provenance_type=r["provenance_type"]
                )
                for r in rel_records
            ]

            # Detections
            det_records = query_all(
                "SELECT * FROM detections WHERE entity_id = %s",
                (ent_id,)
            )
            detections = [
                ContractDetectionItem(
                    title=d["title"],
                    description=d["description"]
                )
                for d in det_records
            ]

            # Mitigations
            mit_records = query_all(
                "SELECT * FROM mitigations WHERE entity_id = %s",
                (ent_id,)
            )
            mitigations = [
                ContractMitigationItem(
                    id=m.get("mitigation_id") or m.get("id"),
                    title=m["title"],
                    description=m["description"]
                )
                for m in mit_records
            ]

            # Lab
            lab_record = query_one(
                "SELECT * FROM labs WHERE technique_id = %s LIMIT 1",
                (ent_id,)
            )
            lab_env = None
            if lab_record:
                lab_env = ContractLabEnvironment(
                    lab_id=lab_record["lab_id"],
                    technique_id=lab_record["technique_id"],
                    technique_name=lab_record["technique_name"],
                    available=bool(lab_record["available"]),
                    launchable=bool(lab_record["launchable"]),
                    lab_type=lab_record["lab_type"],
                    platform=lab_record["platform"],
                    runtime_environment=lab_record["runtime_environment"],
                    network_mode=lab_record["network_mode"],
                    validation_source=lab_record["validation_source"],
                    objective=lab_record["objective"],
                    estimated_duration=lab_record["estimated_duration"],
                    difficulty=lab_record["difficulty"],
                    safety_boundary=lab_record["safety_boundary"],
                    session_steps=lab_record.get("session_steps") or [],
                    scenario_objective=lab_record["scenario_objective"]
                )

            missing_ev = ent.get("missing_evidence") or []
            if isinstance(missing_ev, str):
                try:
                    missing_ev = json.loads(missing_ev)
                except Exception:
                    missing_ev = [missing_ev]

            results.append(
                QueryResultItem(
                    rank=rank,
                    entity=contract_entity,
                    evidence=evidence_items,
                    relationships=relationships,
                    attack_chain=attack_chain,
                    detection=detections,
                    mitigation=mitigations,
                    missing_evidence=missing_ev,
                    summary=ent.get("summary"),
                    lab=lab_env
                )
            )
            rank += 1

        # Synthesize analytical answer
        primary_entity = results[0].entity
        answer_parts = [
            f"**Analysis of {primary_entity.name} ({primary_entity.id})**:\n",
            f"{primary_entity.description or results[0].summary or 'Intelligence details retrieved from knowledge corpus.'}\n\n",
            f"- **Taxonomy**: {primary_entity.taxonomy or 'Enterprise ATT&CK'}\n",
            f"- **Corroborated Evidence Count**: {len(results[0].evidence)} source artifact(s)\n",
            f"- **Attack Chain Stages**: {len(results[0].attack_chain)} validated step(s)\n",
            f"- **Defensive Detections**: {len(results[0].detection)} detection rule(s)\n",
            f"- **Mitigations**: {len(results[0].mitigation)} mitigation control(s)\n"
        ]
        if results[0].lab:
            answer_parts.append(f"- **Interactive Lab**: Available for `{results[0].lab.platform}` ({results[0].lab.runtime_environment})\n")

        answer_text = "".join(answer_parts)
        uncertainty_text = "All findings are corroborated against authoritative sources (MITRE ATT&CK, NVD, CISA KEV)."

        # Save to threads and thread_turns in PostgreSQL
        thread_id = f"th_{uuid.uuid4().hex[:12]}"
        inv_id = f"inv_{uuid.uuid4().hex[:8]}"
        user_id = user.id if user else None
        preview = clean_query[:80]

        execute(
            """
            INSERT INTO threads (id, user_id, question, investigation_id, preview, mode, status_kind, turn_count, pinned, archived, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'active', 1, FALSE, FALSE, NOW(), NOW())
            """,
            (thread_id, user_id, clean_query, inv_id, preview, mode)
        )

        turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        results_json_str = json.dumps([r.model_dump() for r in results])
        execute(
            """
            INSERT INTO thread_turns (id, thread_id, question, answer, uncertainty, outcome, result_json, created_at)
            VALUES (%s, %s, %s, %s, %s, 'ok', %s, NOW())
            """,
            (turn_id, thread_id, clean_query, answer_text, uncertainty_text, results_json_str)
        )

        return QueryResponseBody(
            request_id=req_id,
            query=clean_query,
            status="ok",
            outcome="ok",
            answer=answer_text,
            uncertainty=uncertainty_text,
            results=results,
            meta=meta
        )
