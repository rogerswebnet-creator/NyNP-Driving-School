from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Student, Attendance, Instructor
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch

User = get_user_model()

class StudentRegistrationAndAttendanceTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_student_registration_creates_user_and_student(self):
        data = {
            'admission_number': 'DRTEST1',
            'full_name': 'Test Student',
            'phone_number': '0710000000',
            'email': 'test@student.local',
            'national_id_passport': '12345678',
            'gender': 'M',
            'driving_category': 'B2',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
        }
        resp = self.client.post(reverse('register'), data)
        # should redirect to dashboard
        self.assertEqual(resp.status_code, 302)
        user = User.objects.filter(username='DRTEST1').first()
        self.assertIsNotNone(user)
        student = Student.objects.filter(admission_number='DRTEST1').first()
        self.assertIsNotNone(student)
        self.assertEqual(student.user, user)

    def test_student_can_sign_in_once_per_day(self):
        # create student
        user = User.objects.create_user(username='DRS1', password='pw12345')
        student = Student.objects.create(user=user, admission_number='DRS1', full_name='S1')
        # login
        self.client.login(username='DRS1', password='pw12345')
        resp = self.client.post(reverse('sign_in_today'))
        self.assertEqual(resp.status_code, 302)
        today = timezone.localdate()
        attendances = Attendance.objects.filter(student=student, date=today)
        self.assertEqual(attendances.count(), 1)
        # second sign-in should not create a new record
        resp2 = self.client.post(reverse('sign_in_today'))
        self.assertEqual(Attendance.objects.filter(student=student, date=today).count(), 1)

    def test_student_cannot_sign_in_outside_allowed_hours(self):
        user = User.objects.create_user(username='DRSOUT', password='pw12345')
        student = Student.objects.create(user=user, admission_number='DRSOUT', full_name='S Outside Hours')
        self.client.login(username='DRSOUT', password='pw12345')

        with patch('students.views.timezone.localtime', return_value=datetime(2026, 1, 1, 6, 59, 0)):
            resp = self.client.post(reverse('sign_in_today'))

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Attendance.objects.filter(student=student, date=timezone.localdate()).exists())

    def test_instructor_confirm_attendance(self):
        # create student and attendance
        suser = User.objects.create_user(username='DRS2', password='pw12345')
        student = Student.objects.create(user=suser, admission_number='DRS2', full_name='S2')
        today = timezone.localdate()
        att = Attendance.objects.create(student=student, date=today, sign_in_time=timezone.localtime().time())
        # create instructor
        instructor = User.objects.create_user(username='instr1', password='pwinst')
        instructor.is_staff = True
        instructor.save()
        # login instructor via instructor login view
        self.client.login(username='instr1', password='pwinst')
        confirm_url = reverse('confirm_attendance', args=[att.id])
        resp = self.client.post(confirm_url)
        self.assertEqual(resp.status_code, 302)
        att.refresh_from_db()
        self.assertEqual(att.status, 'CONFIRMED')
        self.assertEqual(att.confirmed_by, instructor)

    def test_instructor_can_decline_student_attendance(self):
        suser = User.objects.create_user(username='DRSDECL', password='pw12345')
        student = Student.objects.create(user=suser, admission_number='DRSDECL', full_name='S Decline')
        today = timezone.localdate()
        att = Attendance.objects.create(student=student, date=today, sign_in_time=timezone.localtime().time(), status='AWAITING')

        instructor = User.objects.create_user(username='instr_decline', password='pwinst')
        instructor.is_staff = True
        instructor.save()
        self.client.login(username='instr_decline', password='pwinst')

        resp = self.client.post(reverse('decline_attendance', args=[att.id]))
        self.assertEqual(resp.status_code, 302)
        att.refresh_from_db()
        self.assertEqual(att.status, 'DECLINED')
        self.assertEqual(att.confirmed_by, instructor)

    def test_declined_attendance_shows_student_message_on_dashboard(self):
        user = User.objects.create_user(username='DRDECLMSG', password='pw12345')
        student = Student.objects.create(user=user, admission_number='DRDECLMSG', full_name='S Declined Message')
        Attendance.objects.create(student=student, date=timezone.localdate(), sign_in_time='08:00:00', status='DECLINED')

        self.client.login(username='DRDECLMSG', password='pw12345')
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Attendance Request Declined')
        self.assertContains(resp, 'Please wait for the next sign-up window.')

    def test_declined_attendance_is_not_counted_in_today_total(self):
        instructor = User.objects.create_user(username='instr_total', password='pwinst')
        instructor.is_staff = True
        instructor.save()
        self.client.login(username='instr_total', password='pwinst')

        student_user = User.objects.create_user(username='DRTOTAL1', password='pw12345')
        student = Student.objects.create(user=student_user, admission_number='DRTOTAL1', full_name='Total Student 1')
        Attendance.objects.create(student=student, date=timezone.localdate(), sign_in_time='08:00:00', status='AWAITING')
        declined_student_user = User.objects.create_user(username='DRTOTAL2', password='pw12345')
        declined_student = Student.objects.create(user=declined_student_user, admission_number='DRTOTAL2', full_name='Total Student 2')
        Attendance.objects.create(student=declined_student, date=timezone.localdate(), sign_in_time='09:00:00', status='DECLINED')

        resp = self.client.get(reverse('instructor_attendance'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_signins_count'], 1)
        self.assertEqual(resp.context['declined_count'], 1)

    def test_instructor_attendance_search_filters_by_student_date_and_status(self):
        instructor = User.objects.create_user(username='instr_search', password='pwinst')
        instructor.is_staff = True
        instructor.save()
        self.client.login(username='instr_search', password='pwinst')

        student_user = User.objects.create_user(username='DR100', password='pw12345')
        student = Student.objects.create(user=student_user, admission_number='DR100', full_name='Search Student')

        older_date = timezone.localdate() - timedelta(days=3)
        other_date = older_date + timedelta(days=1)
        Attendance.objects.create(student=student, date=older_date, status='AWAITING', sign_in_time='08:00:00')
        Attendance.objects.create(student=student, date=other_date, status='CONFIRMED', sign_in_time='08:10:00')
        Attendance.objects.create(student=student, date=timezone.localdate(), status='CONFIRMED', sign_in_time='09:00:00')

        resp = self.client.get(reverse('instructor_attendance'), {
            'q': 'DR100',
            'date': other_date.isoformat(),
            'status': 'CONFIRMED',
        })

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['attendances'].values_list('id', flat=True)), [
            Attendance.objects.get(student=student, date=other_date, status='CONFIRMED').id
        ])
        self.assertEqual(resp.context['status'], 'CONFIRMED')
        self.assertEqual(resp.context['selected_date'], other_date.isoformat())

    def test_password_reset_request_sends_user_to_done_page(self):
        user = User.objects.create_user(username='DRRESET', password='pw12345', email='reset@example.com')
        Student.objects.create(user=user, admission_number='DRRESET', full_name='Reset User')

        resp = self.client.post(reverse('password_reset'), {'email': 'reset@example.com'})
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('password_reset_done'))

    def test_admin_can_change_any_users_password(self):
        admin = User.objects.create_superuser(username='adminpasschg', email='adminpasschg@test.local', password='adminpass')
        self.client.login(username='adminpasschg', password='adminpass')

        target_user = User.objects.create_user(username='DRPASSUSER', password='oldpass123')
        resp = self.client.post(reverse('admin_change_user_password'), {
            'user': target_user.id,
            'new_password1': 'newStrongPass456',
            'new_password2': 'newStrongPass456',
        })
        self.assertEqual(resp.status_code, 302)
        target_user.refresh_from_db()
        self.assertTrue(target_user.check_password('newStrongPass456'))

    def test_admin_can_create_instructor_account(self):
        admin = User.objects.create_superuser(username='admininstrcreate', email='admininstrcreate@test.local', password='adminpass')
        self.client.login(username='admininstrcreate', password='adminpass')

        resp = self.client.post(reverse('create_user'), {
            'role': 'instructor',
            'username': 'instr_admin_create',
            'email': 'instr_admin_create@test.local',
            'full_name': 'Admin Created Instructor',
            'phone_number': '0712345678',
            'national_id_passport': 'ID987654',
            'gender': 'F',
            'instructor_licence_number': 'INST-1001',
            'driving_licence_number': 'DL-1001',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='instr_admin_create')
        self.assertTrue(user.is_staff)
        self.assertTrue(Instructor.objects.filter(user=user, full_name='Admin Created Instructor').exists())

    def test_admin_can_archive_and_delete_instructor(self):
        admin = User.objects.create_superuser(username='admininstrmanage', email='admininstrmanage@test.local', password='adminpass')
        self.client.login(username='admininstrmanage', password='adminpass')

        user = User.objects.create_user(username='instr_delete_me', password='pwinst')
        user.is_staff = True
        user.save()
        instructor = Instructor.objects.create(
            user=user,
            full_name='Archive Me Instructor',
            instructor_licence_number='INST-DELETE',
            phone_number='0700000000',
            email='delete@example.com',
            national_id_passport='IDDELETE',
            gender='M',
            driving_licence_number='DL-DELETE',
        )

        archive_resp = self.client.post(reverse('archive_instructor', args=[instructor.id]))
        self.assertEqual(archive_resp.status_code, 302)
        instructor.refresh_from_db()
        self.assertTrue(instructor.is_archived)
        self.assertFalse(instructor.user.is_staff)

        list_resp = self.client.get(reverse('admin_instructors_list'))
        self.assertNotIn(instructor, list_resp.context['instructors'])

        delete_resp = self.client.post(reverse('delete_instructor', args=[instructor.id]))
        self.assertEqual(delete_resp.status_code, 302)
        self.assertFalse(User.objects.filter(username='instr_delete_me').exists())
        self.assertFalse(Instructor.objects.filter(id=instructor.id).exists())

    def test_instructor_can_archive_completed_student(self):
        instructor = User.objects.create_user(username='instr_archive', password='pwinst')
        instructor.is_staff = True
        instructor.save()
        self.client.login(username='instr_archive', password='pwinst')

        student_user = User.objects.create_user(username='DRARCHIVE', password='pw12345')
        student = Student.objects.create(user=student_user, admission_number='DRARCHIVE', full_name='Completed Student')

        resp = self.client.post(reverse('archive_student', args=[student.id]))
        self.assertEqual(resp.status_code, 302)
        student.refresh_from_db()
        self.assertTrue(student.is_archived)
        self.assertIsNotNone(student.archived_at)
        self.assertEqual(student.archived_by, instructor)

        list_resp = self.client.get(reverse('students_list'))
        self.assertNotIn(student, list_resp.context['students'])

        archived_resp = self.client.get(reverse('archived_students_list'))
        self.assertContains(archived_resp, 'Archived Students')
        self.assertIn(student, archived_resp.context['students'])

        unarchive_resp = self.client.post(reverse('unarchive_student', args=[student.id]))
        self.assertEqual(unarchive_resp.status_code, 302)
        student.refresh_from_db()
        self.assertFalse(student.is_archived)
        self.assertIsNone(student.archived_at)
        self.assertIsNone(student.archived_by)

    def test_instructor_can_edit_and_delete_student_profile(self):
        instructor = User.objects.create_user(username='instr_edit', password='pwinst')
        instructor.is_staff = True
        instructor.save()
        self.client.login(username='instr_edit', password='pwinst')

        student_user = User.objects.create_user(username='DREDIT', password='pw12345')
        student = Student.objects.create(
            user=student_user,
            admission_number='DREDIT',
            full_name='Original Name',
            phone_number='0711111111',
            email='old@example.com',
            national_id_passport='IDOLD',
            gender='M',
            driving_category='B2',
        )

        edit_resp = self.client.post(reverse('edit_student_profile', args=[student.id]), {
            'admission_number': 'DREDIT2',
            'full_name': 'Updated Name',
            'phone_number': '0722222222',
            'email': 'new@example.com',
            'national_id_passport': 'IDNEW',
            'gender': 'F',
            'driving_category': 'B1',
        })
        self.assertEqual(edit_resp.status_code, 302)
        student.refresh_from_db()
        self.assertEqual(student.full_name, 'Updated Name')
        self.assertEqual(student.admission_number, 'DREDIT2')
        self.assertEqual(student.user.username, 'DREDIT2')

        delete_resp = self.client.post(reverse('delete_student', args=[student.id]))
        self.assertEqual(delete_resp.status_code, 302)
        self.assertFalse(Student.objects.filter(id=student.id).exists())
        self.assertFalse(User.objects.filter(username='DREDIT2').exists())

    def test_admin_dashboard_shows_live_statistics(self):
        admin = User.objects.create_superuser(username='adminuser', email='admin@test.local', password='adminpass')
        self.client.login(username='adminuser', password='adminpass')

        student_user = User.objects.create_user(username='student1', password='pw12345')
        Student.objects.create(user=student_user, admission_number='DRS3', full_name='Student Three')

        instructor_user = User.objects.create_user(username='instr2', password='pwinst2')
        instructor_user.is_staff = True
        instructor_user.save()

        today = timezone.localdate()
        Attendance.objects.create(student=Student.objects.create(user=User.objects.create_user(username='student2', password='pw12345'), admission_number='DRS4', full_name='Student Four'), date=today, status='AWAITING')
        Attendance.objects.create(student=Student.objects.create(user=User.objects.create_user(username='student3', password='pw12345'), admission_number='DRS5', full_name='Student Five'), date=today, status='CONFIRMED')

        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Students')
        self.assertContains(resp, 'Instructors')
        self.assertContains(resp, "Today's Attendance")
        self.assertContains(resp, 'Pending Confirmations')
        self.assertContains(resp, 'Awaiting')
        self.assertContains(resp, 'Confirmed')

    def test_admin_can_create_new_users(self):
        admin = User.objects.create_superuser(username='admincreate', email='admincreate@test.local', password='adminpass')
        self.client.login(username='admincreate', password='adminpass')

        resp = self.client.post(reverse('create_user'), {
            'role': 'student',
            'username': 'newstudent',
            'email': 'student@example.com',
            'full_name': 'New Student',
            'admission_number': 'DRNEW001',
            'phone_number': '0711222333',
            'national_id_passport': 'ID001',
            'gender': 'M',
            'driving_category': 'B2',
            'password1': 'studentpass',
            'password2': 'studentpass',
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='newstudent')
        self.assertTrue(Student.objects.filter(user=user, admission_number='DRNEW001').exists())

        resp = self.client.post(reverse('create_user'), {
            'role': 'instructor',
            'username': 'newinstr2',
            'email': 'instructor@example.com',
            'full_name': 'New Instructor',
            'phone_number': '0711222334',
            'national_id_passport': 'ID002',
            'gender': 'F',
            'instructor_licence_number': 'LIC002',
            'driving_licence_number': 'DL002',
            'password1': 'instrpass',
            'password2': 'instrpass',
        })
        self.assertEqual(resp.status_code, 302)
        instr_user = User.objects.get(username='newinstr2')
        self.assertTrue(instr_user.is_staff)
        self.assertTrue(Instructor.objects.filter(user=instr_user, full_name='New Instructor').exists())


class InstructorRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_instructor_registration_with_code(self):
        resp = self.client.post(reverse('instructor_register'), {
            'full_name': 'Instructor New',
            'instructor_licence_number': 'LIC123',
            'phone_number': '0712345678',
            'email': 'instr@test.local',
            'national_id_passport': 'ID1234',
            'gender': 'F',
            'driving_licence_number': 'DL1234',
            'username': 'newinstr',
            'password1': 'instrpass',
            'password2': 'instrpass',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        user = User.objects.filter(username='newinstr').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_staff)
        self.assertIsNotNone(Instructor.objects.filter(user=user).first())
        self.assertEqual(int(self.client.session.get('_auth_user_id')), user.id)
