from django.urls import path
from . import actions, pages, views

urlpatterns = [
    path('',views.home,name='home'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('my-applications/',pages.my_applications,name='my_applications'),
    path('dashboard/',pages.dashboard,name='dashboard'),
    path('applications/',pages.applications,name='applications'),
    path('applications/<uuid:app_id>/',actions.application_detail,name='application_detail'),
    path('documents/',pages.documents,name='documents'),
    path('document-queue/',pages.document_queue,name='document_queue'),
    path('reports/time-per-stage/',pages.time_per_stage,name='time_per_stage'),
    path('appointments/',pages.appointments,name='appointments'),
    path('appointments/new/',actions.new_appointment,name='new_appointment'),
    path('appointments/<uuid:schedule_id>/<str:action>/',actions.appointment_status,name='appointment_status'),
    path('transactions/',pages.transactions,name='transactions'),
    path('employees/',pages.employees,name='employees'),
    path('clients/',pages.clients,name='clients'),
    path('notifications/',pages.notifications,name='notifications'),
    path('stage-history/',pages.stage_history,name='stage_history'),
    path('audit-log/',pages.audit,name='audit'),
    path('reports/revenue/',pages.revenue_report,name='revenue_report'),
    path('users/',pages.users_list,name='users_list'),
    path('data/',pages.data_index,name='data_index'),
    path('data/<str:table>/',pages.data_table,name='data_table'),
    # Explicitly reject old URLs whose writes are outside the approved role permissions.
    path('register/',actions.refused,name='register'),
    path('applications/new/',actions.refused,name='new_application'),
    path('clients/new/',actions.refused,name='add_client'),
    path('employees/new/',actions.refused,name='add_employee'),
    path('notifications/new/',actions.refused,name='new_notification'),
]
