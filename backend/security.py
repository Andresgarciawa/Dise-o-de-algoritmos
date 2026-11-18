import hashlib, hmac, secrets

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()
    return f'{salt}${digest}'

def password_matches(password, stored):
    salt, expected = stored.split('$', 1)
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()
    return hmac.compare_digest(actual, expected)

def new_session():
    return secrets.token_urlsafe(32)
