from django.db import models
from django.conf import settings
from django.utils import timezone

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

DRIVING_CATEGORY_CHOICES = [
    ('A1', 'A1 - Light motorcycle'),
    ('A2', 'A2 - Motorcycle'),
    ('A3', 'A3 - Motorcycle (commercial)'),
    ('B1', 'B1 - Automatic car'),
    ('B2', 'B2 - Manual car'),
    ('B3', 'B3 - Professional light vehicle'),
    ('C1', 'C1 - Light truck'),
    ('C', 'C - Heavy truck'),
    ('CE', 'CE - Heavy truck + trailer'),
    ('D1', 'D1 - Small passenger vehicle'),
    ('D2', 'D2 - Medium passenger vehicle'),
    ('D', 'D - Large passenger vehicle'),
    ('E', 'E - Special/professional'),
]


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student')
    admission_number = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    national_id_passport = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    driving_category = models.CharField(max_length=3, choices=DRIVING_CATEGORY_CHOICES, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='archived_students')

    def __str__(self):
        return f"{self.full_name} ({self.admission_number})"


class Instructor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='instructor')
    full_name = models.CharField(max_length=200)
    instructor_licence_number = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    national_id_passport = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    driving_licence_number = models.CharField(max_length=100, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='archived_instructors')

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('AWAITING', 'Awaiting Confirmation'),
        ('CONFIRMED', 'Confirmed Present'),
        ('DECLINED', 'Declined / Did Not Attend'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.localdate)
    sign_in_time = models.TimeField(default=timezone.localtime)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AWAITING')
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='confirmed_attendances')
    confirmation_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date', '-sign_in_time']

    def __str__(self):
        return f"{self.student.admission_number} - {self.date} - {self.get_status_display()}"
