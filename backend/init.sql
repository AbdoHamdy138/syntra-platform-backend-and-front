-- ============================================================
-- SYNTRA PostgreSQL Clean Production Initializer
-- Strictly maintains table & column names
-- Implements PKs on all 16 tables, FKs, Indexes & Sequence sync
-- Contains zero user/chat raw test data; contains full threat knowledge catalog
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Sequences
CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS otp_codes_id_seq;
CREATE SEQUENCE IF NOT EXISTS detections_id_seq;
CREATE SEQUENCE IF NOT EXISTS mitigations_id_seq;

-- Table Definitions
CREATE TABLE IF NOT EXISTS users (
    id CHARACTER VARYING(64) DEFAULT nextval('users_id_seq'::regclass) NOT NULL,
    email CHARACTER VARYING(255),
    name CHARACTER VARYING(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    password_hash CHARACTER VARYING(255),
    role CHARACTER VARYING(32) DEFAULT 'analyst'::character varying,
    avatar_url TEXT,
    is_verified BOOLEAN DEFAULT false,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    phone CHARACTER VARYING(64)
);

CREATE TABLE IF NOT EXISTS otp_codes (
    id INTEGER DEFAULT nextval('otp_codes_id_seq'::regclass) NOT NULL,
    email CHARACTER VARYING(255) NOT NULL,
    code CHARACTER VARYING(10) NOT NULL,
    flow CHARACTER VARYING(32) DEFAULT 'signup'::character varying NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    max_attempts INTEGER DEFAULT 5,
    phone CHARACTER VARYING(64)
);

CREATE TABLE IF NOT EXISTS sources (
    id CHARACTER VARYING(64) NOT NULL,
    name CHARACTER VARYING(255) NOT NULL,
    url TEXT,
    kind CHARACTER VARYING(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS entities (
    id CHARACTER VARYING(64) NOT NULL,
    type CHARACTER VARYING(32) NOT NULL,
    name CHARACTER VARYING(255) NOT NULL,
    taxonomy CHARACTER VARYING(255),
    description TEXT,
    description_status CHARACTER VARYING(64) DEFAULT 'source_supported'::character varying,
    summary TEXT,
    missing_evidence JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS entity_sources (
    entity_id CHARACTER VARYING(64) NOT NULL,
    source_id CHARACTER VARYING(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS provenance (
    id CHARACTER VARYING(64) NOT NULL,
    entity_id CHARACTER VARYING(64),
    provenance_type CHARACTER VARYING(128) NOT NULL,
    source_name CHARACTER VARYING(255) NOT NULL,
    source_ref CHARACTER VARYING(255),
    source_url TEXT,
    version_or_date CHARACTER VARYING(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS relationships (
    id CHARACTER VARYING(64) NOT NULL,
    from_id CHARACTER VARYING(64) NOT NULL,
    relation_type CHARACTER VARYING(64) NOT NULL,
    to_id CHARACTER VARYING(64) NOT NULL,
    provenance_type CHARACTER VARYING(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence (
    id CHARACTER VARYING(64) NOT NULL,
    ref_id CHARACTER VARYING(64) NOT NULL,
    status CHARACTER VARYING(32) DEFAULT 'confirmed'::character varying NOT NULL,
    category CHARACTER VARYING(32) DEFAULT 'source'::character varying NOT NULL,
    text TEXT NOT NULL,
    source_id CHARACTER VARYING(64),
    source_name CHARACTER VARYING(255) NOT NULL,
    source_url TEXT,
    source_ref CHARACTER VARYING(255),
    evidence_ref CHARACTER VARYING(255),
    provenance_type CHARACTER VARYING(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS attack_chain_stages (
    id CHARACTER VARYING(64) NOT NULL,
    entity_id CHARACTER VARYING(64),
    stage_order INTEGER DEFAULT 0,
    technique_id CHARACTER VARYING(64) NOT NULL,
    technique_name CHARACTER VARYING(255) NOT NULL,
    tactic CHARACTER VARYING(128) NOT NULL,
    status CHARACTER VARYING(32) DEFAULT 'confirmed'::character varying,
    evidence_ids JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    steps JSONB DEFAULT '[]'::jsonb,
    lab_available BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS detections (
    id INTEGER DEFAULT nextval('detections_id_seq'::regclass) NOT NULL,
    entity_id CHARACTER VARYING(64),
    title CHARACTER VARYING(255) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mitigations (
    id INTEGER DEFAULT nextval('mitigations_id_seq'::regclass) NOT NULL,
    entity_id CHARACTER VARYING(64),
    mitigation_id CHARACTER VARYING(64),
    title CHARACTER VARYING(255) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS labs (
    lab_id CHARACTER VARYING(64) NOT NULL,
    technique_id CHARACTER VARYING(64) NOT NULL,
    technique_name CHARACTER VARYING(255) NOT NULL,
    available BOOLEAN DEFAULT true,
    launchable BOOLEAN DEFAULT true,
    lab_type CHARACTER VARYING(128) DEFAULT 'Controlled Technique Validation'::character varying,
    platform CHARACTER VARYING(32) DEFAULT 'windows'::character varying,
    runtime_environment CHARACTER VARYING(255),
    network_mode CHARACTER VARYING(128),
    validation_source CHARACTER VARYING(255),
    objective TEXT,
    estimated_duration CHARACTER VARYING(64),
    difficulty CHARACTER VARYING(64),
    safety_boundary TEXT,
    session_steps JSONB DEFAULT '[]'::jsonb,
    scenario_objective TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lab_sessions (
    session_id CHARACTER VARYING(64) NOT NULL,
    user_id CHARACTER VARYING(64),
    lab_id CHARACTER VARYING(64),
    technique_id CHARACTER VARYING(64) NOT NULL,
    status CHARACTER VARYING(32) DEFAULT 'ready'::character varying,
    connection_url TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    telemetry JSONB,
    logs JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    terminated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS threads (
    id CHARACTER VARYING(64) DEFAULT gen_random_uuid() NOT NULL,
    user_id CHARACTER VARYING(64),
    question TEXT NOT NULL,
    status_kind CHARACTER VARYING(50) DEFAULT 'unverified'::character varying,
    turn_count INTEGER DEFAULT 1,
    pinned BOOLEAN DEFAULT false,
    archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    investigation_id CHARACTER VARYING(64),
    preview TEXT,
    mode CHARACTER VARYING(32) DEFAULT 'standard'::character varying,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS thread_turns (
    id CHARACTER VARYING(64) NOT NULL,
    thread_id CHARACTER VARYING(64) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    uncertainty TEXT,
    outcome CHARACTER VARYING(50) DEFAULT 'ok'::character varying,
    result_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS exports (
    id CHARACTER VARYING(64) NOT NULL,
    thread_id CHARACTER VARYING(64),
    user_id CHARACTER VARYING(64),
    format CHARACTER VARYING(32) NOT NULL,
    file_name CHARACTER VARYING(255) NOT NULL,
    file_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ============================================================
-- 1. Primary Keys & Unique Constraints
-- ============================================================
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'users'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE users ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'otp_codes'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE otp_codes ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'sources'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE sources ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'entities'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE entities ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'provenance'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE provenance ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'relationships'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE relationships ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'evidence'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE evidence ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'attack_chain_stages'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE attack_chain_stages ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'detections'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE detections ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'mitigations'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE mitigations ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'labs'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE labs ADD PRIMARY KEY (lab_id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'lab_sessions'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE lab_sessions ADD PRIMARY KEY (session_id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'threads'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE threads ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'thread_turns'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE thread_turns ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'exports'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE exports ADD PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'entity_sources'::regclass AND contype = 'p'
    ) THEN
        ALTER TABLE entity_sources ADD PRIMARY KEY (entity_id, source_id);
    END IF;
END $$;

-- Account Uniqueness Constraints
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (LOWER(email)) WHERE email IS NOT NULL AND email != '';
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_phone ON users (phone) WHERE phone IS NOT NULL AND phone != '';

-- ============================================================
-- 2. Foreign Key Referential Integrity Constraints
-- ============================================================
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_entity_sources_entity') THEN
        ALTER TABLE entity_sources ADD CONSTRAINT fk_entity_sources_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_entity_sources_source') THEN
        ALTER TABLE entity_sources ADD CONSTRAINT fk_entity_sources_source FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_provenance_entity') THEN
        ALTER TABLE provenance ADD CONSTRAINT fk_provenance_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_attack_chain_stages_entity') THEN
        ALTER TABLE attack_chain_stages ADD CONSTRAINT fk_attack_chain_stages_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_detections_entity') THEN
        ALTER TABLE detections ADD CONSTRAINT fk_detections_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_mitigations_entity') THEN
        ALTER TABLE mitigations ADD CONSTRAINT fk_mitigations_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_labs_entity') THEN
        ALTER TABLE labs ADD CONSTRAINT fk_labs_entity FOREIGN KEY (technique_id) REFERENCES entities(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sessions_lab') THEN
        ALTER TABLE lab_sessions ADD CONSTRAINT fk_lab_sessions_lab FOREIGN KEY (lab_id) REFERENCES labs(lab_id) ON DELETE SET NULL;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sessions_user') THEN
        ALTER TABLE lab_sessions ADD CONSTRAINT fk_lab_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_threads_user') THEN
        ALTER TABLE threads ADD CONSTRAINT fk_threads_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_thread_turns_thread') THEN
        ALTER TABLE thread_turns ADD CONSTRAINT fk_thread_turns_thread FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_exports_thread') THEN
        ALTER TABLE exports ADD CONSTRAINT fk_exports_thread FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE SET NULL;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_exports_user') THEN
        ALTER TABLE exports ADD CONSTRAINT fk_exports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================
-- 3. Secondary Performance Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_threads_user_created ON threads (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_thread_turns_thread_created ON thread_turns (thread_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_otp_codes_lookup ON otp_codes (email, phone, flow, used_at);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities (name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (type);
CREATE INDEX IF NOT EXISTS idx_attack_chain_entity_order ON attack_chain_stages (entity_id, stage_order ASC);
CREATE INDEX IF NOT EXISTS idx_evidence_ref_id ON evidence (ref_id);
CREATE INDEX IF NOT EXISTS idx_detections_entity_id ON detections (entity_id);
CREATE INDEX IF NOT EXISTS idx_mitigations_entity_id ON mitigations (entity_id);
CREATE INDEX IF NOT EXISTS idx_labs_technique_id ON labs (technique_id);
CREATE INDEX IF NOT EXISTS idx_exports_thread_id ON exports (thread_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_user_status ON lab_sessions (user_id, status);

-- ============================================================
-- 4. Identity Sequence Reset (Schema-Only Initialization)
-- ============================================================
SELECT setval('users_id_seq', 1, false);
SELECT setval('otp_codes_id_seq', 1, false);
SELECT setval('detections_id_seq', 1, false);
SELECT setval('mitigations_id_seq', 1, false);

