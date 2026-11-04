import hashlib
import logging
from django.core.cache import cache
from django.db import DatabaseError
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from .auth import check_login
from .decorators import login_required_alsj

logger = logging.getLogger(__name__)

@sensitive_post_parameters('password')
def login_view(request):
    error = ''
    status = 200
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        token = hashlib.sha256((request.META.get('REMOTE_ADDR', '') + ':' + phone).encode()).hexdigest()
        key = 'login:' + token
        tries = cache.get(key, 0)
        if tries >= 5:
            error, status = 'Too many attempts. Try again in five minutes.', 429
        else:
            try:
                user = check_login(phone, password)
            except DatabaseError:
                logger.exception('Login database operation failed')
                user = None
                error, status = 'Login is unavailable. Check the database integration setup.', 503
            if user:
                request.session.flush()
                rotate_token(request)
                request.session['user'] = {
                    'id': str(user['user_id']), 'name': user['full_name'], 'role': user['role_name'],
                }
                cache.delete(key)
                return redirect('home')
            if not error:
                cache.set(key, tries + 1, 300)
                error = 'Wrong phone or password.'
    return render(request, 'core/login.html', {'error': error}, status=status)

@require_POST
def logout_view(request):
    request.session.flush()
    return redirect('login')

def home(request):
    if not request.session.get('user'):
        return render(request, 'core/welcome.html')
    role = request.session['user']['role']
    if role == 'Director':
        return redirect('dashboard')
    if role == 'Data Entry Staff':
        return redirect('document_queue')
    return redirect({'Client':'my_applications','Secretary':'appointments','Field Agent':'applications'}.get(role,'applications'))
