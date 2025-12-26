-- User ID: d82c3b0b-ae5c-4be7-8999-0ad0fac5bf47
-- Email: thumbnail_test_460@example.com
-- Password: SecurePass123!

INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
VALUES ('d82c3b0b-ae5c-4be7-8999-0ad0fac5bf47', 'thumbnail_test_460@example.com', '$2b$12$QzLNFBDL90GY4DEKKwvS6ep.13VN4t4xEx.gnHJYv.aDxOyV1RnXW', 'Thumbnail Test User 460', true, true, 'user', NOW(), NOW());
