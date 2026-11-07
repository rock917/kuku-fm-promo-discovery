-- =============================================================================
-- Kuku FM Promo Discovery System — Supabase Database Schema
-- Run this script in your Supabase Dashboard -> SQL Editor
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Pipeline Runs Table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_timestamp TIMESTAMPTZ DEFAULT NOW(),
    show_title TEXT NOT NULL,
    episodes_processed INT NOT NULL DEFAULT 50,
    llm_provider TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    total_candidates_generated INT NOT NULL,
    valid_candidates INT NOT NULL,
    invalid_candidates INT NOT NULL,
    ranked_output_count INT NOT NULL,
    pipeline_duration_sec NUMERIC(6, 2),
    scoring_weights JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick sorting by run date
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at ON pipeline_runs(created_at DESC);

-- 2. Promo Candidates Table
CREATE TABLE IF NOT EXISTS promo_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    candidate_id TEXT NOT NULL,
    rank INT,
    final_score NUMERIC(6, 4),
    is_valid BOOLEAN DEFAULT TRUE,
    primary_episode INT NOT NULL,
    episodes INT[] NOT NULL,
    total_duration_sec NUMERIC(6, 2) NOT NULL,
    opening_hook_text TEXT,
    closing_cliffhanger_text TEXT,
    narrative_context TEXT,
    has_cliffhanger_sfx BOOLEAN DEFAULT FALSE,
    cliffhanger_sfx_note TEXT,
    
    -- AI-generated scores (1.0 to 10.0 scale)
    ai_hook_strength NUMERIC(4, 2),
    ai_cliffhanger_strength NUMERIC(4, 2),
    ai_standalone_clarity NUMERIC(4, 2),
    ai_emotional_impact NUMERIC(4, 2),
    
    -- Programmatic score
    prog_duration_quality NUMERIC(4, 2),
    
    -- Structured diagnostics
    score_breakdown JSONB,
    validation_failures TEXT[] DEFAULT '{}',
    validation_warnings TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promo_candidates_run_id ON promo_candidates(run_id);
CREATE INDEX IF NOT EXISTS idx_promo_candidates_rank ON promo_candidates(rank);
CREATE INDEX IF NOT EXISTS idx_promo_candidates_score ON promo_candidates(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_promo_candidates_episode ON promo_candidates(primary_episode);

-- 3. Promo Segments Table (Supports multi-scene / scene-relative timestamps)
CREATE TABLE IF NOT EXISTS promo_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_ref_id UUID REFERENCES promo_candidates(id) ON DELETE CASCADE,
    episode_number INT NOT NULL,
    scene_number INT NOT NULL,
    scene_heading TEXT,
    start_ts TEXT NOT NULL,
    end_ts TEXT NOT NULL,
    start_sec NUMERIC(7, 2) NOT NULL,
    end_sec NUMERIC(7, 2) NOT NULL,
    duration_sec NUMERIC(7, 2) NOT NULL,
    timestamp_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promo_segments_candidate_ref ON promo_segments(candidate_ref_id);

-- 4. Quality Reports Table
CREATE TABLE IF NOT EXISTS quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    candidate_counts JSONB,
    validation_summary JSONB,
    score_distribution JSONB,
    coverage JSONB,
    raw_report JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Failure Analysis Table
CREATE TABLE IF NOT EXISTS failure_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    summary JSONB,
    system_limitations JSONB,
    validation_failures JSONB,
    weak_candidates JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS) with Public Read Access for Vercel Frontend
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE promo_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE promo_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE failure_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access for pipeline_runs" ON pipeline_runs FOR SELECT USING (true);
CREATE POLICY "Allow public read access for promo_candidates" ON promo_candidates FOR SELECT USING (true);
CREATE POLICY "Allow public read access for promo_segments" ON promo_segments FOR SELECT USING (true);
CREATE POLICY "Allow public read access for quality_reports" ON quality_reports FOR SELECT USING (true);
CREATE POLICY "Allow public read access for failure_analyses" ON failure_analyses FOR SELECT USING (true);

-- Allow service role full access for backend sync
CREATE POLICY "Allow service role full access pipeline_runs" ON pipeline_runs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow service role full access promo_candidates" ON promo_candidates FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow service role full access promo_segments" ON promo_segments FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow service role full access quality_reports" ON quality_reports FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow service role full access failure_analyses" ON failure_analyses FOR ALL USING (auth.role() = 'service_role');

