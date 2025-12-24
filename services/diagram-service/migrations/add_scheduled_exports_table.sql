-- Migration: Add scheduled_exports table
-- Description: Track scheduled/recurring exports for diagrams
-- Date: 2025-12-24
-- Features: #508 (daily), #509 (weekly)

-- Create scheduled_exports table
CREATE TABLE IF NOT EXISTS scheduled_exports (
    id VARCHAR(36) PRIMARY KEY,
    file_id VARCHAR(36) NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL,  -- daily, weekly, monthly
    schedule_time TIME NOT NULL,  -- Time of day to run (e.g., 02:00:00)
    schedule_day_of_week INTEGER,  -- 0-6 for weekly (0=Monday)
    schedule_day_of_month INTEGER,  -- 1-31 for monthly
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Export configuration
    export_format VARCHAR(20) NOT NULL,  -- png, svg, pdf, json, md, html
    export_settings JSONB DEFAULT '{}',  -- Width, height, scale, quality, background, etc.
    
    -- Destination configuration
    destination_type VARCHAR(20) DEFAULT 'local',  -- local, s3, google_drive, dropbox
    destination_config JSONB DEFAULT '{}',  -- Bucket name, folder path, etc.
    
    -- Status and tracking
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT chk_schedule_type CHECK (schedule_type IN ('daily', 'weekly', 'monthly')),
    CONSTRAINT chk_export_format CHECK (export_format IN ('png', 'svg', 'pdf', 'json', 'md', 'html')),
    CONSTRAINT chk_destination_type CHECK (destination_type IN ('local', 's3', 'google_drive', 'dropbox'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_file ON scheduled_exports(file_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_user ON scheduled_exports(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_active ON scheduled_exports(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_next_run ON scheduled_exports(next_run_at) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_schedule_type ON scheduled_exports(schedule_type);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_scheduled_exports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_scheduled_exports_updated_at
    BEFORE UPDATE ON scheduled_exports
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduled_exports_updated_at();

-- Add comments
COMMENT ON TABLE scheduled_exports IS 'Stores configuration for scheduled/recurring diagram exports';
COMMENT ON COLUMN scheduled_exports.schedule_type IS 'Type of schedule: daily, weekly, or monthly';
COMMENT ON COLUMN scheduled_exports.schedule_time IS 'Time of day to run export (in user timezone)';
COMMENT ON COLUMN scheduled_exports.schedule_day_of_week IS 'Day of week for weekly exports (0=Monday, 6=Sunday)';
COMMENT ON COLUMN scheduled_exports.schedule_day_of_month IS 'Day of month for monthly exports (1-31)';
COMMENT ON COLUMN scheduled_exports.timezone IS 'User timezone for schedule calculation';
COMMENT ON COLUMN scheduled_exports.export_settings IS 'JSON object with export options (width, height, scale, quality, background)';
COMMENT ON COLUMN scheduled_exports.destination_config IS 'JSON object with destination-specific config (bucket, folder, credentials)';
COMMENT ON COLUMN scheduled_exports.next_run_at IS 'Calculated next execution time in UTC';
