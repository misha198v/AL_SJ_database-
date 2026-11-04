"""Run ONLY against a disposable clone, never against the project database.

Set ALSJ_INTEGRATION_TEST=1, DB_NAME=alsj_django_test_<suffix>, DB_PORT=55439.
The test cluster uses local trust authentication; owner access is test-only.
"""
import os
import uuid
from pathlib import Path

if os.environ.get('ALSJ_INTEGRATION_TEST') != '1':
    raise SystemExit('Explicit ALSJ_INTEGRATION_TEST=1 required.')
if not os.environ.get('DB_NAME', '').startswith('alsj_django_test_') or os.environ.get('DB_PORT') != '55439':
    raise SystemExit('A disposable alsj_django_test_* database on test port 55439 is required.')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alsj_backend.settings')
import django
django.setup()
import bcrypt
import psycopg
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.db import connections
from django.test import Client, override_settings

owner = psycopg.connect(host='127.0.0.1', port=55439, dbname=os.environ['DB_NAME'], user='postgres', autocommit=True,
                        options='-c client_encoding=UTF8')
owner.execute(Path('sql/050_django_integration.sql').read_text(encoding='utf-8'))
# Test fixtures only: no password in the real database is changed by this script.
owner.execute('UPDATE public.users SET password_hash=%s', [bcrypt.hashpw(b'Test1234!', bcrypt.gensalt()).decode()])
owner.execute("UPDATE public.users SET is_active=true WHERE phone='0700000002'")
owner.execute("""UPDATE public.documents SET verification_status='PENDING',verified_by=NULL,
                 verified_at=NULL,rejection_reason=NULL
                 WHERE document_id='30000000-0000-0000-0000-000000000002'""")
call_command('migrate', database='default', verbosity=0)
checks = 0

def check(condition, message):
    global checks
    assert condition, message
    checks += 1
    print('PASS:', message)

def scalar(sql, params=()):
    return owner.execute(sql, params or None).fetchone()[0]

def login(phone):
    cache.clear()
    c = Client()
    response = c.post('/login/', {'phone': phone, 'password': 'Test1234!'})
    check(response.status_code == 302, 'bcrypt login ' + phone)
    check('password_hash' not in str(dict(c.session)), 'session contains no password hash')
    return c

def request(c, url, expected=200):
    response = c.get(url)
    check(response.status_code == expected, url + ' HTTP ' + str(expected))
    with connections['alsj'].cursor() as cur:
        cur.execute("SELECT current_user, NULLIF(current_setting('app.current_user_id',true),'')")
        name, actor = cur.fetchone()
    check(name == 'alsj_app_login' and actor is None, 'request role and identity reset')
    return response

app = '20000000-0000-0000-0000-000000000001'
other = '20000000-0000-0000-0000-000000000002'
with override_settings(ALLOWED_HOSTS=['testserver']):
    check(settings.DATABASES['default']['ENGINE'].endswith('sqlite3'), 'sessions use SQLite')
    check(scalar("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'django_%'") == 0,
          'no Django tables in public')
    c = Client()
    check(c.post('/login/', {'phone':'0700000002','password':'wrong'}).status_code == 200 and 'user' not in c.session,
          'wrong password refused')
    for _ in range(5):
        response = c.post('/login/', {'phone':'unknown','password':'wrong'})
    check(c.post('/login/', {'phone':'unknown','password':'wrong'}).status_code == 429, 'login retry limit')
    de = login('0700000002')
    for url in ['/document-queue/','/reports/time-per-stage/','/applications/','/documents/',f'/applications/{app}/']:
        request(de,url)
    request(de,'/transactions/',403)
    check(b'REJECTED' in request(de,f'/applications/{app}/').content, 'Data Entry decision form displayed')
    response = de.get('/reports/time-per-stage/?csv=1')
    check(response.status_code==200 and 'attachment' in response['Content-Disposition'], 'stage duration CSV export')
    doc = '30000000-0000-0000-0000-000000000002'
    old_audits = scalar('SELECT count(*) FROM public.audit_logs')
    de.post(f'/applications/{app}/', {'action':'decide','document_id':doc,'decision':'REJECTED','reason':''})
    check(scalar('SELECT verification_status::text FROM public.documents WHERE document_id=%s',[doc])=='PENDING', 'blank rejection refused')
    de.post(f'/applications/{app}/', {'action':'decide','document_id':doc,'decision':'VERIFIED'})
    check(scalar('SELECT verification_status::text FROM public.documents WHERE document_id=%s',[doc])=='VERIFIED', 'Data Entry decision saved through routine')
    check(scalar('SELECT count(*) FROM public.audit_logs')==old_audits+1, 'document audit trigger fired once')
    stage = scalar('SELECT stage_id FROM public.pipeline_stages WHERE stage_order=4')
    before = scalar('SELECT count(*) FROM public.stage_history WHERE application_id=%s',[app])
    de.post(f'/applications/{app}/', {'action':'stage','stage_id':str(stage)})
    check(scalar('SELECT current_stage_id FROM public.applications WHERE application_id=%s',[app])==stage, 'Data Entry stage routine saved stage')
    check(scalar('SELECT count(*) FROM public.stage_history WHERE application_id=%s',[app])==before+1, 'stage history inserted once')
    check(b'No pending documents' in request(de,'/document-queue/').content, 'reviewed document leaves pending queue')
    agent = login('0700000001')
    for url in ['/applications/','/documents/',f'/applications/{app}/']:
        request(agent,url)
    # Use a test fixture to guarantee the second application is unassigned.
    owner.execute('UPDATE public.applications SET assigned_agent_id=NULL WHERE application_id=%s',[other])
    request(agent,f'/applications/{other}/',404)
    request(agent,'/reports/time-per-stage/',403)
    old_stage = scalar('SELECT current_stage_id FROM public.applications WHERE application_id=%s',[other])
    response = agent.post(f'/applications/{other}/', {'action':'stage','stage_id':1})
    check(response.status_code==404 and scalar('SELECT current_stage_id FROM public.applications WHERE application_id=%s',[other])==old_stage,
          'Field Agent cannot change an unassigned application')
    stage = scalar('SELECT stage_id FROM public.pipeline_stages WHERE stage_order=5')
    agent.post(f'/applications/{app}/', {'action':'stage','stage_id':str(stage)})
    check(scalar('SELECT current_stage_id FROM public.applications WHERE application_id=%s',[app])==stage,
          'Field Agent stage wrapper updates assigned application')
    agent.post(f'/applications/{app}/', {'action':'decide','document_id':doc,'decision':'REJECTED','reason':'Test rejection'})
    check(scalar('SELECT verification_status::text FROM public.documents WHERE document_id=%s',[doc])=='REJECTED',
          'Field Agent decision uses assigned-document routine')
    client = login('0772556213')
    request(client,'/my-applications/')
    request(client,f'/applications/{app}/')
    request(client,f'/applications/{other}/',404)
    request(client,'/document-queue/',403)
    check(client.post(f'/applications/{app}/',{'action':'stage','stage_id':1}).status_code==403, 'Client cannot change stage')
    session = client.session
    session['user'] = dict(session['user'], role='Director')
    session.save()
    request(client,'/dashboard/',403)
    check(client.session['user']['role']=='Client', 'database revalidates session role')
    director = login('0700000004')
    for url in ['/dashboard/','/applications/','/documents/','/document-queue/','/reports/time-per-stage/',
                '/transactions/','/employees/','/clients/','/appointments/','/notifications/',
                '/stage-history/','/audit-log/','/users/','/data/','/data/users/','/reports/revenue/']:
        request(director,url)
    check(director.post(f'/applications/{app}/',{'action':'stage','stage_id':1}).status_code==403, 'Director remains read only')
    check(b'New appointment' not in request(director,'/appointments/').content, 'Director sees no appointment write controls')
    secretary = login('0700000003')
    request(secretary,'/appointments/')
    request(secretary,'/appointments/new/')
    request(secretary,'/transactions/',403)
    kind = 'Integration ' + uuid.uuid4().hex[:8]
    response = secretary.post('/appointments/new/', {
        'client_id':'10000000-0000-0000-0000-000000000011',
        'staff_id':'10000000-0000-0000-0000-000000000003',
        'appointment_type':kind,'when':'2026-12-01T10:00',
    })
    check(response.status_code==302, 'Secretary creates appointment through routine')
    schedule = scalar('SELECT schedule_id FROM public.schedule_records WHERE appointment_type=%s',[kind])
    secretary.post(f'/appointments/{schedule}/complete/')
    check(scalar('SELECT status::text FROM public.schedule_records WHERE schedule_id=%s',[schedule])=='COMPLETED','Secretary updates appointment through routine')
    secretary.post(f'/appointments/{schedule}/delete/')
    check(scalar('SELECT count(*) FROM public.schedule_records WHERE schedule_id=%s',[schedule])==0,'Secretary deletes appointment through routine')
    owner.execute("UPDATE public.users SET is_active=false WHERE phone='0700000002'")
    request(de,'/document-queue/',302)
    check('user' not in de.session, 'disabled user session revoked')
    for role in ['alsj_app_login','alsj_client','alsj_field_agent','alsj_data_entry_staff','alsj_secretary','alsj_director']:
        check(not scalar("SELECT has_column_privilege(%s,'public.users','password_hash','SELECT')",[role]),role+' cannot read hashes')
    check(scalar("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")==12,'12-table design preserved')
    check(scalar("SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND contype='f'")==18,'18 relationships preserved')
    csrf = Client(enforce_csrf_checks=True)
    csrf.get('/login/')
    check(csrf.post('/login/',{'phone':'0700000001','password':'Test1234!'}).status_code==403,'CSRF enforced')

connections.close_all()
owner.close()
print(f'All {checks} integration checks passed.')
