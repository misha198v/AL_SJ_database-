MENUS = {
    'Client': [('My applications','my_applications')],
    'Field Agent': [('My applications','applications'),('Documents','documents')],
    'Data Entry Staff': [('Document queue','document_queue'),('Time per stage','time_per_stage'),('Applications','applications'),('Documents','documents')],
    'Secretary': [('Appointments','appointments'),('Book appointment','new_appointment')],
    'Director': [('Dashboard','dashboard'),('Applications','applications'),('Documents','documents'),
                 ('Document queue','document_queue'),('Time per stage','time_per_stage'),
                 ('Transactions','transactions'),('Employees','employees'),('Clients','clients'),
                 ('Appointments','appointments'),('Notifications','notifications'),('Stage history','stage_history'),
                 ('Audit log','audit'),('Users','users_list'),('All records','data_index')],
}
ROUTE_ICONS = {'dashboard':'grid','my_applications':'files','applications':'files',
    'documents':'files','document_queue':'files','time_per_stage':'clock',
    'appointments':'calendar','new_appointment':'plus','transactions':'wallet',
    'employees':'users','clients':'users','notifications':'mail','stage_history':'route',
    'audit':'shield','users_list':'users','data_index':'database'}
SCREENS = {
    'applications':('Applications','Your journeys, in one place.','Travel operations'),
    'my_applications':('My applications','Follow each step of your travel application.','Your journeys'),
    'document_queue':('Document review queue','The next document is the next step in someone’s journey.','Review workspace'),
    'time_per_stage':('Time per stage','Understand how applications move through the journey.','Journey insights'),
    'documents':('Documents','A clear view of submitted travel documents.','Travel operations'),
    'dashboard':('Operations overview','A considered view of your agency, from applications to departures.','Director workspace'),
    'application_detail':('Application details','Every document and milestone, together.','Travel operations'),
    'appointments':('Appointments','Make time for the next step.','Client coordination'),
    'new_appointment':('Book an appointment','Bring the right people together, at the right time.','Client coordination'),
}

def menu(request):
    user = request.session.get('user')
    route = request.resolver_match.url_name if request.resolver_match else ''
    items = MENUS.get(user['role'],[]) if user else []
    navigation = [{'label':label,'route':name,'icon':ROUTE_ICONS.get(name,'files'),
                   'active':route==name or (route=='application_detail' and name in ('applications','my_applications'))}
                  for label,name in items]
    title,description,eyebrow = SCREENS.get(route,(route.replace('_',' ').capitalize() if route else 'Workspace','Your travel operations, clearly organized.','AL SJ workspace'))
    return {'menu':items,'navigation':navigation,'screen':{'title':title,'description':description,'eyebrow':eyebrow}}
