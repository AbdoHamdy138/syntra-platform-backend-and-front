from datetime import datetime, timezone
from fastapi import APIRouter, Request
from app.database import query_one, query_all
from app.models.api_models import (
    EntityDetailResponse,
    ContractEntity,
    EntitySourceItem,
    EntityProvenanceItem,
    ContractRelationship
)
from app.middleware import get_request_id, raise_not_found

router = APIRouter(prefix="/entities", tags=["Entities"])

@router.get("/{entity_id}", response_model=EntityDetailResponse)
def get_entity_detail(entity_id: str, request: Request) -> EntityDetailResponse:
    req_id = get_request_id(request)
    now_iso = datetime.now(timezone.utc).isoformat()

    ent = query_one("SELECT * FROM entities WHERE id = %s", (entity_id,))
    if not ent:
        raise_not_found(f"Entity '{entity_id}' not found in threat intelligence knowledge corpus.")

    contract_entity = ContractEntity(
        id=ent["id"],
        type=ent["type"],
        name=ent["name"],
        taxonomy=ent.get("taxonomy"),
        description=ent.get("description"),
        description_status=ent.get("description_status", "source_supported")
    )

    # Fetch sources
    src_rows = query_all(
        """
        SELECT s.id as source_id, s.name, s.url, s.kind
        FROM sources s
        JOIN entity_sources es ON s.id = es.source_id
        WHERE es.entity_id = %s
        """,
        (entity_id,)
    )
    sources = [
        EntitySourceItem(
            source_id=s["source_id"],
            name=s["name"],
            url=s.get("url"),
            kind=s["kind"]
        )
        for s in src_rows
    ]

    # Fetch provenance
    prov_rows = query_all(
        """
        SELECT id as provenance_id, provenance_type, source_name, source_ref, source_url, version_or_date
        FROM provenance
        WHERE entity_id = %s
        """,
        (entity_id,)
    )
    provenance = [
        EntityProvenanceItem(
            provenance_id=p["provenance_id"],
            provenance_type=p["provenance_type"],
            source_name=p["source_name"],
            source_ref=p.get("source_ref"),
            source_url=p.get("source_url"),
            version_or_date=p.get("version_or_date")
        )
        for p in prov_rows
    ]

    # Fetch relationships
    rel_rows = query_all(
        """
        SELECT id as relationship_id, from_id, relation_type, to_id, provenance_type
        FROM relationships
        WHERE from_id = %s OR to_id = %s
        """,
        (entity_id, entity_id)
    )
    relationships = [
        ContractRelationship(
            relationship_id=r["relationship_id"],
            from_id=r["from_id"],
            relation_type=r["relation_type"],
            to_id=r["to_id"],
            provenance_type=r["provenance_type"]
        )
        for r in rel_rows
    ]

    return EntityDetailResponse(
        request_id=req_id,
        entity=contract_entity,
        sources=sources,
        provenance=provenance,
        relationships=relationships,
        generated_at=now_iso
    )

