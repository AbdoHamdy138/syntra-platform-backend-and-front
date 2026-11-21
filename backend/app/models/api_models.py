from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

# --- Error Model ---
ApiErrorCode = Literal[
    "invalid_input",
    "unauthorized",
    "forbidden",
    "not_found",
    "rate_limited",
    "dependency_unavailable",
    "internal_error",
]

class ApiErrorResponse(BaseModel):
    error: bool = True
    code: ApiErrorCode
    message: str
    request_id: Optional[str] = None
    generated_at: str

# --- Auth Models ---
class AuthUser(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    role: Literal["analyst", "admin", "guest"] = "analyst"
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    is_verified: Optional[bool] = False

class SignUpRequestBody(BaseModel):
    email: str
    phone: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    otp_channel: Optional[Literal["email", "sms"]] = "email"

class SignUpResponseBody(BaseModel):
    status: Literal["pending_verification", "verified"] = "pending_verification"
    message: str
    email: str
    phone: Optional[str] = None
    otp_channel: Literal["email", "sms"] = "email"
    expires_in_seconds: int
    demo_code: Optional[str] = None

class VerifyOtpRequestBody(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    code: str
    flow: Optional[Literal["signup", "login", "reset"]] = "signup"

class VerifyOtpResponseBody(BaseModel):
    status: Literal["verified"] = "verified"
    message: str
    token: str
    refresh_token: Optional[str] = None
    user: AuthUser
    expires_in_seconds: int

class ResendOtpRequestBody(BaseModel):
    email: str
    phone: Optional[str] = None
    otp_channel: Optional[Literal["email", "sms"]] = "email"
    flow: Optional[Literal["signup", "login", "reset"]] = "signup"

class ResendOtpResponseBody(BaseModel):
    status: Literal["sent"] = "sent"
    message: str
    email: str
    phone: Optional[str] = None
    otp_channel: Literal["email", "sms"] = "email"
    expires_in_seconds: int
    demo_code: Optional[str] = None

class LoginRequestBody(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class LoginResponseBody(BaseModel):
    status: Literal["authenticated"] = "authenticated"
    message: str
    token: str
    refresh_token: Optional[str] = None
    user: AuthUser
    expires_in_seconds: int

class AnonymousResponseBody(BaseModel):
    status: Literal["authenticated"] = "authenticated"
    token: str
    user: AuthUser
    expires_in_seconds: int

class MeResponseBody(BaseModel):
    user: AuthUser

class LogoutResponseBody(BaseModel):
    success: bool
    message: str

# --- Health Model ---
class HealthDependencies(BaseModel):
    retrieval: bool
    answer_generation: bool
    lab_orchestration: bool

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    dependencies: HealthDependencies
    retrieval_version: Optional[str] = "2026.3.1"
    generated_at: str

# --- Query & Intelligence Models ---
ContractEvidenceStatus = Literal["confirmed", "supported", "unverified", "insufficient"]
ContractEvidenceCategory = Literal["source", "lab"]

class ContractEvidenceItem(BaseModel):
    evidence_id: str
    ref_id: str
    status: ContractEvidenceStatus
    category: ContractEvidenceCategory
    text: str
    source_id: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    source_ref: Optional[str] = None
    evidence_ref: Optional[str] = None
    provenance_type: str

class ContractEntity(BaseModel):
    id: str
    type: str
    name: str
    taxonomy: Optional[str] = None
    description: Optional[str] = None
    description_status: Literal["source_supported", "not_available_in_validated_source"] = "source_supported"

class ContractRelationship(BaseModel):
    relationship_id: str
    from_id: str
    relation_type: str
    to_id: str
    provenance_type: str

class ContractChainStage(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    status: ContractEvidenceStatus
    evidence_ids: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    lab_available: bool = False

class ContractDetectionItem(BaseModel):
    title: str
    description: str

class ContractMitigationItem(BaseModel):
    id: Optional[str] = None
    title: str
    description: str

class ContractLabEnvironment(BaseModel):
    lab_id: str
    technique_id: str
    technique_name: str
    available: bool
    launchable: bool
    lab_type: str
    platform: Literal["windows", "linux", "android"]
    runtime_environment: str
    network_mode: str
    validation_source: str
    objective: str
    estimated_duration: str
    difficulty: str
    safety_boundary: str
    session_steps: List[str] = Field(default_factory=list)
    scenario_objective: str

class QueryResultItem(BaseModel):
    rank: int
    entity: ContractEntity
    evidence: List[ContractEvidenceItem] = Field(default_factory=list)
    relationships: List[ContractRelationship] = Field(default_factory=list)
    attack_chain: List[ContractChainStage] = Field(default_factory=list)
    detection: List[ContractDetectionItem] = Field(default_factory=list)
    mitigation: List[ContractMitigationItem] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    lab: Optional[ContractLabEnvironment] = None

QueryOutcome = Literal[
    "ok",
    "no_results",
    "out_of_domain",
    "insufficient_evidence",
    "safety_refused",
]

class QueryRefusal(BaseModel):
    message: str
    alternatives: List[str] = Field(default_factory=list)

class QueryMeta(BaseModel):
    retrieval_version: str
    generated_at: str

class QueryRequestBody(BaseModel):
    query: str
    mode: Optional[Literal["standard", "full_report"]] = "standard"

class QueryResponseBody(BaseModel):
    request_id: str
    query: str
    status: Literal["ok", "empty"]
    outcome: QueryOutcome
    answer: Optional[str] = None
    uncertainty: Optional[str] = None
    results: List[QueryResultItem] = Field(default_factory=list)
    refusal: Optional[QueryRefusal] = None
    meta: QueryMeta

# --- Entity Detail Model ---
class EntitySourceItem(BaseModel):
    source_id: str
    name: str
    url: Optional[str] = None
    kind: str

class EntityProvenanceItem(BaseModel):
    provenance_id: str
    provenance_type: str
    source_name: str
    source_ref: Optional[str] = None
    source_url: Optional[str] = None
    version_or_date: Optional[str] = None

class EntityDetailResponse(BaseModel):
    request_id: str
    entity: ContractEntity
    sources: List[EntitySourceItem] = Field(default_factory=list)
    provenance: List[EntityProvenanceItem] = Field(default_factory=list)
    relationships: List[ContractRelationship] = Field(default_factory=list)
    generated_at: str

# --- History Models ---
class HistoryItemPayload(BaseModel):
    thread_id: str
    investigation_id: str
    question: str
    created_at: int
    preview: str
    source: Literal["remote", "local"] = "remote"

class HistoryTurnPayload(BaseModel):
    id: str
    thread_id: str
    question: str
    answer: Optional[str] = None
    uncertainty: Optional[str] = None
    outcome: str = "ok"
    results: List[QueryResultItem] = Field(default_factory=list)
    created_at: int

class HistoryThreadDetailResponse(BaseModel):
    thread_id: str
    investigation_id: Optional[str] = None
    question: str
    preview: Optional[str] = None
    mode: Optional[str] = "standard"
    created_at: int
    turns: List[HistoryTurnPayload] = Field(default_factory=list)

class HistoryListResponse(BaseModel):
    items: List[HistoryItemPayload] = Field(default_factory=list)
    total: int
    generated_at: str

class DeleteThreadResponse(BaseModel):
    success: bool
    deleted_id: str

# --- Labs Models ---
class LabCatalogItem(BaseModel):
    lab_id: str
    technique_id: str
    technique_name: str
    available: bool
    launchable: bool
    platform: Literal["windows", "linux", "android"]
    validation_source: str

class LabCatalogResponse(BaseModel):
    labs: List[LabCatalogItem] = Field(default_factory=list)
    generated_at: str

class LaunchLabRequestBody(BaseModel):
    lab_id: str
    technique_id: str
    platform: Literal["windows", "linux", "android"]

class LaunchLabResponseBody(BaseModel):
    session_id: str
    lab_id: str
    technique_id: str
    status: Literal["provisioning", "ready", "failed"]
    connection_url: Optional[str] = None
    expires_at: str
    message: Optional[str] = None

class LabSessionStatusResponse(BaseModel):
    session_id: str
    status: Literal["provisioning", "ready", "running", "terminated", "failed"]
    uptime_seconds: int
    telemetry: Optional[Dict[str, Any]] = None
    logs: List[str] = Field(default_factory=list)

class TerminateLabSessionResponse(BaseModel):
    success: bool
    session_id: str
    terminated_at: str

# --- Export Models ---
class ExportRequestBody(BaseModel):
    thread_id: str
    format: Literal["pdf", "json", "markdown"] = "pdf"
    include_provenance: Optional[bool] = True

class ExportResponseBody(BaseModel):
    download_url: str
    file_name: str
    format: str
    generated_at: str

