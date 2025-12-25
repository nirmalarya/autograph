-- Fix icon table columns from TEXT[] to JSONB
ALTER TABLE icons
  DROP COLUMN tags,
  DROP COLUMN keywords;

ALTER TABLE icons
  ADD COLUMN tags JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN keywords JSONB DEFAULT '[]'::jsonb;

-- Recreate indexes
DROP INDEX IF EXISTS idx_icons_tags;
DROP INDEX IF EXISTS idx_icons_keywords;

CREATE INDEX idx_icons_tags ON icons USING GIN(tags);
CREATE INDEX idx_icons_keywords ON icons USING GIN(keywords);
