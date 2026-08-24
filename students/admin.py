from django.contrib import admin

from .models import Attendance, Instructor, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'admission_number',
        'full_name',
        'phone_number',
        'email',
        'national_id_passport',
        'gender',
        'driving_category',
        'registration_date',
    )
    search_fields = (
        'admission_number',
        'full_name',
        'national_id_passport',
        'phone_number',
        'email',
    )
    list_filter = (
        'gender',
        'driving_category',
        'registration_date',
    )
    ordering = ('-registration_date',)
    readonly_fields = ('registration_date',)


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'instructor_licence_number',
        'phone_number',
        'email',
        'national_id_passport',
        'gender',
        'driving_licence_number',
        'user',
        'registration_date',
    )
    search_fields = (
        'full_name',
        'instructor_licence_number',
        'phone_number',
        'email',
        'national_id_passport',
        'driving_licence_number',
        'user__username',
    )
    list_filter = (
        'gender',
        'registration_date',
    )
    ordering = ('-registration_date',)
    readonly_fields = ('registration_date',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'date',
        'sign_in_time',
        'status',
        'confirmed_by',
        'confirmation_time',
    )
    list_filter = ('status', 'date')
    search_fields = (
        'student__admission_number',
        'student__full_name',
        'student__national_id_passport',
        'confirmed_by__username',
    )
    ordering = ('-date', '-sign_in_time')
