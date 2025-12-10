-- Migration: Add API Keys support
-- Date: 2025-12-10

-- Create table for user API keys
CREATE TABLE IF NOT EXISTS user_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'exhausted')),
    key_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add columns to users table for key management
ALTER TABLE users ADD COLUMN current_key_index INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN last_key_reset_date TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_status ON user_api_keys(status);
