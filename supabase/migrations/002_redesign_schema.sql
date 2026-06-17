-- =============================================================================
-- AI-Interview-Agent: Comprehensive Schema Redesign
-- Migration 002 — Replaces the initial 4-table schema with 7 production tables
-- =============================================================================
-- Tables:
--   1. programs                — Bootcamp requirements, rubric, topics
--   2. candidates              — Applicant registry with status tracking
--   3. candidate_profiles      — Structured long-term memory (JSONB sections)
--   4. interview_sessions      — Interview state & progress tracking
--   5. interview_turns         — Per-turn Q&A with evaluation data
--   6. interview_reports       — Final assessment & decision support
--   7. conversation_messages   — Chat history for FastAPI interface
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Drop old tables (from migration 001)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS candidate_reports CASCADE;
DROP TABLE IF EXISTS candidate_responses CASCADE;
DROP TABLE IF EXISTS interview_sessions CASCADE;
DROP TABLE IF EXISTS candidates CASCADE;

-- Drop old trigger function if exists
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- ---------------------------------------------------------------------------
-- 0b. Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Helper: Auto-update updated_at trigger function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ===========================================================================
-- 1. programs — Bootcamp/program definitions & requirements
-- ===========================================================================
-- Replaces the hardcoded get_program_requirements() dict.
-- Each program defines its own required topics, skills to assess, and rubric.
-- ---------------------------------------------------------------------------
CREATE TABLE programs (
    id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name             text        NOT NULL,
    description      text,
    required_topics  jsonb       NOT NULL DEFAULT '["background","education","experience","skills","projects"]'::jsonb,
    skills_to_assess jsonb       NOT NULL DEFAULT '["Python","ML basics","problem solving","communication"]'::jsonb,
    rubric           jsonb       NOT NULL DEFAULT '{}'::jsonb,
    max_turns        int         NOT NULL DEFAULT 30,
    is_active        boolean     NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  programs IS 'Bootcamp program definitions with interview requirements, rubric, and topic list.';
COMMENT ON COLUMN programs.required_topics  IS 'JSON array of topic strings the interview must cover.';
COMMENT ON COLUMN programs.skills_to_assess IS 'JSON array of skill strings to evaluate during interview.';
COMMENT ON COLUMN programs.rubric           IS 'JSON object with scoring criteria: {excellent, good, weak}.';
COMMENT ON COLUMN programs.max_turns        IS 'Maximum number of interview turns before wrap-up.';

CREATE INDEX idx_programs_active ON programs(is_active) WHERE is_active = true;

CREATE TRIGGER trg_programs_updated_at
    BEFORE UPDATE ON programs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ===========================================================================
-- 2. candidates — Applicant registry
-- ===========================================================================
-- Tracks every candidate who enters the system.
-- Status field supports the full applicant lifecycle.
-- ---------------------------------------------------------------------------
CREATE TABLE candidates (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name   text        NOT NULL,
    email       text        UNIQUE,
    phone       text,
    status      text        NOT NULL DEFAULT 'new'
                            CHECK (status IN ('new', 'interviewing', 'interviewed', 'accepted', 'rejected')),
    metadata    jsonb       DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  candidates IS 'Master registry of all bootcamp applicants.';
COMMENT ON COLUMN candidates.status IS 'Lifecycle: new → interviewing → interviewed → accepted/rejected.';

CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_email  ON candidates(email);

CREATE TRIGGER trg_candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ===========================================================================
-- 3. candidate_profiles — Structured long-term memory
-- ===========================================================================
-- Built incrementally by update_candidate_profile() during the interview.
-- Each JSONB column stores a different aspect of the candidate's profile.
-- This is the "Long-Term Memory" from the requirements.
-- ---------------------------------------------------------------------------
CREATE TABLE candidate_profiles (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    uuid        NOT NULL UNIQUE REFERENCES candidates(id) ON DELETE CASCADE,

    -- Structured profile sections (JSONB for flexibility)
    background      jsonb       DEFAULT '{}'::jsonb,
    education       jsonb       DEFAULT '{}'::jsonb,
    experience      jsonb       DEFAULT '[]'::jsonb,
    skills          jsonb       DEFAULT '{"technical":[],"soft":[],"proficiency":{}}'::jsonb,
    projects        jsonb       DEFAULT '[]'::jsonb,

    -- Agent-synthesized assessment
    strengths       text,
    weaknesses      text,

    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  candidate_profiles IS 'Structured candidate profile built incrementally during interview. Long-term memory store.';
COMMENT ON COLUMN candidate_profiles.background IS 'JSON: {summary, location, motivation, career_goals, ...}';
COMMENT ON COLUMN candidate_profiles.education  IS 'JSON: {degree, university, field, gpa, graduation_year, certifications, ...}';
COMMENT ON COLUMN candidate_profiles.experience IS 'JSON array: [{role, company, duration, highlights, technologies}, ...]';
COMMENT ON COLUMN candidate_profiles.skills     IS 'JSON: {technical: [...], soft: [...], proficiency: {skill: score}}';
COMMENT ON COLUMN candidate_profiles.projects   IS 'JSON array: [{name, description, tech_stack, role, outcome, url}, ...]';

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON candidate_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ===========================================================================
-- 4. interview_sessions — Interview state & progress tracking
-- ===========================================================================
-- One row per interview run. Mirrors the LangGraph InterviewState.
-- Persists state for session recovery and analytics.
-- ---------------------------------------------------------------------------
CREATE TABLE interview_sessions (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    uuid        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    program_id      uuid        REFERENCES programs(id) ON DELETE SET NULL,

    -- Interview state
    status          text        NOT NULL DEFAULT 'in_progress'
                                CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    current_topic   text,
    topics_covered  text[]      DEFAULT '{}',
    missing_topics  text[]      DEFAULT '{}',
    turn_count      int         NOT NULL DEFAULT 0,
    scores          jsonb       DEFAULT '{}'::jsonb,

    -- Timestamps
    started_at      timestamptz NOT NULL DEFAULT now(),
    ended_at        timestamptz
);

COMMENT ON TABLE  interview_sessions IS 'Tracks each interview run — mirrors LangGraph InterviewState for persistence.';
COMMENT ON COLUMN interview_sessions.current_topic  IS 'The topic currently being asked about.';
COMMENT ON COLUMN interview_sessions.topics_covered IS 'Array of topics that have been sufficiently covered.';
COMMENT ON COLUMN interview_sessions.missing_topics IS 'Array of required topics not yet covered — used by identify_missing_info().';
COMMENT ON COLUMN interview_sessions.scores         IS 'Nested score payload: {"summary_metrics": {...}, "topic_scores": {"skills": {"final_topic_score": 4.0, "turn_scores": [...]}}}.';

CREATE INDEX idx_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX idx_sessions_program   ON interview_sessions(program_id);
CREATE INDEX idx_sessions_status    ON interview_sessions(status);
CREATE INDEX idx_sessions_started   ON interview_sessions(started_at DESC);


-- ===========================================================================
-- 5. interview_turns — Per-turn Q&A with evaluation
-- ===========================================================================
-- One row per question-answer cycle. The heart of the interview data.
-- Stores question (from generate_question), answer, and evaluation
-- (from evaluate_answer) including score, feedback, and extracted data.
-- ---------------------------------------------------------------------------
CREATE TABLE interview_turns (
    id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id        uuid        NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    turn_number       int         NOT NULL,
    topic             text        NOT NULL,

    -- Q&A
    question          text        NOT NULL,
    answer            text,

    -- Evaluation (from evaluate_answer)
    score             int         CHECK (score IS NULL OR (score >= 1 AND score <= 5)),
    feedback          text,
    needs_probe       boolean     DEFAULT false,

    -- Extracted data
    extracted_skills  jsonb       DEFAULT '[]'::jsonb,
    extracted_info    jsonb       DEFAULT '{}'::jsonb,

    created_at        timestamptz NOT NULL DEFAULT now(),

    -- Ensure unique turn numbers within a session
    UNIQUE (session_id, turn_number)
);

COMMENT ON TABLE  interview_turns IS 'Each question-answer-evaluation cycle within an interview session.';
COMMENT ON COLUMN interview_turns.extracted_skills IS 'JSON array of technical skills mentioned: ["Python", "TensorFlow", ...].';
COMMENT ON COLUMN interview_turns.extracted_info   IS 'Structured info extracted from answer for profile building.';
COMMENT ON COLUMN interview_turns.needs_probe      IS 'True if the agent should ask a follow-up probe question.';

CREATE INDEX idx_turns_session    ON interview_turns(session_id);
CREATE INDEX idx_turns_topic      ON interview_turns(topic);
CREATE INDEX idx_turns_session_turn ON interview_turns(session_id, turn_number);


-- ===========================================================================
-- 6. interview_reports — Final assessment & decision support
-- ===========================================================================
-- Generated by generate_report() and calculate_score().
-- One report per session. Includes recommendation for admissions team.
-- ---------------------------------------------------------------------------
CREATE TABLE interview_reports (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      uuid        NOT NULL UNIQUE REFERENCES interview_sessions(id) ON DELETE CASCADE,
    candidate_id    uuid        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,

    -- Scores
    topic_scores    jsonb       NOT NULL DEFAULT '{}'::jsonb,
    overall_score   numeric(3,2),

    -- Assessment
    summary         text,
    recommendation  text        CHECK (recommendation IS NULL OR recommendation IN ('accept', 'reject', 'review')),
    strengths       text,
    weaknesses      text,
    decision_notes  text,

    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  interview_reports IS 'Final interview assessment report for decision support.';
COMMENT ON COLUMN interview_reports.topic_scores   IS 'Nested score payload copied from interview_sessions.scores for final reporting.';
COMMENT ON COLUMN interview_reports.overall_score  IS 'Weighted or averaged score (0.00–5.00).';
COMMENT ON COLUMN interview_reports.recommendation IS 'Agent recommendation: accept, reject, or review.';
COMMENT ON COLUMN interview_reports.decision_notes IS 'Additional context for the admissions team.';

CREATE INDEX idx_reports_candidate     ON interview_reports(candidate_id);
CREATE INDEX idx_reports_overall       ON interview_reports(overall_score DESC);
CREATE INDEX idx_reports_recommendation ON interview_reports(recommendation);

CREATE TRIGGER trg_reports_updated_at
    BEFORE UPDATE ON interview_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ===========================================================================
-- 7. conversation_messages — Chat history for FastAPI interface
-- ===========================================================================
-- Stores the full conversation flow for the chat UI.
-- Each message is tagged with role (system/assistant/user).
-- ---------------------------------------------------------------------------
CREATE TABLE conversation_messages (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  uuid        NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    role        text        NOT NULL CHECK (role IN ('system', 'assistant', 'user')),
    content     text        NOT NULL,
    metadata    jsonb       DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE  conversation_messages IS 'Chat message history for the FastAPI conversational interface.';
COMMENT ON COLUMN conversation_messages.role     IS 'Message sender: system, assistant (agent), or user (candidate).';
COMMENT ON COLUMN conversation_messages.metadata IS 'Optional: {turn_number, topic, tool_call, ...}.';

CREATE INDEX idx_messages_session ON conversation_messages(session_id);
CREATE INDEX idx_messages_created ON conversation_messages(session_id, created_at);


-- ===========================================================================
-- 8. Row Level Security (RLS)
-- ===========================================================================
-- Enable RLS on all tables (Supabase best practice).
-- service_role key automatically bypasses RLS.
-- Policies grant authenticated users access (for FastAPI backend).
-- ---------------------------------------------------------------------------

ALTER TABLE programs              ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates            ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_turns       ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_reports     ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

-- Programs: readable by all authenticated users
CREATE POLICY "programs_read_authenticated"
    ON programs FOR SELECT
    TO authenticated
    USING (true);

-- Programs: only service role can modify (via bypass)
-- No INSERT/UPDATE/DELETE policy for authenticated — service_role handles it.

-- Candidates: full CRUD for authenticated (backend service)
CREATE POLICY "candidates_all_authenticated"
    ON candidates FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Candidate profiles: full CRUD for authenticated
CREATE POLICY "profiles_all_authenticated"
    ON candidate_profiles FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Interview sessions: full CRUD for authenticated
CREATE POLICY "sessions_all_authenticated"
    ON interview_sessions FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Interview turns: full CRUD for authenticated
CREATE POLICY "turns_all_authenticated"
    ON interview_turns FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Interview reports: full CRUD for authenticated
CREATE POLICY "reports_all_authenticated"
    ON interview_reports FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Conversation messages: full CRUD for authenticated
CREATE POLICY "messages_all_authenticated"
    ON conversation_messages FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);


-- ===========================================================================
-- 9. Seed Data — Default bootcamp program
-- ===========================================================================
-- Matches the current hardcoded get_program_requirements() in tools.py
-- ---------------------------------------------------------------------------
INSERT INTO programs (name, description, required_topics, skills_to_assess, rubric, max_turns)
VALUES (
    'AI & Software Engineering Bootcamp',
    'Intensive bootcamp for candidates seeking training in AI, machine learning, and software engineering. '
    'The interview assesses technical background, education, professional experience, skills, and project portfolio.',
    '["background", "education", "experience", "skills", "projects"]'::jsonb,
    '["Python", "ML basics", "problem solving", "communication"]'::jsonb,
    '{
        "excellent": "Clear, detailed, relevant answer with specific technical examples and demonstrable depth.",
        "good": "Mostly relevant and conceptually correct, but with minor gaps or lacks deep implementation details.",
        "weak": "Vague, brief, off-topic, or shows fundamental misunderstandings. Needs probing."
    }'::jsonb,
    30
);


-- ===========================================================================
-- Done! Schema v2 deployed.
-- ===========================================================================
