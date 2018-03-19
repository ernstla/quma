DB_NAME = 'quma_test_db'
DB_USER = 'quma_test_user'
DB_PASS = 'quma_test_password'
DSN = f'dbname={DB_NAME} user={DB_USER} password={DB_PASS}'
SQLITE_URI = 'sqlite:////tmp/quma.sqlite'
PG_URI = f'postgresql://{DB_USER}:{DB_PASS}@/{DB_NAME}'
PG_POOL_URI = f'postgresql+pool://{DB_USER}:{DB_PASS}@/{DB_NAME}'
MYSQL_URI = f'mysql://{DB_USER}:{DB_PASS}@/{DB_NAME}'

DROP_USERS = 'DROP TABLE IF EXISTS users;'
CREATE_USERS = ("""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    email VARCHAR(128) NOT NULL,
    city VARCHAR(128) NOT NULL);
""")
INSERT_USERS = ("""
INSERT INTO
    users (name, email, city)
VALUES
    ('Hans Karl', 'hans.karl@example.com', 'Staffelbach'),
    ('Robert Fößel', 'robert.foessel@example.com', 'Oberhaid'),
    ('Franz Görtler', 'franz.goertler@example.com', 'Bamberg'),
    ('Emil Jäger', 'emil.jaeger@example.com', 'Nürnberg');
""")


def setup_pg_db():
    import psycopg2
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute(DROP_USERS)
    cur.execute(CREATE_USERS)
    cur.execute(INSERT_USERS)
    conn.commit()
    cur.close()
    conn.close()


def setup_mysql_db():
    import MySQLdb
    conn = MySQLdb.connect(db=DB_NAME, user=DB_USER, passwd=DB_PASS)
    cur = conn.cursor()
    cur.execute(DROP_USERS)
    cur.execute(CREATE_USERS)
    cur.execute(INSERT_USERS)
    conn.commit()
    cur.close()
    conn.close()
