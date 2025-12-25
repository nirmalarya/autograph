import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='autograph',
    user='autograph_user',
    password='autograph_dev_password'
)
print('Connected!')
conn.close()
