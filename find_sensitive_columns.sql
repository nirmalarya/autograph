SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
    AND (column_name LIKE '%secret%'
         OR column_name LIKE '%key%'
         OR column_name LIKE '%token%'
         OR column_name LIKE '%encrypted%'
         OR data_type = 'bytea')
ORDER BY table_name, column_name;
