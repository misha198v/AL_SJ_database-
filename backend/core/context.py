# The menu each role sees. Each item is (label, url name).
MENUS = {
    'Client': [('My applications', 'my_applications'), ('New application', 'new_application')],
    'Field Agent': [('My clients', 'my_clients'), ('My applications', 'applications'), ('Documents', 'documents')],
    'Data Entry Staff': [('Applications', 'applications'), ('Documents', 'documents')],
    'Secretary': [('Applications', 'applications'), ('New application', 'new_application'), ('Clients', 'clients'),
                  ('Add client', 'add_client'), ('Appointments', 'appointments'), ('Send notification', 'new_notification')],
    'Director': [
        ('Dashboard', 'dashboard'), ('Applications', 'applications'), ('New application', 'new_application'),
        ('Transactions', 'transactions'), ('Employees', 'employees'), ('Add employee', 'add_employee'),
        ('Clients', 'clients'), ('Add client', 'add_client'), ('Documents', 'documents'),
        ('Appointments', 'appointments'), ('Send notification', 'new_notification'), ('Notifications', 'notifications'),
        ('Stage history', 'stage_history'), ('Audit log', 'audit'), ('Users', 'users_list'), ('All tables', 'data_index'),
    ],
}


def menu(request):
    user = request.session.get('user')
    return {'menu': MENUS.get(user['role'], []) if user else []}
