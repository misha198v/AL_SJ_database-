from django.db import DatabaseError, connection, transaction
from django.shortcuts import redirect, render

from . import pages
from .db import fetch_all
from .decorators import role_required


@role_required('Director', 'Field Agent', 'Data Entry Staff')
def documents(request):
    # Everyone except Data Entry Staff keeps the existing read-only list.
    if request.session['user']['role'] != 'Data Entry Staff':
        return pages.documents(request)
    rows = fetch_all("SELECT * FROM v_document_review_queue ORDER BY uploaded_at ASC")
    flash = request.session.pop('flash', None)
    return render(request, 'core/documents_queue.html', {'rows': rows, 'flash': flash})


@role_required('Data Entry Staff')
def decide(request, document_id):
    if request.method != 'POST':
        return redirect('documents')
    decision = request.POST.get('decision', '')
    reason = request.POST.get('reason', '').strip()
    try:
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute(
                "SELECT fn_decide_document(%s::uuid, %s::text, %s::uuid, %s::text)",
                [str(document_id), decision, request.session['user']['id'], reason or None],
            )
        request.session['flash'] = {'ok': True, 'text': 'Document %s.' % decision.lower()}
    except DatabaseError as exc:
        request.session['flash'] = {'ok': False, 'text': str(exc).split('\n')[0]}
    return redirect('documents')