-- Create export_presets table for feature #513
-- Feature #513: Export presets - save favorite settings

CREATE TABLE IF NOT EXISTS export_presets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    format VARCHAR(50) NOT NULL,  -- png, svg, pdf, json, md, html
    settings JSONB DEFAULT '{}',
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_export_format CHECK (format IN ('png', 'svg', 'pdf', 'json', 'md', 'html')),
    CONSTRAINT unique_preset_name_per_user UNIQUE (user_id, name)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_export_presets_user_id ON export_presets(user_id);
CREATE INDEX IF NOT EXISTS idx_export_presets_format ON export_presets(format);
CREATE INDEX IF NOT EXISTS idx_export_presets_default ON export_presets(user_id, format, is_default) WHERE is_default = true;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_export_presets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_export_presets_updated_at ON export_presets;
CREATE TRIGGER trigger_update_export_presets_updated_at
    BEFORE UPDATE ON export_presets
    FOR EACH ROW
    EXECUTE FUNCTION update_export_presets_updated_at();

COMMENT ON TABLE export_presets IS 'Saved export presets for quick reuse of favorite settings';
COMMENT ON COLUMN export_presets.settings IS 'JSONB containing export settings (width, height, quality, etc.)';
COMMENT ON COLUMN export_presets.is_default IS 'Whether this is the default preset for this format and user';
