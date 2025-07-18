-- Migration: Add user_id to sessions table
-- This migration adds user authentication support to the sessions table

-- Step 1: Add user_id column (nullable initially for existing rows)
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS user_id TEXT;

-- Step 2: Update existing sessions with a default user_id (for migration only)
-- In production, you might want to handle this differently
UPDATE sessions 
SET user_id = 'legacy_user' 
WHERE user_id IS NULL;

-- Step 3: Make user_id NOT NULL after updating existing rows
ALTER TABLE sessions 
ALTER COLUMN user_id SET NOT NULL;

-- Step 4: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_created ON sessions(user_id, created_at DESC);

-- Step 5: Add a composite index for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_state ON sessions(user_id, current_state);

-- Step 6: Update the valid_state constraint if it exists
-- First drop the old constraint if it exists
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS valid_state;

-- Then add it back with all valid states
ALTER TABLE sessions ADD CONSTRAINT valid_state CHECK (
    current_state IN (
        'PROVIDE_GREETING',
        'ASK_CLARIFYING_QUESTIONS',
        'CREATE_CONFIRMATION_PLAN',
        'GENERATE_STRAWMAN',
        'REFINE_STRAWMAN'
    )
);

-- Optional: Add Row Level Security (RLS) policies
-- This ensures users can only access their own sessions

-- Enable RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Create policy for selecting own sessions
CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT
    USING (auth.uid()::text = user_id);

-- Create policy for inserting own sessions
CREATE POLICY "Users can insert own sessions" ON sessions
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- Create policy for updating own sessions
CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

-- Create policy for deleting own sessions
CREATE POLICY "Users can delete own sessions" ON sessions
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- Note: If not using Supabase Auth, you can skip the RLS policies
-- or modify them to match your authentication method