-- Migration: Add Icon Library Tables
-- Features: 205-209 (Icon library with 3000+ icons, search, categories, recent, favorites)
-- Date: 2025-12-25

-- ============================================================================
-- 1. Icon Categories Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS icon_categories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL, -- 'simple-icons', 'aws', 'azure', 'gcp'
    description TEXT,
    icon_count INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_icon_categories_provider ON icon_categories(provider);
CREATE INDEX idx_icon_categories_slug ON icon_categories(slug);

-- ============================================================================
-- 2. Icons Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS icons (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    title VARCHAR(200) NOT NULL, -- Display title
    category_id VARCHAR(36) REFERENCES icon_categories(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL, -- 'simple-icons', 'aws', 'azure', 'gcp'

    -- Icon data
    svg_data TEXT NOT NULL, -- SVG content
    svg_url VARCHAR(512), -- Optional external URL

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb, -- Array of search tags
    keywords JSONB DEFAULT '[]'::jsonb, -- Additional searchable keywords
    hex_color VARCHAR(7), -- Brand/default color (e.g., '#FF5733')

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_icons_slug ON icons(slug);
CREATE INDEX idx_icons_name ON icons(name);
CREATE INDEX idx_icons_provider ON icons(provider);
CREATE INDEX idx_icons_category ON icons(category_id);
CREATE INDEX idx_icons_usage_count ON icons(usage_count DESC);
CREATE INDEX idx_icons_tags ON icons USING GIN(tags); -- For array search
CREATE INDEX idx_icons_keywords ON icons USING GIN(keywords);

-- Full-text search will be handled via application-level fuzzy matching
-- Using PostgreSQL's trigram similarity extension would require additional setup
-- We'll use the tags and keywords GIN indexes for efficient searching

-- ============================================================================
-- 3. User Recent Icons Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_recent_icons (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    icon_id VARCHAR(36) NOT NULL REFERENCES icons(id) ON DELETE CASCADE,

    -- Tracking
    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1,

    UNIQUE(user_id, icon_id)
);

CREATE INDEX idx_user_recent_icons_user ON user_recent_icons(user_id, used_at DESC);
CREATE INDEX idx_user_recent_icons_icon ON user_recent_icons(icon_id);

-- ============================================================================
-- 4. User Favorite Icons Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_favorite_icons (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    icon_id VARCHAR(36) NOT NULL REFERENCES icons(id) ON DELETE CASCADE,

    -- Metadata
    note TEXT, -- Optional user note
    sort_order INTEGER DEFAULT 0, -- User can reorder favorites

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, icon_id)
);

CREATE INDEX idx_user_favorite_icons_user ON user_favorite_icons(user_id, sort_order);
CREATE INDEX idx_user_favorite_icons_icon ON user_favorite_icons(icon_id);

-- ============================================================================
-- 5. Triggers for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_icon_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER icon_categories_updated_at
    BEFORE UPDATE ON icon_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_icon_categories_updated_at();

CREATE OR REPLACE FUNCTION update_icons_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER icons_updated_at
    BEFORE UPDATE ON icons
    FOR EACH ROW
    EXECUTE FUNCTION update_icons_updated_at();

-- ============================================================================
-- 6. Function to update category icon count
-- ============================================================================

CREATE OR REPLACE FUNCTION update_category_icon_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update count when icon is added/removed/changed
    IF TG_OP = 'INSERT' THEN
        UPDATE icon_categories
        SET icon_count = icon_count + 1
        WHERE id = NEW.category_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE icon_categories
        SET icon_count = icon_count - 1
        WHERE id = OLD.category_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.category_id != NEW.category_id THEN
        UPDATE icon_categories
        SET icon_count = icon_count - 1
        WHERE id = OLD.category_id;
        UPDATE icon_categories
        SET icon_count = icon_count + 1
        WHERE id = NEW.category_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER icons_category_count
    AFTER INSERT OR UPDATE OR DELETE ON icons
    FOR EACH ROW
    EXECUTE FUNCTION update_category_icon_count();

-- ============================================================================
-- 7. Sample Data - Icon Categories
-- ============================================================================

INSERT INTO icon_categories (id, name, slug, provider, description, sort_order) VALUES
    (gen_random_uuid()::text, 'Brand Icons', 'brand-icons', 'simple-icons', '2800+ brand and company icons from SimpleIcons', 1),
    (gen_random_uuid()::text, 'AWS Services', 'aws-services', 'aws', 'Amazon Web Services architecture icons', 2),
    (gen_random_uuid()::text, 'AWS Compute', 'aws-compute', 'aws', 'AWS compute and container services', 3),
    (gen_random_uuid()::text, 'AWS Storage', 'aws-storage', 'aws', 'AWS storage services (S3, EBS, etc.)', 4),
    (gen_random_uuid()::text, 'AWS Database', 'aws-database', 'aws', 'AWS database services (RDS, DynamoDB, etc.)', 5),
    (gen_random_uuid()::text, 'Azure Services', 'azure-services', 'azure', 'Microsoft Azure cloud services', 6),
    (gen_random_uuid()::text, 'Azure Compute', 'azure-compute', 'azure', 'Azure compute services', 7),
    (gen_random_uuid()::text, 'Azure Data', 'azure-data', 'azure', 'Azure data and storage services', 8),
    (gen_random_uuid()::text, 'GCP Services', 'gcp-services', 'gcp', 'Google Cloud Platform services', 9),
    (gen_random_uuid()::text, 'GCP Compute', 'gcp-compute', 'gcp', 'GCP compute and container services', 10),
    (gen_random_uuid()::text, 'GCP Storage', 'gcp-storage', 'gcp', 'GCP storage services', 11),
    (gen_random_uuid()::text, 'GCP Data', 'gcp-data', 'gcp', 'GCP data and analytics services', 12)
ON CONFLICT (slug) DO NOTHING;

COMMENT ON TABLE icon_categories IS 'Categories for organizing icon library (AWS, Azure, GCP, SimpleIcons)';
COMMENT ON TABLE icons IS 'Icon library with 3000+ icons from various providers';
COMMENT ON TABLE user_recent_icons IS 'Tracks recently used icons per user for quick access';
COMMENT ON TABLE user_favorite_icons IS 'User-favorited icons for quick access';
