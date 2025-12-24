-- Migration: Add export_history table
-- Description: Track all export operations with settings, status, and file information
-- Date: 2025-12-24

-- Create export_history table
CREATE TABLE IF NOT EXISTS export_history (
    id VARCHAR(36) PRIMARY KEY,
    file_id VARCHAR(36) NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Export details
    export_format VARCHAR(20) NOT NULL,  -- png, svg, pdf, json, md, html
    export_type VARCHAR(50) DEFAULT 'full',  -- full, selection, figure
    
    -- Export settings (JSON for flexibility)
    export_settings JSONB DEFAULT '{}',
    
    -- File information
    file_size BIGINT,
    file_path VARCHAR(1024),
    download_url VARCHAR(1024),
    
    -- Status
    status VARCHAR(20) DEFAULT 'completed' NOT NULL,  -- pending, completed, failed
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_export_history_file ON export_history(file_id);
CREATE INDEX IF NOT EXISTS idx_export_history_user ON export_history(user_id);
CREATE INDEX IF NOT EXISTS idx_export_history_created ON export_history(created_at);
CREATE INDEX IF NOT EXISTS idx_export_history_format ON export_history(export_format);
CREATE INDEX IF NOT EXISTS idx_export_history_status ON export_history(status);
CREATE INDEX IF NOT EXISTS idx_export_history_expires ON export_history(expires_at);

-- Add comment
COMMENT ON TABLE export_history IS 'Tracks all export operations for diagrams with full history';
COMMENT ON COLUMN export_history.export_settings IS 'JSON object containing resolution, quality, background, etc.';
COMMENT ON COLUMN export_history.expires_at IS 'When the exported file expires and can be cleaned up';
