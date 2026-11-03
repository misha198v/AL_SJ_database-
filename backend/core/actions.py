"""All the forms that WRITE to the database. Every one runs in a transaction and shows the
database's own message in plain words if it refuses something (a check, a trigger, a key)."""
import uuid

from django.contrib import messages
from django.core.files.storage import default_storage
from django.db import DatabaseError, IntegrityError, ProgrammingError, connection, transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render

from .auth import hash_password
from .db import fetch_all, fetch_table
from .decorators import role_required


class FormError(Exception):
    """A problem with what the user typed (shown on the form)."""


def options(sql, params=None):
    return [(str(r[0]), r[1]) for r in fetch_table(sql, params)[1]]


def audit(request, cur, action, entity_type, entity_id):
    cur.execute(
        """INSERT INTO audit_logs (user_id, action, entity_type, entity_id, ip_address)
           VALUES (%s, %s, %s, %s, %s)""",
        [request.session['user']['id'], action, entity_type, str(entity_id), request.META.get('REMOTE_ADDR')],
    )


def form_page(request, title, fields, handler, success, submit='Save', multipart=False):
    error, values = '', {}
    if request.method == 'POST':
        values = request.POST
        try:
            with transaction.atomic(), connection.cursor() as cur:
                result = handler(cur, request.POST, request.FILES)
            messages.success(request, '%s: saved.' % title)
            return redirect(success(result) if callable(success) else success)
        except FormError as exc:
            error = str(exc)
        except IntegrityError:
            error = 'That value already exists (for example a phone number, national ID or employee number).'
        except DatabaseError as exc:
            error = 'The database refused this: %s' % str(exc).strip().splitlines()[0]
    return render(request, 'core/form.html', {'title': title, 'fields': fields, 'values': values,
                                              'error': error, 'submit': submit, 'multipart': multipart})


def need(data, *names):
    for n in names:
        if not data.get(n, '').strip():
            raise FormError('Please fill in: %s.' % n.replace('_', ' '))


def create_user(cur, data, role_name=None, role_id=None):
    need(data, 'full_name', 'phone')
    if len(data.get('password', '')) < 8:
        raise FormError('Use a password of at least 8 characters.')
    cur.execute(
        """INSERT INTO users (full_name, email, phone, password_hash, role_id)
           VALUES (%s, %s, %s, %s, COALESCE(%s::smallint, (SELECT role_id FROM roles WHERE role_name = %s)))
           RETURNING user_id""",
        [data['full_name'].strip(), data.get('email', '').strip() or None, data['phone'].strip(),
         hash_password(data['password']), role_id, role_name],
    )
    return cur.fetchone()[0]


def create_client(cur, data):
    need(data, 'national_id')
    user_id = create_user(cur, data, role_name='Client')
    cur.execute(
        """INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language)
           VALUES (%s, %s, %s, %s, 'EN')""",
        [user_id, data['national_id'].strip(), data.get('date_of_birth') or None, data.get('address', '').strip() or None],
    )
    return user_id


CLIENT_FIELDS = [
    ('full_name', 'Full name', 'text', None, True), ('phone', 'Phone', 'text', None, True),
    ('password', 'Password (at least 8 characters)', 'password', None, True),
    ('national_id', 'National ID', 'text', None, True), ('date_of_birth', 'Date of birth', 'date', None, False),
    ('address', 'Address', 'text', None, False),
]


@role_required('Director', 'Secretary')
def add_client(request):
    return form_page(request, 'Add a client', CLIENT_FIELDS, lambda cur, d, f: create_client(cur, d), 'clients')


@role_required('Director')
def add_employee(request):
    roles = options("SELECT role_id, role_name FROM roles WHERE role_name <> 'Client' ORDER BY role_name")
    fields = [
        ('full_name', 'Full name', 'text', None, True), ('phone', 'Phone', 'text', None, True),
        ('email', 'Email', 'text', None, False), ('password', 'Password (at least 8 characters)', 'password', None, True),
        ('role_id', 'Role', 'select', roles, True), ('employee_no', 'Employee number', 'text', None, True),
        ('date_hired', 'Date hired', 'date', None, False),
    ]

    def handler(cur, d, f):
        need(d, 'role_id', 'employee_no')
        user_id = create_user(cur, d, role_id=int(d['role_id']))
        cur.execute("INSERT INTO staff_profiles (user_id, employee_no, date_hired) VALUES (%s, %s, COALESCE(%s::date, CURRENT_DATE))",
                    [user_id, d['employee_no'].strip(), d.get('date_hired') or None])
        audit(request, cur, 'EMPLOYEE_ADDED', 'users', user_id)
        return user_id
    return form_page(request, 'Add an employee', fields, handler, 'employees')


def can_see(user, app):
    role = user['role']
    if role == 'Client':
        return str(app['client_id']) == user['id']
    if role == 'Field Agent':
        return str(app['assigned_agent_id']) == user['id']
    return role in ('Director', 'Secretary', 'Data Entry Staff')


@role_required('Client', 'Director', 'Secretary')
def new_application(request):
    user = request.session['user']
    staff = user['role'] != 'Client'
    fields = []
    if staff:
        fields.append(('client_id', 'Client', 'select', options(
            "SELECT user_id, full_name || ' (' || phone || ')' FROM users u WHERE EXISTS (SELECT 1 FROM client_profiles c WHERE c.user_id = u.user_id) ORDER BY full_name"), True))
    fields += [
        ('service_type', 'Service', 'select', [('LABOUR_MIGRATION', 'Labour migration'), ('DOMESTIC_TOURISM', 'Domestic tourism')], True),
        ('destination', 'Destination', 'text', None, True), ('travel_purpose', 'Purpose', 'text', None, False),
        ('preferred_travel_date', 'Preferred travel date', 'date', None, True),
    ]
    if staff:
        fields.append(('agent_id', 'Assign a Field Agent (optional)', 'select', [('', '(none yet)')] + options(
            "SELECT u.user_id, u.full_name FROM users u JOIN roles r ON r.role_id = u.role_id WHERE r.role_name = 'Field Agent' ORDER BY u.full_name"), False))

    def handler(cur, d, f):
        need(d, 'service_type', 'destination', 'preferred_travel_date')
        client_id = d.get('client_id') if staff else user['id']
        if not client_id:
            raise FormError('Choose a client.')
        cur.execute(
            """INSERT INTO applications (client_id, assigned_agent_id, current_stage_id, service_type, destination,
                                         travel_purpose, preferred_travel_date, status)
               VALUES (%s, %s, (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1), %s, %s, %s, %s, 'ACTIVE')
               RETURNING application_id""",
            [client_id, (d.get('agent_id') or None) if staff else None, d['service_type'], d['destination'].strip(),
             d.get('travel_purpose', '').strip() or None, d['preferred_travel_date']],
        )
        app_id = cur.fetchone()[0]
        # first history row (skipped when a database trigger has already written it)
        cur.execute(
            """INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by)
               SELECT %s, NULL, (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1), NULL
               WHERE NOT EXISTS (SELECT 1 FROM stage_history WHERE application_id = %s)""", [app_id, app_id])
        audit(request, cur, 'APPLICATION_REGISTERED', 'applications', app_id)
        return app_id
    return form_page(request, 'New application', fields, handler, lambda app_id: '/applications/%s/' % app_id)


def move_stage(app_id, stage_id, user_id):
    """Use the database routine change_stage() when it exists, otherwise do the same steps here."""
    try:
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("SELECT change_stage(%s, %s, %s)", [app_id, int(stage_id), user_id])
    except ProgrammingError as exc:
        if 'change_stage' not in str(exc):
            raise
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("SELECT current_stage_id FROM applications WHERE application_id = %s FOR UPDATE", [app_id])
            old = cur.fetchone()[0]
            cur.execute("UPDATE applications SET current_stage_id = %s WHERE application_id = %s", [stage_id, app_id])
            cur.execute("""INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by)
                           VALUES (%s, %s, %s, %s)""", [app_id, old, stage_id, user_id])


def application_detail(request, app_id):
    user = request.session.get('user')
    if not user:
        return redirect('login')
    rows = fetch_all("""SELECT a.*, c.full_name AS client_name, c.phone AS client_phone, ag.full_name AS agent_name,
                               ps.stage_name, ps.stage_order
                        FROM applications a JOIN users c ON c.user_id = a.client_id
                        JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
                        LEFT JOIN users ag ON ag.user_id = a.assigned_agent_id
                        WHERE a.application_id = %s""", [app_id])
    if not rows:
        raise Http404
    app = rows[0]
    if not can_see(user, app):
        return HttpResponseForbidden('Not allowed for your role.')
    role = user['role']
    can_assign = role in ('Director', 'Secretary')
    can_stage = role in ('Director', 'Field Agent', 'Data Entry Staff')
    can_decide = role in ('Director', 'Field Agent', 'Data Entry Staff')
    can_pay_status = role in ('Director', 'Data Entry Staff')
    is_client = role == 'Client'

    if request.method == 'POST':
        act, d = request.POST.get('action'), request.POST
        try:
            with transaction.atomic(), connection.cursor() as cur:
                if act == 'assign' and can_assign:
                    cur.execute("UPDATE applications SET assigned_agent_id = %s WHERE application_id = %s", [d.get('agent_id') or None, app_id])
                    audit(request, cur, 'APPLICATION_ASSIGNED', 'applications', app_id)
                elif act == 'stage' and can_stage:
                    need(d, 'stage_id')
                    move_stage(app_id, d['stage_id'], user['id'])
                elif act == 'upload' and is_client:
                    f = request.FILES.get('file')
                    if not f:
                        raise FormError('Choose a file.')
                    if f.size < 1 or f.size > 5 * 1024 * 1024:
                        raise FormError('The file must be between 1 byte and 5 MB.')
                    ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
                    if ext not in ('pdf', 'jpg', 'jpeg', 'png'):
                        raise FormError('Only PDF, JPG or PNG files.')
                    path = default_storage.save('documents/%s/%s_%s.%s' % (app_id, d.get('document_type', 'DOC'), uuid.uuid4().hex[:8], ext), f)
                    cur.execute("""INSERT INTO documents (application_id, document_type, file_path, file_size_bytes)
                                   VALUES (%s, %s, %s, %s)""", [app_id, d.get('document_type'), path, f.size])
                elif act == 'decide' and can_decide:
                    decision, reason = d.get('decision'), d.get('reason', '').strip()
                    if decision == 'REJECTED' and not reason:
                        raise FormError('Give a reason when rejecting a document.')
                    cur.execute("""UPDATE documents SET verification_status = %s, verified_by = %s, verified_at = now(),
                                          rejection_reason = %s
                                   WHERE document_id = %s AND application_id = %s""",
                                [decision, user['id'], reason if decision == 'REJECTED' else None, d.get('document_id'), app_id])
                elif act == 'pay' and is_client:
                    amount = d.get('amount', '').strip()
                    if not amount:
                        raise FormError('Enter an amount.')
                    cur.execute("""INSERT INTO payments (application_id, amount, payment_method, payer_phone)
                                   VALUES (%s, %s, %s, %s)""", [app_id, amount, d.get('payment_method'), d.get('payer_phone', '').strip()])
                elif act == 'payment_status' and can_pay_status:
                    new = d.get('status')
                    if new == 'COMPLETED':
                        cur.execute("""UPDATE payments SET status = 'COMPLETED', completed_at = now(),
                                              transaction_reference = 'SIM-' || upper(substr(md5(random()::text), 1, 10))
                                       WHERE payment_id = %s AND application_id = %s AND status = 'PENDING'""", [d.get('payment_id'), app_id])
                    elif new == 'FAILED':
                        cur.execute("UPDATE payments SET status = 'FAILED' WHERE payment_id = %s AND application_id = %s AND status = 'PENDING'", [d.get('payment_id'), app_id])
                    elif new == 'REFUNDED':
                        cur.execute("UPDATE payments SET status = 'REFUNDED' WHERE payment_id = %s AND application_id = %s AND status = 'COMPLETED'", [d.get('payment_id'), app_id])
                    else:
                        raise FormError('Unknown payment action.')
                    if cur.rowcount == 0:
                        raise FormError('That payment is not in a state that allows this action.')
                else:
                    return HttpResponseForbidden('Not allowed for your role.')
            messages.success(request, 'Done.')
        except FormError as exc:
            messages.error(request, str(exc))
        except IntegrityError as exc:
            messages.error(request, 'The database refused this: %s' % str(exc).strip().splitlines()[0])
        except DatabaseError as exc:
            messages.error(request, 'The database refused this: %s' % str(exc).strip().splitlines()[0])
        return redirect('/applications/%s/' % app_id)

    ctx = {
        'app': app, 'can_assign': can_assign, 'can_stage': can_stage, 'can_decide': can_decide,
        'can_pay_status': can_pay_status, 'is_client': is_client,
        'documents': fetch_all("""SELECT d.*, v.full_name AS verifier FROM documents d
                                   LEFT JOIN users v ON v.user_id = d.verified_by
                                   WHERE d.application_id = %s ORDER BY d.uploaded_at""", [app_id]),
        'payments': fetch_all("SELECT * FROM payments WHERE application_id = %s ORDER BY initiated_at", [app_id]),
        'history': fetch_all("""SELECT h.changed_at, fs.stage_name AS from_stage, ts.stage_name AS to_stage,
                                       COALESCE(u.full_name, 'system') AS changed_by
                                FROM stage_history h LEFT JOIN pipeline_stages fs ON fs.stage_id = h.from_stage_id
                                JOIN pipeline_stages ts ON ts.stage_id = h.to_stage_id
                                LEFT JOIN users u ON u.user_id = h.changed_by
                                WHERE h.application_id = %s ORDER BY h.changed_at, h.history_id""", [app_id]),
        'agents': options("SELECT u.user_id, u.full_name FROM users u JOIN roles r ON r.role_id = u.role_id WHERE r.role_name = 'Field Agent' ORDER BY u.full_name"),
        'stages': options("SELECT stage_id, stage_order || '. ' || stage_name FROM pipeline_stages ORDER BY stage_order"),
    }
    return render(request, 'core/application_detail.html', ctx)


@role_required('Director', 'Secretary')
def new_appointment(request):
    fields = [
        ('client_id', 'Client', 'select', options("SELECT user_id, full_name FROM users u WHERE EXISTS (SELECT 1 FROM client_profiles c WHERE c.user_id = u.user_id) ORDER BY full_name"), True),
        ('staff_id', 'Staff member', 'select', options("SELECT user_id, full_name FROM users u WHERE EXISTS (SELECT 1 FROM staff_profiles s WHERE s.user_id = u.user_id) ORDER BY full_name"), True),
        ('appointment_type', 'Type (for example Consultation)', 'text', None, True),
        ('when', 'Date and time (Kampala time)', 'datetime-local', None, True),
    ]

    def handler(cur, d, f):
        need(d, 'client_id', 'staff_id', 'appointment_type', 'when')
        cur.execute("""INSERT INTO schedule_records (client_id, staff_id, appointment_type, scheduled_datetime)
                       VALUES (%s, %s, %s, %s::timestamp AT TIME ZONE 'Africa/Kampala')""",
                    [d['client_id'], d['staff_id'], d['appointment_type'].strip(), d['when']])
    return form_page(request, 'New appointment', fields, handler, 'appointments')


@role_required('Director', 'Secretary')
def appointment_status(request, schedule_id, action):
    if request.method == 'POST' and action in ('complete', 'cancel'):
        status = 'COMPLETED' if action == 'complete' else 'CANCELLED'
        try:
            with connection.cursor() as cur:
                cur.execute("UPDATE schedule_records SET status = %s WHERE schedule_id = %s", [status, schedule_id])
            messages.success(request, 'Appointment marked %s.' % status.lower())
        except DatabaseError as exc:
            messages.error(request, 'The database refused this: %s' % str(exc).strip().splitlines()[0])
    return redirect('appointments')


@role_required('Director', 'Secretary')
def new_notification(request):
    fields = [
        ('user_id', 'Send to', 'select', options("SELECT user_id, full_name || ' (' || phone || ')' FROM users ORDER BY full_name"), True),
        ('channel', 'Channel', 'select', [('SMS', 'SMS'), ('EMAIL', 'Email')], True),
        ('message', 'Message (max 300 characters)', 'textarea', None, True),
        ('application_id', 'About an application (optional)', 'select', [('', '(none)')] + options(
            "SELECT a.application_id, c.full_name || ' to ' || a.destination FROM applications a JOIN users c ON c.user_id = a.client_id ORDER BY c.full_name"), False),
    ]

    def handler(cur, d, f):
        need(d, 'user_id', 'channel', 'message')
        if len(d['message']) > 300:
            raise FormError('The message is longer than 300 characters.')
        # there is no real SMS or email gateway in this project: the row is stored as SENT
        cur.execute("INSERT INTO notifications (user_id, application_id, channel, message, status) VALUES (%s, %s, %s, %s, 'SENT')",
                    [d['user_id'], d.get('application_id') or None, d['channel'], d['message'].strip()])
    return form_page(request, 'Send a notification', fields, handler,
                     lambda _: 'notifications' if request.session['user']['role'] == 'Director' else 'applications')