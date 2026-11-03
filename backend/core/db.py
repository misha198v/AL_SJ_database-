from django.db import connection


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of dicts, one per row."""
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def fetch_table(sql, params=None):
    """Run a SELECT and return (column names, list of rows)."""
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        columns = [col[0] for col in cur.description]
        return columns, [list(row) for row in cur.fetchall()]
