import bcrypt
from .db import fetch_all


def check_login(phone, password):
    """Return the user (a dict) if phone and password are right, otherwise None."""
    rows = fetch_all(
        """SELECT u.user_id, u.full_name, u.password_hash, u.is_active, r.role_name
           FROM users u JOIN roles r ON r.role_id = u.role_id
           WHERE u.phone = %s""",
        [phone],
    )
    if not rows:
        return None
    user = rows[0]
    if not user['is_active']:
        return None
    try:
        if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return user
    except ValueError:
        # the stored value is not a bcrypt hash (an older user): treat it as a wrong password
        return None
    return None


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
