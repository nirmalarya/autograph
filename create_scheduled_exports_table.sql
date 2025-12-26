-- Create scheduled_exports table for features #507-508
-- Feature #507: Scheduled exports - daily
-- Feature #508: Scheduled exports - weekly

CREATE TABLE IF NOT EXISTS scheduled_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL,  -- daily, weekly, monthly
    schedule_time TIME NOT NULL,  -- HH:MM:SS
    schedule_day_of_week INTEGER,  -- 0-6 for weekly (0=Monday, 6=Sunday)
    schedule_day_of_month INTEGER,  -- 1-31 for monthly
    timezone VARCHAR(100) DEFAULT 'UTC',
    export_format VARCHAR(50) NOT NULL,  -- png, svg, pdf, json, md, html
    export_settings JSONB DEFAULT '{}',
    destination_type VARCHAR(50) DEFAULT 'local',  -- local, s3, google_drive, dropbox
    destination_config JSONB DEFAULT '{}',
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, disabled, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_schedule_type CHECK (schedule_type IN ('daily', 'weekly', 'monthly')),
    CONSTRAINT valid_export_format CHECK (export_format IN ('png', 'svg', 'pdf', 'json', 'md', 'html')),
    CONSTRAINT valid_destination_type CHECK (destination_type IN ('local', 's3', 'google_drive', 'dropbox')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'disabled', 'failed')),
    CONSTRAINT valid_day_of_week CHECK (schedule_day_of_week IS NULL OR (schedule_day_of_week >= 0 AND schedule_day_of_week <= 6)),
    CONSTRAINT valid_day_of_month CHECK (schedule_day_of_month IS NULL OR (schedule_day_of_month >= 1 AND schedule_day_of_month <= 31))
);

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_user_id ON scheduled_exports(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_file_id ON scheduled_exports(file_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_next_run ON scheduled_exports(next_run) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_scheduled_exports_status ON scheduled_exports(status);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_scheduled_exports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_scheduled_exports_updated_at ON scheduled_exports;
CREATE TRIGGER trigger_update_scheduled_exports_updated_at
    BEFORE UPDATE ON scheduled_exports
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduled_exports_updated_at();

COMMENT ON TABLE scheduled_exports IS 'Scheduled exports for automatic diagram exports';
COMMENT ON COLUMN scheduled_exports.schedule_type IS 'daily, weekly, or monthly';
COMMENT ON COLUMN scheduled_exports.schedule_day_of_week IS '0=Monday, 1=Tuesday, ..., 6=Sunday';
COMMENT ON COLUMN scheduled_exports.schedule_day_of_month IS 'Day of month (1-31) for monthly schedules';
COMMENT ON COLUMN scheduled_exports.next_run IS 'Next scheduled execution time';
COMMENT ON COLUMN scheduled_exports.last_run IS 'Last execution time';
COMMENT ON COLUMN scheduled_exports.status IS 'active, paused, disabled, or failed';
