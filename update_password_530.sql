-- Update passwords for test users
UPDATE users SET password_hash = '$2b$12$Qrz/mckmjsNAaSZ/lcjJX.84ucH2OwLSn07G73bdmPONRaLA0tz3i'
WHERE email = 'admin530@test.com';

UPDATE users SET password_hash = '$2b$12$Qrz/mckmjsNAaSZ/lcjJX.84ucH2OwLSn07G73bdmPONRaLA0tz3i'
WHERE email = 'member530@test.com';

SELECT email, substring(password_hash, 1, 30) as hash_prefix FROM users WHERE email LIKE '%530%';
