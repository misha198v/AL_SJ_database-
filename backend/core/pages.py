import csv

from django.db import connection
from django.http import Http404, HttpResponse
from django.shortcuts import render

from .db import fetch_all, fetch_table
from .decorators import role_required


def table_response(request, title, columns, rows):
    """Show a result as a page, or as a CSV download when the address ends in ?csv=1."""
    if request.GET.get('csv'):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title.lower().replace(' ', '_')
        writer = csv.writer(response)
        writer.writerow(columns)
        writer.writerows(rows)
        return response
    return render(request, 'core/table.html', {'title': title, 'columns': columns, 'rows': rows, 'count': len(rows)})


def simple_page(request, title, sql, params=None):
    columns, rows = fetch_table(sql, params)
    return table_response(request, title, columns, rows)


APPLICATIONS_SQL = """
SELECT a.application_id, c.full_name AS client, c.phone AS client_phone, ag.full_name AS agent,
       ps.stage_order AS stage_no, ps.stage_name AS stage, a.service_type, a.destination,
       a.preferred_travel_date AS travel_date, a.status, a.created_at
FROM applications a
JOIN users c            ON c.user_id   = a.client_id
JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
LEFT JOIN users ag      ON ag.user_id  = a.assigned_agent_id
"""


@role_required('Client')
def my_applications(request):
    rows = fetch_all(
        APPLICATIONS_SQL + " WHERE a.client_id = %s ORDER BY a.created_at DESC",
        [request.session['user']['id']],
    )
    return render(request, 'core/applications_list.html', {'title': 'My applications', 'rows': rows})


@role_required('Director', 'Secretary', 'Data Entry Staff', 'Field Agent')
def applications(request):
    user = request.session['user']
    if user['role'] == 'Field Agent':
        rows = fetch_all(APPLICATIONS_SQL + " WHERE a.assigned_agent_id = %s ORDER BY a.created_at DESC", [user['id']])
        return render(request, 'core/applications_list.html', {'title': 'Applications assigned to me', 'rows': rows})
    rows = fetch_all(APPLICATIONS_SQL + " ORDER BY a.created_at DESC")
    return render(request, 'core/applications_list.html', {'title': 'Applications', 'rows': rows})


@role_required('Director')
def transactions(request):
    sql = """
    SELECT p.initiated_at, c.full_name AS client, a.destination, p.amount, p.currency,
           p.payment_method, p.payer_phone, p.status, p.transaction_reference, p.completed_at
    FROM payments p
    JOIN applications a ON a.application_id = p.application_id
    JOIN users c        ON c.user_id = a.client_id"""
    params, title = [], 'Transactions'
    status = request.GET.get('status', '')
    if status in ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED'):
        sql += " WHERE p.status = %s"
        params.append(status)
        title += ' (%s)' % status
    return simple_page(request, title, sql + " ORDER BY p.initiated_at DESC", params)


@role_required('Director')
def employees(request):
    return simple_page(request, 'Employees and who they are assigned to', """
    SELECT s.employee_no, u.full_name, r.role_name AS role, u.phone, u.email, s.date_hired, u.is_active,
           count(a.application_id) FILTER (WHERE a.status = 'ACTIVE') AS active_applications,
           string_agg(DISTINCT c.full_name || ' (' || c.phone || ')', ', ') AS assigned_clients
    FROM staff_profiles s
    JOIN users u ON u.user_id = s.user_id
    JOIN roles r ON r.role_id = u.role_id
    LEFT JOIN applications a ON a.assigned_agent_id = u.user_id
    LEFT JOIN users c ON c.user_id = a.client_id
    GROUP BY s.employee_no, u.full_name, r.role_name, u.phone, u.email, s.date_hired, u.is_active
    ORDER BY s.employee_no""")


@role_required('Field Agent')
def my_clients(request):
    return simple_page(request, 'My clients', """
    SELECT c.full_name AS client, c.phone, c.email, cp.address, a.destination, a.service_type,
           ps.stage_name AS stage, a.status
    FROM applications a
    JOIN users c ON c.user_id = a.client_id
    LEFT JOIN client_profiles cp ON cp.user_id = c.user_id
    JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
    WHERE a.assigned_agent_id = %s
    ORDER BY c.full_name""", [request.session['user']['id']])


@role_required('Director')
def users_list(request):
    return simple_page(request, 'All users', """
    SELECT u.full_name, u.phone, u.email, r.role_name AS role, u.is_active, u.created_at
    FROM users u JOIN roles r ON r.role_id = u.role_id ORDER BY r.role_name, u.full_name""")


@role_required('Director', 'Secretary')
def clients(request):
    return simple_page(request, 'Clients', """
    SELECT u.full_name, u.phone, cp.national_id, cp.date_of_birth, cp.address,
           cp.preferred_language AS language, u.is_active, u.created_at
    FROM client_profiles cp JOIN users u ON u.user_id = cp.user_id
    ORDER BY u.full_name""")


@role_required('Director', 'Field Agent', 'Data Entry Staff')
def documents(request):
    return simple_page(request, 'Documents', """
    SELECT d.uploaded_at, c.full_name AS client, a.destination, d.document_type, d.file_path,
           d.file_size_bytes AS bytes, d.verification_status AS status, v.full_name AS verified_by,
           d.verified_at, d.rejection_reason
    FROM documents d
    JOIN applications a ON a.application_id = d.application_id
    JOIN users c        ON c.user_id = a.client_id
    LEFT JOIN users v   ON v.user_id = d.verified_by
    ORDER BY d.uploaded_at DESC""")


@role_required('Director', 'Secretary')
def appointments(request):
    rows = fetch_all("""
    SELECT s.schedule_id, s.scheduled_datetime AS scheduled, c.full_name AS client, st.full_name AS staff_member,
           s.appointment_type AS type, s.status
    FROM schedule_records s
    JOIN users c  ON c.user_id  = s.client_id
    JOIN users st ON st.user_id = s.staff_id
    ORDER BY s.scheduled_datetime DESC""")
    return render(request, 'core/appointments.html', {'rows': rows})


@role_required('Director')
def notifications(request):
    return simple_page(request, 'Notifications', """
    SELECT n.notification_id AS no, u.full_name AS recipient, n.channel, n.message, n.status,
           a.destination AS application
    FROM notifications n
    JOIN users u ON u.user_id = n.user_id
    LEFT JOIN applications a ON a.application_id = n.application_id
    ORDER BY n.notification_id DESC""")


@role_required('Director')
def stage_history(request):
    return simple_page(request, 'Stage history', """
    SELECT h.changed_at, c.full_name AS client, a.destination,
           fs.stage_name AS from_stage, ts.stage_name AS to_stage, COALESCE(u.full_name, 'system') AS changed_by
    FROM stage_history h
    JOIN applications a    ON a.application_id = h.application_id
    JOIN users c           ON c.user_id = a.client_id
    LEFT JOIN pipeline_stages fs ON fs.stage_id = h.from_stage_id
    JOIN pipeline_stages ts      ON ts.stage_id = h.to_stage_id
    LEFT JOIN users u      ON u.user_id = h.changed_by
    ORDER BY h.changed_at DESC""")


@role_required('Director')
def audit(request):
    return simple_page(request, 'Audit log', """
    SELECT l.created_at, COALESCE(u.full_name, 'system') AS actor, l.action, l.entity_type, l.entity_id, l.ip_address
    FROM audit_logs l LEFT JOIN users u ON u.user_id = l.user_id
    ORDER BY l.created_at DESC""")


@role_required('Director')
def revenue_report(request):
    return simple_page(request, 'Revenue by month and method', REVENUE_SQL)


REVENUE_SQL = """
SELECT date_trunc('month', completed_at AT TIME ZONE 'Africa/Kampala')::date AS month,
       payment_method, currency, count(*) AS payments, sum(amount) AS collected,
       COALESCE(sum(amount) FILTER (WHERE status = 'REFUNDED'), 0)  AS refunded,
       COALESCE(sum(amount) FILTER (WHERE status = 'COMPLETED'), 0) AS net
FROM payments
WHERE status IN ('COMPLETED', 'REFUNDED')
GROUP BY 1, payment_method, currency
ORDER BY 1 DESC, payment_method"""


@role_required('Director')
def dashboard(request):
    a = fetch_all("""SELECT count(*) AS total,
        count(*) FILTER (WHERE status = 'ACTIVE') AS active,
        count(*) FILTER (WHERE status IN ('CLOSED', 'ARCHIVED')) AS finished,
        count(*) FILTER (WHERE status = 'CANCELLED') AS cancelled FROM applications""")[0]
    p = fetch_all("""SELECT COALESCE(sum(amount) FILTER (WHERE status = 'COMPLETED' AND currency = 'UGX'), 0) AS net,
        count(*) FILTER (WHERE status = 'PENDING') AS pending,
        count(*) FILTER (WHERE status = 'FAILED') AS failed,
        count(*) FILTER (WHERE status = 'REFUNDED') AS refunded FROM payments""")[0]
    d = fetch_all("SELECT count(*) FILTER (WHERE verification_status = 'PENDING') AS pending FROM documents")[0]
    ap = fetch_all("SELECT count(*) AS n FROM schedule_records WHERE status = 'UPCOMING'")[0]
    people = fetch_all("""SELECT (SELECT count(*) FROM client_profiles) AS clients,
                                 (SELECT count(*) FROM staff_profiles) AS employees""")[0]
    kpis = [
        ('Applications', a['total']), ('Active', a['active']), ('Closed or archived', a['finished']),
        ('Cancelled', a['cancelled']), ('Clients', people['clients']), ('Employees', people['employees']),
        ('Net revenue (UGX)', '{:,.0f}'.format(p['net'])), ('Pending payments', p['pending']),
        ('Failed payments', p['failed']), ('Refunded payments', p['refunded']),
        ('Documents to review', d['pending']), ('Upcoming appointments', ap['n']),
    ]
    stages = fetch_all("""SELECT ps.stage_order, ps.stage_name, count(a.application_id) AS applications
        FROM pipeline_stages ps LEFT JOIN applications a ON a.current_stage_id = ps.stage_id
        GROUP BY ps.stage_order, ps.stage_name ORDER BY ps.stage_order""")
    biggest = max([s['applications'] for s in stages] + [1])
    for s in stages:
        s['pct'] = round(100 * s['applications'] / biggest)
    queries = [
        ('Applications by service type', """SELECT service_type, count(*) AS applications FROM applications
            GROUP BY service_type ORDER BY 2 DESC"""),
        ('Field Agent workload', """SELECT u.full_name AS agent,
                count(*) FILTER (WHERE a.status = 'ACTIVE') AS active_applications
            FROM users u JOIN roles r ON r.role_id = u.role_id
            LEFT JOIN applications a ON a.assigned_agent_id = u.user_id
            WHERE r.role_name = 'Field Agent' GROUP BY u.full_name ORDER BY 2 DESC"""),
        ('Revenue by month and method', REVENUE_SQL),
        ('Document rejection rate', """SELECT document_type, count(*) AS total,
                count(*) FILTER (WHERE verification_status = 'REJECTED') AS rejected,
                round(100.0 * count(*) FILTER (WHERE verification_status = 'REJECTED') / count(*), 1) AS rejected_percent
            FROM documents GROUP BY document_type ORDER BY 1"""),
            ('Notification delivery by channel', """SELECT channel,
                count(*) FILTER (WHERE status = 'SENT') AS sent,
                count(*) FILTER (WHERE status = 'FAILED') AS failed
            FROM notifications GROUP BY channel ORDER BY 1"""),
    ]
    sections = []
    for title, sql in queries:
        columns, rows = fetch_table(sql)
        sections.append({'title': title, 'columns': columns, 'rows': rows})
    return render(request, 'core/dashboard.html', {'kpis': kpis, 'stages': stages, 'sections': sections})


# ---- "All tables": every table in the design, read-only, with a CSV download ----
TABLES = ['roles', 'pipeline_stages', 'users', 'client_profiles', 'staff_profiles', 'applications',
          'documents', 'payments', 'stage_history', 'schedule_records', 'notifications', 'audit_logs']
HIDDEN_COLUMNS = {'password_hash'}


@role_required('Director')
def data_index(request):
    tables = [{'name': t, 'count': fetch_all('SELECT count(*) AS n FROM %s' % t)[0]['n']} for t in TABLES]
    return render(request, 'core/data_index.html', {'tables': tables})


@role_required('Director')
def data_table(request, table):
    if table not in TABLES:
        raise Http404
    names = [c['column_name'] for c in fetch_all(
        """SELECT column_name FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position""", [table])]
    shown = [c for c in names if c not in HIDDEN_COLUMNS]
    quoted = ', '.join(connection.ops.quote_name(c) for c in shown)
    columns, rows = fetch_table('SELECT %s FROM %s ORDER BY 1 LIMIT 500' % (quoted, table))
    return table_response(request, table, columns, rows)
