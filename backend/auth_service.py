import hashlib

try:
    from .security import password_matches, new_session
    from .mysql_database import connection
except ImportError:
    from security import password_matches, new_session
    from mysql_database import connection

USERS = {}
SESSIONS = {}

def configure(users, sessions):
    USERS.clear(); USERS.update(users); SESSIONS.clear(); SESSIONS.update(sessions)

def public_user(user):
    return {key: user[key] for key in ('id', 'username', 'name', 'role', 'location_id', 'active')}

def login(username, password):
    user = USERS.get(username.lower())
    if not user or not user['active']:
        return None
    try:
        if not password_matches(password, user['password']):
            return None
    except (AttributeError, ValueError):
        return None
    session = new_session()
    db = connection()
    try:
        cur = db.cursor()
        cur.execute('DELETE FROM sessions WHERE user_id=%s OR expires_at<=NOW()', (user['id'],))
        cur.execute('INSERT INTO sessions(token,user_id,expires_at) VALUES(%s,%s,DATE_ADD(NOW(),INTERVAL 30 MINUTE))',
                    (hashlib.sha256(session.encode('utf-8')).hexdigest(), user['id']))
        cur.execute("INSERT INTO audit_log(user_id,action,entity,entity_id) VALUES(%s,'Inicio de sesion','users',%s)",
                    (user['id'], user['id']))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    SESSIONS[session] = user['username']
    return session, public_user(user)

def user_from_session(session):
    if not session:
        return None
    token_hash = hashlib.sha256(session.encode('utf-8')).hexdigest()
    db = connection()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("""SELECT u.id,u.username,u.full_name name,r.name role,u.location_id,u.active,
                       u.password_hash password,s.expires_at
                       FROM sessions s JOIN users u ON u.id=s.user_id
                       JOIN roles r ON r.id=u.role_id
                       WHERE s.token=%s AND s.expires_at>NOW() AND u.active=TRUE""", (token_hash,))
        user = cur.fetchone()
        if not user:
            cur.execute('DELETE FROM sessions WHERE token=%s OR expires_at<=NOW()', (token_hash,))
            db.commit()
            SESSIONS.pop(session, None)
            return None
        cur.execute('UPDATE sessions SET expires_at=DATE_ADD(NOW(),INTERVAL 30 MINUTE) WHERE token=%s', (token_hash,))
        db.commit()
        USERS[user['username']] = {key: value for key, value in user.items() if key != 'expires_at'}
        SESSIONS[session] = user['username']
        return USERS[user['username']]
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def logout(session):
    if not session:
        return
    username = SESSIONS.pop(session, None)
    user = USERS.get(username)
    token_hash = hashlib.sha256(session.encode('utf-8')).hexdigest()
    db = connection()
    try:
        cur = db.cursor()
        cur.execute('DELETE FROM sessions WHERE token=%s', (token_hash,))
        if user:
            cur.execute("INSERT INTO audit_log(user_id,action,entity,entity_id) VALUES(%s,'Cierre de sesion','users',%s)",
                        (user['id'], user['id']))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
