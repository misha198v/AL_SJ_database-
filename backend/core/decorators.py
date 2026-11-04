from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render


def login_required_alsj(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if 'user' not in request.session:
            return redirect('login')
        return view(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.session.get('user')
            if not user:
                return redirect('login')
            if user['role'] not in roles:
                return render(request, 'core/error.html', {'error_title':'This page belongs to another workspace','error_text':'Your current role does not have access to this page. Use the navigation to return to your work.','error_code':'403'}, status=403)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
