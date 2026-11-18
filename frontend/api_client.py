"""Cliente HTTP del frontend hacia el backend de BarWise."""
from http.client import HTTPConnection
import json
import os

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

BACKEND_HOST = os.getenv('BARWISE_BACKEND_HOST', '127.0.0.1')
BACKEND_PORT = int(os.getenv('BARWISE_BACKEND_PORT', '5001'))


def request(path, method='GET', body=None, cookie='', location_id=None):
    connection = HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=3)
    headers = {'Content-Type': 'application/json'}
    if cookie:
        headers['Cookie'] = cookie
    if location_id is not None:
        headers['X-Location-ID'] = str(location_id)
    payload = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        connection.request(method, path, payload, headers)
        response = connection.getresponse()
        raw = response.read().decode('utf-8')
        data = json.loads(raw) if raw else {}
        return response.status, data, response.getheader('Set-Cookie', '')
    except OSError as error:
        return 503, {'error': f'No se pudo comunicar con el backend: {error}'}, ''
    finally:
        connection.close()


def download(path, cookie='', location_id=None):
    connection = HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=10)
    headers = {}
    if cookie:
        headers['Cookie'] = cookie
    if location_id is not None:
        headers['X-Location-ID'] = str(location_id)
    try:
        connection.request('GET', path, headers=headers)
        response = connection.getresponse()
        content = response.read()
        if response.status >= 400:
            data = json.loads(content.decode('utf-8')) if content else {}
            return response.status, data, response.getheader('Content-Type', '')
        return response.status, content, response.getheader('Content-Type', '')
    except OSError as error:
        return 503, {'error': f'No se pudo comunicar con el backend: {error}'}, ''
    finally:
        connection.close()
