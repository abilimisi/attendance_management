from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Teacher Dashboard and related URLs
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('scanner/<int:session_id>/', views.scanner_view, name='scanner_view'),
    path('process-scan/<int:session_id>/', views.process_scan, name='process_scan'),
    path('attendance/<int:session_id>/', views.attendance_list_view, name='attendance_list'),
    
    # Session Management
    path('start_session/<int:subject_id>/', views.start_session, name='start_session'),
    path('end_session/<int:session_id>/', views.end_session, name='end_session'), # NEW URL

    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('download/<int:session_id>/', views.download_attendance, name='download_attendance'), 

    path('history/<int:subject_id>/', views.subject_history_view, name='subject_history'),


]