#!/usr/bin/env python3
"""
Database setup script for the presentation generator.
Creates necessary tables, extensions, and functions in Supabase.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# SQL statements for database setup
ENABLE_EXTENSIONS = """
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
"""

CREATE_SESSIONS_TABLE = """
-- Sessions table for managing user sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_history JSONB[] DEFAULT ARRAY[]::JSONB[],
    current_state JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    expires_at TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Index for user_id lookups
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Index for cleanup of expired sessions
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE
    ON sessions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
"""

CREATE_PRESENTATIONS_TABLE = """
-- Presentations table with vector embeddings
CREATE TABLE IF NOT EXISTS presentations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    structure JSONB NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    presentation_type TEXT,
    industry TEXT,
    target_audience TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    metadata JSONB DEFAULT '{}'::JSONB,
    version INTEGER DEFAULT 1,
    is_template BOOLEAN DEFAULT FALSE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_presentations_session_id ON presentations(session_id);
CREATE INDEX IF NOT EXISTS idx_presentations_type ON presentations(presentation_type);
CREATE INDEX IF NOT EXISTS idx_presentations_created_at ON presentations(created_at DESC);

-- Vector similarity search index (IVFFlat)
CREATE INDEX IF NOT EXISTS presentations_embedding_idx ON presentations 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Updated timestamp trigger
CREATE TRIGGER update_presentations_updated_at BEFORE UPDATE
    ON presentations FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
"""

CREATE_VISUAL_ASSETS_TABLE = """
-- Visual assets table for storing generated images and graphics
CREATE TABLE IF NOT EXISTS visual_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    presentation_id UUID REFERENCES presentations(id) ON DELETE CASCADE,
    slide_number INTEGER NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('image', 'chart', 'diagram', 'icon')),
    url TEXT NOT NULL,
    prompt TEXT,
    style_params JSONB DEFAULT '{}'::JSONB,
    embedding vector(512), -- CLIP embedding dimension for visual similarity
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::JSONB,
    usage_count INTEGER DEFAULT 0,
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    created_by TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_visual_assets_presentation_id ON visual_assets(presentation_id);
CREATE INDEX IF NOT EXISTS idx_visual_assets_type ON visual_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_visual_assets_tags ON visual_assets USING GIN(tags);

-- Vector similarity search index for visual assets
CREATE INDEX IF NOT EXISTS visual_assets_embedding_idx ON visual_assets 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
"""

CREATE_AGENT_OUTPUTS_TABLE = """
-- Agent outputs table for tracking all agent responses
CREATE TABLE IF NOT EXISTS agent_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    output_type TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'partial', 'failed')),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    error_message TEXT,
    processing_time_ms INTEGER,
    tokens_used JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_outputs_session_id ON agent_outputs(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_agent_id ON agent_outputs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_correlation_id ON agent_outputs(correlation_id);
CREATE INDEX IF NOT EXISTS idx_agent_outputs_created_at ON agent_outputs(created_at DESC);
"""

CREATE_SIMILARITY_FUNCTIONS = """
-- Function to find similar presentations
CREATE OR REPLACE FUNCTION match_presentations(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.8,
    match_count int DEFAULT 5,
    filter_type text DEFAULT NULL,
    filter_industry text DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    description TEXT,
    structure JSONB,
    presentation_type TEXT,
    industry TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.description,
        p.structure,
        p.presentation_type,
        p.industry,
        1 - (p.embedding <=> query_embedding) as similarity
    FROM presentations p
    WHERE 
        p.embedding IS NOT NULL
        AND 1 - (p.embedding <=> query_embedding) > match_threshold
        AND (filter_type IS NULL OR p.presentation_type = filter_type)
        AND (filter_industry IS NULL OR p.industry = filter_industry)
        AND p.is_template = TRUE
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to find similar visual assets
CREATE OR REPLACE FUNCTION match_visual_assets(
    query_embedding vector(512),
    asset_type_filter text DEFAULT NULL,
    match_threshold float DEFAULT 0.75,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    asset_type TEXT,
    url TEXT,
    tags TEXT[],
    metadata JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.asset_type,
        v.url,
        v.tags,
        v.metadata,
        1 - (v.embedding <=> query_embedding) as similarity
    FROM visual_assets v
    WHERE 
        v.embedding IS NOT NULL
        AND 1 - (v.embedding <=> query_embedding) > match_threshold
        AND (asset_type_filter IS NULL OR v.asset_type = asset_type_filter)
    ORDER BY v.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM sessions
    WHERE expires_at < TIMEZONE('utc', NOW());
END;
$$;
"""

CREATE_RLS_POLICIES = """
-- Enable Row Level Security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE presentations ENABLE ROW LEVEL SECURITY;
ALTER TABLE visual_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_outputs ENABLE ROW LEVEL SECURITY;

-- Sessions policies
CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own sessions" ON sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own sessions" ON sessions
    FOR DELETE USING (auth.uid()::text = user_id);

-- Presentations policies
CREATE POLICY "Users can view own presentations" ON presentations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sessions s 
            WHERE s.id = presentations.session_id 
            AND s.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert own presentations" ON presentations
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions s 
            WHERE s.id = presentations.session_id 
            AND s.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can update own presentations" ON presentations
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM sessions s 
            WHERE s.id = presentations.session_id 
            AND s.user_id = auth.uid()::text
        )
    );

-- Visual assets policies
CREATE POLICY "Users can view assets from own presentations" ON visual_assets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM presentations p
            JOIN sessions s ON s.id = p.session_id
            WHERE p.id = visual_assets.presentation_id 
            AND s.user_id = auth.uid()::text
        )
    );

-- Agent outputs policies
CREATE POLICY "Users can view own agent outputs" ON agent_outputs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sessions s 
            WHERE s.id = agent_outputs.session_id 
            AND s.user_id = auth.uid()::text
        )
    );
"""


def setup_database():
    """Run all database setup commands."""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
        sys.exit(1)
    
    print("Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Note: The Supabase Python client doesn't support direct SQL execution
    # You'll need to run these SQL commands directly in the Supabase SQL editor
    # or use the Supabase CLI
    
    print("\nDatabase setup SQL has been generated.")
    print("Please run the following SQL commands in your Supabase SQL editor:")
    print("1. Go to https://app.supabase.com/project/[your-project]/sql")
    print("2. Run each section in order:\n")
    
    sections = [
        ("Enable Extensions", ENABLE_EXTENSIONS),
        ("Create Sessions Table", CREATE_SESSIONS_TABLE),
        ("Create Presentations Table", CREATE_PRESENTATIONS_TABLE),
        ("Create Visual Assets Table", CREATE_VISUAL_ASSETS_TABLE),
        ("Create Agent Outputs Table", CREATE_AGENT_OUTPUTS_TABLE),
        ("Create Similarity Functions", CREATE_SIMILARITY_FUNCTIONS),
        ("Create RLS Policies", CREATE_RLS_POLICIES)
    ]
    
    # Save to SQL file
    sql_file_path = Path(__file__).parent / "setup_database.sql"
    with open(sql_file_path, "w") as f:
        for name, sql in sections:
            f.write(f"-- {name}\n")
            f.write(sql)
            f.write("\n\n")
    
    print(f"\nSQL commands have been saved to: {sql_file_path}")
    print("\nYou can also run this file using the Supabase CLI:")
    print(f"supabase db reset --db-url $SUPABASE_DB_URL")
    print(f"supabase db push --db-url $SUPABASE_DB_URL")


if __name__ == "__main__":
    setup_database()