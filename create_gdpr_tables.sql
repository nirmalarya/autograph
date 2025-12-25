-- GDPR Compliance Tables

-- User Consents Table
CREATE TABLE IF NOT EXISTS user_consents (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    consent_version VARCHAR(20),
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),
    consent_method VARCHAR(50),
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    withdrawn_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_user_consents_user ON user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type);
CREATE INDEX IF NOT EXISTS idx_user_consents_created ON user_consents(created_at);

-- Data Processing Activities Table
CREATE TABLE IF NOT EXISTS data_processing_activities (
    id VARCHAR(36) PRIMARY KEY,
    activity_name VARCHAR(255) NOT NULL,
    activity_description TEXT NOT NULL,
    purpose TEXT NOT NULL,
    legal_basis VARCHAR(100) NOT NULL,
    data_categories JSONB NOT NULL,
    data_subjects JSONB NOT NULL,
    recipients JSONB,
    third_country_transfers BOOLEAN DEFAULT FALSE,
    third_countries JSONB,
    safeguards TEXT,
    retention_period VARCHAR(255),
    security_measures TEXT,
    data_controller VARCHAR(255),
    data_protection_officer VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_processing_activities_active ON data_processing_activities(is_active);
CREATE INDEX IF NOT EXISTS idx_data_processing_activities_legal_basis ON data_processing_activities(legal_basis);

-- Data Breach Logs Table
CREATE TABLE IF NOT EXISTS data_breach_logs (
    id VARCHAR(36) PRIMARY KEY,
    breach_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    affected_users_count INTEGER DEFAULT 0,
    affected_data_categories JSONB,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    contained_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    authority_notified BOOLEAN DEFAULT FALSE,
    authority_notified_at TIMESTAMP WITH TIME ZONE,
    users_notified BOOLEAN DEFAULT FALSE,
    users_notified_at TIMESTAMP WITH TIME ZONE,
    likely_consequences TEXT,
    measures_taken TEXT,
    measures_proposed TEXT,
    reported_by VARCHAR(255),
    dpo_notified BOOLEAN DEFAULT FALSE,
    dpo_notified_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'open',
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_breach_logs_severity ON data_breach_logs(severity);
CREATE INDEX IF NOT EXISTS idx_data_breach_logs_status ON data_breach_logs(status);
CREATE INDEX IF NOT EXISTS idx_data_breach_logs_detected ON data_breach_logs(detected_at);

-- Data Deletion Requests Table
CREATE TABLE IF NOT EXISTS data_deletion_requests (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255) NOT NULL,
    request_reason TEXT,
    verification_token VARCHAR(255) UNIQUE,
    verified_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    tables_processed JSONB,
    records_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_deletion_requests_user ON data_deletion_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_data_deletion_requests_email ON data_deletion_requests(user_email);
CREATE INDEX IF NOT EXISTS idx_data_deletion_requests_status ON data_deletion_requests(status);
CREATE INDEX IF NOT EXISTS idx_data_deletion_requests_token ON data_deletion_requests(verification_token);
