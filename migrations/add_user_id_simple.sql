-- Simple migration to add user_id to sessions table
-- Run this in your Supabase SQL editor

-- Add user_id column
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS user_id TEXT;

-- Update any existing sessions (you can change 'anonymous' to whatever makes sense)
UPDATE sessions 
SET user_id = 'anonymous' 
WHERE user_id IS NULL;

-- Make user_id required
ALTER TABLE sessions 
ALTER COLUMN user_id SET NOT NULL;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_created ON sessions(user_id, created_at DESC);