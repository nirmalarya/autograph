-- Add compression fields to versions table
ALTER TABLE versions ADD COLUMN IF NOT EXISTS is_compressed BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE versions ADD COLUMN IF NOT EXISTS compressed_canvas_data TEXT;
ALTER TABLE versions ADD COLUMN IF NOT EXISTS compressed_note_content TEXT;
ALTER TABLE versions ADD COLUMN IF NOT EXISTS original_size BIGINT;
ALTER TABLE versions ADD COLUMN IF NOT EXISTS compressed_size BIGINT;
ALTER TABLE versions ADD COLUMN IF NOT EXISTS compression_ratio FLOAT;
ALTER TABLE versions ADD COLUMN IF NOT EXISTS compressed_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for compression queries
CREATE INDEX IF NOT EXISTS idx_versions_compressed ON versions(is_compressed);
CREATE INDEX IF NOT EXISTS idx_versions_created ON versions(created_at);

-- Add comment
COMMENT ON COLUMN versions.is_compressed IS 'Whether version content is gzip compressed';
COMMENT ON COLUMN versions.compressed_canvas_data IS 'Base64-encoded gzipped canvas_data';
COMMENT ON COLUMN versions.compressed_note_content IS 'Base64-encoded gzipped note_content';
COMMENT ON COLUMN versions.original_size IS 'Size before compression in bytes';
COMMENT ON COLUMN versions.compressed_size IS 'Size after compression in bytes';
COMMENT ON COLUMN versions.compression_ratio IS 'Compression ratio (compressed/original)';
