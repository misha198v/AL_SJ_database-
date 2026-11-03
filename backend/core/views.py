from django.db import DatabaseError, IntegrityError, connection, transaction
from django.shortcuts import redirect, render

from .auth import check_login, hash_password
from .decorators import login_required_alsj


def login_view(request):
    error = ''
    if request.method == 'POST':
        user = check_login(request.POST.get('phone', '').strip(), request.POST.get('password', ''))
        if user:
            request.session['user'] = {
                'id': str(user['user_id']),
                'name': user['full_name'],
                'role': user['role_name'],
            }
            return redirect('home')
        error = 'Wrong phone or password.'
    return render(request, 'core/login.html', {'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('login')


@login_required_alsj
def home(request):
    if request.session['user']['role'] == 'Director':
        return redirect('dashboard')
    return render(request, 'core/home.html')


def register(request):
    error = ''
    if request.method == 'POST':
        p = request.POST
        full_name, phone = p.get('full_name', '').strip(), p.get('phone', '').strip()
        password, national_id = p.get('password', ''), p.get('national_id', '').strip()
        if not (full_name and phone and national_id) or len(password) < 8:
            error = 'Fill in name, phone and national ID, and use a password of at least 8 characters.'
        else:
            try:
                with transaction.atomic(), connection.cursor() as cur:
                    cur.execute(
                        """INSERT INTO users (full_name, phone, password_hash, role_id)
                           VALUES (%s, %s, %s, (SELECT role_id FROM roles WHERE role_name = 'Client'))
                           RETURNING user_id""",
                        [full_name, phone, hash_password(password)],
                    )
                    user_id = cur.fetchone()[0]
                    cur.execute(
                        """INSERT INTO client_profiles (user_id, national_id, date_of_birth, address, preferred_language)
                           VALUES (%s, %s, %s, %s, %s)""",
                        [user_id, national_id, p.get('date_of_birth') or None, p.get('address', '').strip() or None, 'EN'],
                    )
                return redirect('login')
            except IntegrityError:
                error = 'That phone number or national ID is already registered.'
            except DatabaseError as exc:
                error = 'The database refused this: %s' % exc
    return render(request, 'core/register.html', {'error': error})
