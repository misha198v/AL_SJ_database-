from .db import fetch_all

def check_login(phone, password):
    if not phone or not password or len(phone) > 20 or len(password.encode('utf-8')) > 72:
        return None
    rows = fetch_all('SELECT * FROM public.app_authenticate(%s, %s)', [phone, password])
    return rows[0] if rows else None
