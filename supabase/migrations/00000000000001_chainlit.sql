-- Migration: Chainlit data layer schema
--
-- Tables required by Chainlit's SQLAlchemyDataLayer for persistent
-- conversation history, step tracking, file elements, and feedback.
--
-- Schema translated from Chainlit's official documentation:
-- https://docs.chainlit.io/data-layers/sqlalchemy
--
-- Includes columns added in later Chainlit versions:
--   - "modes"        (v2.9.4)
--   - "autoCollapse" (v2.10)
--
-- Chainlit uses camelCase column names — we preserve them exactly
-- to avoid any mapping issues with SQLAlchemyDataLayer.

-- ── Users ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    "id"         UUID PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata"   JSONB NOT NULL DEFAULT '{}'::jsonb,
    "createdAt"  TEXT
);

-- ── Threads (conversations) ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS threads (
    "id"             UUID PRIMARY KEY,
    "createdAt"      TEXT,
    "name"           TEXT,
    "userId"         UUID REFERENCES users("id") ON DELETE CASCADE,
    "userIdentifier" TEXT,
    "tags"           TEXT[],
    "metadata"       JSONB
);

CREATE INDEX IF NOT EXISTS idx_threads_user
    ON threads ("userId");

-- ── Steps (individual messages / tool calls) ──────────────────────

CREATE TABLE IF NOT EXISTS steps (
    "id"            UUID PRIMARY KEY,
    "name"          TEXT NOT NULL,
    "type"          TEXT NOT NULL,
    "threadId"      UUID NOT NULL REFERENCES threads("id") ON DELETE CASCADE,
    "parentId"      UUID,
    "streaming"     BOOLEAN NOT NULL DEFAULT false,
    "waitForAnswer" BOOLEAN,
    "isError"       BOOLEAN,
    "metadata"      JSONB,
    "tags"          TEXT[],
    "input"         TEXT,
    "output"        TEXT,
    "createdAt"     TEXT,
    "command"       TEXT,
    "start"         TEXT,
    "end"           TEXT,
    "generation"    JSONB,
    "showInput"     TEXT,
    "language"      TEXT,
    "indent"        INT,
    "defaultOpen"   BOOLEAN,
    "modes"         TEXT,
    "autoCollapse"  BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_steps_thread
    ON steps ("threadId");
CREATE INDEX IF NOT EXISTS idx_steps_created
    ON steps ("createdAt" DESC);

-- ── Elements (file attachments, images, etc.) ─────────────────────

CREATE TABLE IF NOT EXISTS elements (
    "id"          UUID PRIMARY KEY,
    "threadId"    UUID REFERENCES threads("id") ON DELETE CASCADE,
    "type"        TEXT,
    "url"         TEXT,
    "chainlitKey" TEXT,
    "name"        TEXT NOT NULL,
    "display"     TEXT,
    "objectKey"   TEXT,
    "size"        TEXT,
    "page"        INT,
    "language"    TEXT,
    "forId"       UUID,
    "mime"        TEXT,
    "props"       JSONB
);

CREATE INDEX IF NOT EXISTS idx_elements_thread
    ON elements ("threadId");

-- ── Feedbacks ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS feedbacks (
    "id"       UUID PRIMARY KEY,
    "forId"    UUID NOT NULL,
    "threadId" UUID NOT NULL REFERENCES threads("id") ON DELETE CASCADE,
    "value"    INT NOT NULL,
    "comment"  TEXT
);

CREATE INDEX IF NOT EXISTS idx_feedbacks_for
    ON feedbacks ("forId");

-- ── Row Level Security ────────────────────────────────────────────
-- Same pattern as tracing: RLS enabled to lock down PostgREST access.
-- Application connects as postgres role with full access.
-- anon/authenticated roles have no policies = no access.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;

-- Full access for the application's postgres role
CREATE POLICY users_app_full_access ON users
    FOR ALL TO postgres USING (true) WITH CHECK (true);

CREATE POLICY threads_app_full_access ON threads
    FOR ALL TO postgres USING (true) WITH CHECK (true);

CREATE POLICY steps_app_full_access ON steps
    FOR ALL TO postgres USING (true) WITH CHECK (true);

CREATE POLICY elements_app_full_access ON elements
    FOR ALL TO postgres USING (true) WITH CHECK (true);

CREATE POLICY feedbacks_app_full_access ON feedbacks
    FOR ALL TO postgres USING (true) WITH CHECK (true);

-- ── Future: per-user isolation ────────────────────────────────────
-- When multi-user auth is enabled, add policies like:
--
--   CREATE POLICY threads_user_isolation ON threads
--       FOR ALL TO authenticated
--       USING ((select auth.uid()) = "userId")
--       WITH CHECK ((select auth.uid()) = "userId");
--
-- Note: wrap auth.uid() in (select ...) for performance —
-- prevents per-row function evaluation (see security-rls-performance).
