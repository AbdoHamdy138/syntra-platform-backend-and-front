# SYNTRA — PostgreSQL Schema Issues Report

**Date:** 2026-11-21  
**Scope:** `backend-integration/backend/init.sql`  
**Source:** Findings recorded in `SYNTRA_BACKEND_INTEGRATION_AUDIT.md` (source-code review, not a live database audit).  
**Current test environment:** PostgreSQL 18.7, database `syntra_integration`, container `syntra_postgres_dev`, Windows port `55432`. The database was verified empty (`\dt` returned no tables).

## Executive summary

The existing `init.sql` is a database backup rather than a clean schema-only initializer. The audit identifies missing primary/unique constraints on five tables, no declared foreign keys, missing uniqueness on account identifiers, no supporting secondary indexes, and sequence values not synchronized after explicit-ID seed inserts. These are **schema-design risks**, not a PostgreSQL installation fault. The database currently running in Docker is empty; none of these schema problems has been deployed to it yet.

| Issue | Evidence in audit | Risk | Priority |
|---|---|---|---|
| Missing PK/unique constraints | Five named tables have no PK/unique protection | Duplicate records and ambiguous references | High |
| Missing foreign keys | No declared FKs in `init.sql` | Orphan records and inconsistent relationships | High |
| Sequences not reset | Four sequences; explicit numeric IDs inserted; no `setval`/restart | Auto-generated IDs may collide after import | High if old seeds imported; lower with clean schema |
| Missing account uniqueness | No declared email/phone uniqueness | Duplicate account identities | High |
| Missing indexes and checks | No secondary indexes or enum checks | Slower lookups and invalid state values | Medium |

## 1. Primary keys and unique constraints

### Verified finding

The audit found **11 primary keys** defined at `init.sql` lines **184–195**, but the following five tables lack primary-key/unique protection:

- `entity_sources`
- `provenance`
- `relationships`
- `detections`
- `mitigations`

### Why this matters

A primary key identifies one row uniquely. Without a primary or unique constraint, duplicate identifiers or duplicate entity-to-source links may be accepted. This also means `INSERT ... ON CONFLICT DO NOTHING` cannot suppress duplicates unless an applicable unique/exclusion constraint exists.

### Proposed resolution

Review each table's intended natural or surrogate key, then add a suitable `PRIMARY KEY` or `UNIQUE` constraint. For example, **if** each entity/source pair should appear only once, `entity_sources` could use a composite key `(entity_id, source_id)`. This is a design proposal, **not a verified existing rule**. Check column types, nullability and intended duplicate semantics before editing.

## 2. Foreign keys

### Verified finding

The audit reports **no declared foreign keys** in `init.sql`.

### Why this matters

An application can insert a child row referring to an entity, thread, user or source that does not exist. This can create orphan records, misleading query results, or broken history/export relationships.

### Proposed resolution

Define explicit relationships based on the actual backend code and column types. Candidate relationships to evaluate include:

- `entity_sources` → `entities` and `sources`
- `detections` / `mitigations` → `entities`
- `thread_turns` → `threads`
- `threads` → `users`, where authenticated ownership is required
- `exports` → `threads` and their owners

These are **candidate relationships**, not confirmed FK definitions. Decide `ON DELETE RESTRICT`, `CASCADE` or `SET NULL` per relationship; avoid automatically cascading deletion of security history or audit evidence.

## 3. Sequences and auto-generated IDs

### Verified finding

The audit found **four sequences** at `init.sql` lines **8–11**. The original backup explicitly inserts numeric IDs for OTP, detections and mitigations, but has no `setval(...)` or sequence restart commands.

### Why this matters

When IDs are inserted manually, the associated sequence may still generate an already-used value. A subsequent insert can fail with `duplicate key value violates unique constraint`. Where no PK/unique constraint exists (e.g. detections/mitigations), a duplicate may instead be silently accepted.

### Proposed resolution

Because the integration database is empty and historical users, OTPs and conversations are **not needed**, the preferred fix is to **remove old seed inserts** and initialize only the reviewed schema plus any genuinely required nonpersonal reference data. Confirm identity/sequence defaults are correctly attached to columns. Use `setval` only if keeping legitimate explicit-ID seed rows, after identifying the actual sequence-to-column mappings.

## 4. Additional issues identified by the audit

- **Account uniqueness:** no declared uniqueness constraints for email/phone identifiers. Decide normalization and verification rules before adding uniqueness.
- **Indexes:** no supporting secondary indexes. Consider indexes for thread ownership and recency, turns by thread/time, and OTP identity/flow/time, guided by real query patterns.
- **Status/value checks:** no declared enum-value `CHECK` constraints. Add only after validating permitted values against application models.
- **Old data in initializer:** the audit counted **79 user INSERTs** and **78 OTP INSERTs**, plus historical conversations. Do not import these into a clean development database.

## 5. Recommended implementation approach — no duplicate project files

1. Review `backend/init.sql` and the FastAPI SQL queries together.
2. Edit the **existing** `backend/init.sql` in place: remove personal/historical seed records and retain only required reference data.
3. Add reviewed PK/unique constraints, FKs, checks and indexes to that same file.
4. Confirm sequences/defaults; reset sequences only when explicit-ID seed data remains.
5. Validate against the **currently empty** `syntra_integration` database. Do not run the original unreviewed initializer or existing Compose bootstrap.
6. Test account creation, thread/turn storage, exports, entity lookups, duplicate rejection and referential integrity.

**Safety:** Before changing the original file, keep a version-controlled commit or an external backup. Do not create multiple duplicate schema files inside the project. Do not delete the PostgreSQL Docker volume or disturb the existing n8n container.

## 6. Read-only verification SQL (after schema deployment)

List tables without a primary key:

```sql
SELECT t.table_schema, t.table_name
FROM information_schema.tables AS t
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints AS c
    WHERE c.table_schema = t.table_schema
      AND c.table_name = t.table_name
      AND c.constraint_type = 'PRIMARY KEY'
  )
ORDER BY t.table_name;
```

List foreign keys:

```sql
SELECT conrelid::regclass AS table_name, conname AS constraint_name,
       confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE contype = 'f' AND connamespace = 'public'::regnamespace
ORDER BY 1, 2;
```

List serial/identity-backed columns and their sequences (where discoverable):

```sql
SELECT table_name, column_name,
       pg_get_serial_sequence(format('%I.%I', table_schema, table_name), column_name) AS sequence_name
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

These commands **inspect** the database; they do not alter it. The current empty database will naturally return no application tables or FKs.

## 7. Evidence and limitations

This report is based on the earlier source audit, particularly `backend/init.sql:8–195` and the SQL seed analysis. The precise PK/FK DDL changes must be reviewed against the complete current `init.sql` and backend query code before execution. No migration has been run, no application files have been changed, and no claim is made that the empty PostgreSQL database already contains these defects.
