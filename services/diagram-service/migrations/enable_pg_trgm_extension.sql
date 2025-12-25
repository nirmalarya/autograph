-- Enable pg_trgm extension for fuzzy text search (typo tolerance)
-- This extension provides functions for determining the similarity of text based on trigram matching

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create GIN index on title column for faster fuzzy searches
CREATE INDEX IF NOT EXISTS idx_files_title_trgm ON files USING GIN (title gin_trgm_ops);

-- Create GIN index on note_content for faster fuzzy searches on notes
CREATE INDEX IF NOT EXISTS idx_files_note_content_trgm ON files USING GIN (note_content gin_trgm_ops);

-- Set default similarity threshold (0.3 = 30% similar, good for typo tolerance)
-- Can be adjusted per query using SET pg_trgm.similarity_threshold = value;
SELECT set_limit(0.3);
