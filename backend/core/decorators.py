from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


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
                return HttpResponseForbidden('Not allowed for your role.')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
