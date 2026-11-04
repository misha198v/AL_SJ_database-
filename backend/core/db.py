from django.db import connections

def fetch_all(sql, params=None):
    with connections['alsj'].cursor() as cur:
        cur.execute(sql, params or [])
        names = [c[0] for c in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]

def fetch_table(sql, params=None):
    with connections['alsj'].cursor() as cur:
        cur.execute(sql, params or [])
        return [c[0] for c in cur.description], [list(row) for row in cur.fetchall()]
