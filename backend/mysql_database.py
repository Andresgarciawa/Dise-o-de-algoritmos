"""Conexion opcional a MySQL. Las credenciales se leen del entorno."""
import os

_POOL = None

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

load_env()

def connection():
    global _POOL
    try:
        from mysql.connector.pooling import MySQLConnectionPool
    except ImportError as error:
        raise RuntimeError('Instala mysql-connector-python para activar MySQL') from error
    if _POOL is None:
        _POOL = MySQLConnectionPool(pool_name='barwise_pool', pool_size=5, pool_reset_session=True,
                                    host=os.getenv('BARWISE_DB_HOST', '127.0.0.1'),
                                    port=int(os.getenv('BARWISE_DB_PORT', '3306')),
                                    user=os.getenv('BARWISE_DB_USER', 'root'),
                                    password=os.getenv('BARWISE_DB_PASSWORD', ''),
                                    database=os.getenv('BARWISE_DB_NAME', 'barwise'))
    return _POOL.get_connection()

def check_connection():
    db = connection()
    try:
        cursor = db.cursor(); cursor.execute('SELECT 1'); return cursor.fetchone()[0] == 1
    finally:
        db.close()
