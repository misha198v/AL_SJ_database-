import logging
from uuid import UUID
from django.db import connections, transaction, DatabaseError
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)
ROLE_NAMES = {
    'Client': 'alsj_client', 'Field Agent': 'alsj_field_agent',
    'Data Entry Staff': 'alsj_data_entry_staff', 'Secretary': 'alsj_secretary',
    'Director': 'alsj_director',
}


class DatabaseRoleMiddleware:
    """The authenticated server session supplies identity, never request form data."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/logout/' and request.method == 'POST':
            return self.get_response(request)
        user = request.session.get('user')
        if not user:
            return self.get_response(request)
        try:
            actor = str(UUID(user['id']))
        except (ValueError, KeyError, TypeError):
            request.session.flush()
            return self.get_response(request)
        try:
            with transaction.atomic(using='alsj'):
                conn = connections['alsj']
                with conn.cursor() as cur:
                    cur.execute('SELECT * FROM public.app_session_identity(%s)', [actor])
                    identity = cur.fetchone()
                    if not identity or identity[2] not in ROLE_NAMES:
                        request.session.flush()
                    else:
                        request.session['user'] = {'id': str(identity[0]), 'name': identity[1], 'role': identity[2]}
                        cur.execute('SET LOCAL ROLE ' + conn.ops.quote_name(ROLE_NAMES[identity[2]]))
                        cur.execute("SELECT set_config('app.current_user_id', %s, true)", [actor])
                # Rendered responses, including every query, stay inside this transaction.
                response = self.get_response(request)
                if response.status_code == 404:
                    response = render(request, 'core/error.html', {'error_code':'404','error_title':'This record is not available','error_text':'It may not exist or may not be available to your role. Return to your workspace to continue.'},status=404)
                if hasattr(response, 'render') and callable(response.render):
                    response.render()
                if response.status_code >= 400:
                    transaction.set_rollback(True, using='alsj')
                return response
        except DatabaseError:
            logger.exception('Application database request failed')
            return render(request, 'core/error.html', {'error_code':'503','error_title':'The workspace could not connect','error_text':'Your change could not be confirmed. Check the connection, then reload before trying again.'}, status=503)
