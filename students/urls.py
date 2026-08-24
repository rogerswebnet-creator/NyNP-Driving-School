from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='students/password_reset.html',
        email_template_name='students/password_reset_email.html',
        success_url='/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='students/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='students/password_reset_confirm.html',
        success_url='/reset/complete/',
    ), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='students/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('register/choose/', views.register_choice, name='register_choice'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-user/', views.create_user, name='create_user'),
    path('admin-users/change-password/', views.admin_change_user_password, name='admin_change_user_password'),
    path('logout/', views.logout_view, name='logout'),
    path('sign-in/', views.sign_in_today, name='sign_in_today'),

    # instructor frontend
    path('instructor/login/', views.instructor_login, name='instructor_login'),
    path('instructor/register/', views.instructor_register, name='instructor_register'),
    path('instructor/attendance/', views.instructor_attendance, name='instructor_attendance'),
    path('instructor/confirm/<int:attendance_id>/', views.confirm_attendance, name='confirm_attendance'),
    path('instructor/decline/<int:attendance_id>/', views.decline_attendance, name='decline_attendance'),

    # student/admin lists
    path('students/', views.students_list, name='students_list'),
    path('students/archived/', views.archived_students_list, name='archived_students_list'),
    path('students/<int:student_id>/edit/', views.edit_student_profile, name='edit_student_profile'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('students/archive/<int:student_id>/', views.archive_student, name='archive_student'),
    path('students/unarchive/<int:student_id>/', views.unarchive_student, name='unarchive_student'),
    path('students/download/csv/', views.download_students_csv, name='download_students_csv'),
    path('students/download/xlsx/', views.download_students_excel, name='download_students_excel'),

    # admin instructors list
    path('manage/instructors/', views.admin_instructors_list, name='admin_instructors_list'),
    path('manage/instructors/archived/', views.archived_instructors_list, name='archived_instructors_list'),
    path('manage/instructors/<int:instructor_id>/edit/', views.admin_edit_instructor, name='admin_edit_instructor'),
    path('manage/instructors/<int:instructor_id>/archive/', views.archive_instructor, name='archive_instructor'),
    path('manage/instructors/<int:instructor_id>/unarchive/', views.unarchive_instructor, name='unarchive_instructor'),
    path('manage/instructors/<int:instructor_id>/delete/', views.delete_instructor, name='delete_instructor'),

    # student attendance history
    path('attendance/history/', views.attendance_history, name='attendance_history'),
]
