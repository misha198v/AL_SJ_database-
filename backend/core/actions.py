"""Only operations allowed by the installed database roles are exposed."""
from datetime import datetime
from django.contrib import messages
from django.db import DatabaseError, transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from .db import fetch_all, fetch_table
from .decorators import role_required

def refused(request, *args, **kwargs):
    return render(request, 'core/error.html', {'error_title':'This action is not available','error_text':'Your workspace does not allow this change. Return to a page available to your role.','error_code':'403'}, status=403)

@role_required('Client', 'Field Agent', 'Data Entry Staff', 'Director')
def application_detail(request, app_id):
    rows = fetch_all("""
        SELECT a.*, c.full_name AS client_name,c.phone AS client_phone,
               ag.full_name AS agent_name,ps.stage_name,ps.stage_order
        FROM public.applications a
        JOIN public.users c ON c.user_id=a.client_id
        LEFT JOIN public.users ag ON ag.user_id=a.assigned_agent_id
        LEFT JOIN public.pipeline_stages ps ON ps.stage_id=a.current_stage_id
        WHERE a.application_id=%s""", [app_id])
    if not rows:
        raise Http404
    role = request.session['user']['role']
    can_edit = role in ('Data Entry Staff', 'Field Agent')
    action_error = ''
    if request.method == 'POST':
        if not can_edit:
            return refused(request)
        action = request.POST.get('action')
        if action not in ('decide', 'stage'):
            return refused(request)
        try:
            # A savepoint keeps a refused routine from poisoning the outer request transaction.
            with transaction.atomic(using='alsj'):
                prefix = 'data_entry' if role == 'Data Entry Staff' else 'field_agent'
                if action == 'decide':
                    doc_id = request.POST.get('document_id', '')
                    if not fetch_all('SELECT document_id FROM public.documents WHERE document_id=%s AND application_id=%s',
                                     [doc_id, app_id]):
                        raise Http404
                    fetch_all('SELECT public.' + prefix + '_decide_document(%s,%s,%s)',
                              [doc_id, request.POST.get('decision'), request.POST.get('reason', '').strip() or None])
                else:
                    stage = int(request.POST.get('stage_id', ''))
                    fetch_all('SELECT public.' + prefix + '_change_stage(%s,%s)', [app_id, stage])
            messages.success(request, 'Stage updated.' if action == 'stage' else 'Document decision saved.')
            return redirect('application_detail', app_id=app_id)
        except (ValueError, TypeError):
            action_error = 'Choose a valid stage.'
        except DatabaseError:
            action_error = 'This change was not saved. Check the decision, rejection reason and your permissions, then try again.'
    docs = fetch_all('SELECT d.*,u.full_name AS verifier FROM public.documents d LEFT JOIN public.users u ON u.user_id=d.verified_by WHERE d.application_id=%s ORDER BY d.uploaded_at,d.document_id', [app_id])
    for doc in docs:
        submitted = str(doc['document_id']) == request.POST.get('document_id')
        doc['decision_value'] = request.POST.get('decision','VERIFIED') if submitted else 'VERIFIED'
        doc['reason_value'] = request.POST.get('reason','') if submitted else ''
    pipeline = fetch_all('SELECT stage_id,stage_name,stage_order FROM public.pipeline_stages ORDER BY stage_order')
    history = []
    if role != 'Client':
        history = fetch_all("""
            SELECT h.changed_at,fs.stage_name AS from_stage,ts.stage_name AS to_stage,
                   COALESCE(u.full_name,'system') AS changed_by
            FROM public.stage_history h
            LEFT JOIN public.pipeline_stages fs ON fs.stage_id=h.from_stage_id
            JOIN public.pipeline_stages ts ON ts.stage_id=h.to_stage_id
            LEFT JOIN public.users u ON u.user_id=h.changed_by
            WHERE h.application_id=%s ORDER BY h.changed_at,h.history_id""", [app_id])
    can_read_payments = role in ('Client', 'Director')
    return render(request, 'core/application_detail.html', {
        'app': rows[0], 'documents': docs, 'history': history, 'action_error':action_error,
        'pipeline':pipeline,
        'payments': fetch_all('SELECT * FROM public.payments WHERE application_id=%s ORDER BY initiated_at', [app_id]) if can_read_payments else [],
        'can_read_payments': can_read_payments, 'can_read_history': role != 'Client',
        'can_stage': can_edit, 'can_decide': can_edit,
        'can_assign': False, 'can_pay_status': False, 'is_client': False,
        'stages': [(p['stage_id'],str(p['stage_order'])+'. '+p['stage_name']) for p in pipeline],
    })

@role_required('Secretary')
def new_appointment(request):
    error = ''
    choices = fetch_all('SELECT * FROM public.secretary_appointment_choices()')
    fields = [
        ('client_id','Client','select',[(str(r['user_id']),r['full_name']) for r in choices if r['kind']=='client'],True),
        ('staff_id','Staff member','select',[(str(r['user_id']),r['full_name']) for r in choices if r['kind']=='staff'],True),
        ('appointment_type','Appointment type','text',None,True),
        ('when','Date and time (Kampala time)','datetime-local',None,True),
    ]
    if request.method == 'POST':
        try:
            if not all(request.POST.get(k,'').strip() for k in ('when','client_id','staff_id','appointment_type')):
                raise ValueError('Required fields are missing')
            moment = datetime.fromisoformat(request.POST.get('when', ''))
            if timezone.is_naive(moment):
                moment = timezone.make_aware(moment)
            with transaction.atomic(using='alsj'):
                fetch_all('SELECT public.secretary_save_appointment(%s,%s,%s,%s)',
                          [request.POST.get('client_id'),request.POST.get('staff_id'),
                           request.POST.get('appointment_type','').strip(),moment])
            messages.success(request,'Appointment saved.')
            return redirect('appointments')
        except (ValueError, TypeError):
            error = 'Complete the required fields and choose a valid date and time.'
        except DatabaseError:
            error = 'The database refused this appointment. Check the client, staff member and appointment details.'
    return render(request,'core/form.html',{'title':'New appointment','fields':fields,
                                           'values':request.POST,'error':error,'submit':'Save'})

@role_required('Secretary')
def appointment_status(request, schedule_id, action):
    if request.method != 'POST' or action not in ('complete','cancel','delete'):
        return refused(request)
    rows = fetch_all('SELECT * FROM public.schedule_records WHERE schedule_id=%s',[schedule_id])
    if not rows:
        raise Http404
    row = rows[0]
    try:
        with transaction.atomic(using='alsj'):
            if action == 'delete':
                fetch_all('SELECT public.secretary_delete_appointment(%s)',[schedule_id])
            else:
                fetch_all('SELECT public.secretary_save_appointment(%s,%s,%s,%s,%s,%s)',
                          [row['client_id'],row['staff_id'],row['appointment_type'],row['scheduled_datetime'],
                           'COMPLETED' if action=='complete' else 'CANCELLED',schedule_id])
        messages.success(request,'Appointment deleted.' if action == 'delete' else 'Appointment updated.')
    except DatabaseError:
        messages.error(request,'The database refused this appointment change.')
    return redirect('appointments')
