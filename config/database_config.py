import os
import psycopg2

def load_database_config():

    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 5432))
    username = os.getenv('DB_USERNAME', 'postgres')
    password = os.getenv('DB_PASSWORD', '123456789')
    dbname = os.getenv('DB_NAME', 'uq_eventible')

    return {
        'host': host,
        'port': port,
        'username': username,
        'password': password,
        'dbname': dbname
    }

def database_connection():
    config = load_database_config()
    psql_info = (
        f"host={config['host']} port={config['port']} user={'postgres'} "
        f"password={config['password']} dbname={config['dbname']} "
        f"options='-c client_encoding=UTF8'"
    )
    print('DB_info:',psql_info)
    try:
        conn = psycopg2.connect(psql_info)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        return conn
    except psycopg2.Error as err:
        print(f"Error connecting to the database: {err}")
        return None