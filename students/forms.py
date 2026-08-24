from django import forms
from django.contrib.auth import get_user_model
from .models import Instructor, Student


class StudentRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))

    class Meta:
        model = Student
        fields = [
            'admission_number',
            'full_name',
            'phone_number',
            'email',
            'national_id_passport',
            'gender',
            'driving_category',
        ]

        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: DR100'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'national_id_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'driving_category': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match')
        return cleaned

    def save(self, commit=True):
        User = get_user_model()
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['admission_number'],
            password=data['password1'],
            email=data.get('email', '')
        )
        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
        return student


class StudentProfileForm(forms.ModelForm):
    # Optional password fields to allow changing the linked user's password
    new_password1 = forms.CharField(
        label='New password',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}),
        help_text='Leave blank to keep the current password.'
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    class Meta:
        model = Student
        fields = [
            'admission_number',
            'full_name',
            'phone_number',
            'email',
            'national_id_passport',
            'gender',
            'driving_category',
        ]
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: DR100'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'national_id_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'driving_category': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 or p2:
            # if one provided, require both and match
            if not p1 or not p2:
                raise forms.ValidationError('Both password fields are required to change the password.')
            if p1 != p2:
                raise forms.ValidationError('New passwords do not match.')
        return cleaned

    def save(self, commit=True):
        student = super().save(commit=False)
        # keep user username/email in sync
        if getattr(student, 'user', None):
            student.user.username = student.admission_number
            student.user.email = student.email
            # if password fields provided, update password on the linked user
            new_pw = self.cleaned_data.get('new_password1')
            if new_pw:
                student.user.set_password(new_pw)
                # save password together with username/email
                student.user.save(update_fields=None)
            else:
                student.user.save(update_fields=['username', 'email'])
        if commit:
            student.save()
        return student


class AdminUserCreateForm(forms.Form):
    ROLE_CHOICES = [('student', 'Student'), ('instructor', 'Instructor')]

    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='student', widget=forms.Select(attrs={'class': 'form-select'}))
    username = forms.CharField(label='Username', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    full_name = forms.CharField(label='Full Name', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    admission_number = forms.CharField(label='Admission Number', required=False, max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: DR100'}))
    phone_number = forms.CharField(label='Phone Number', required=False, max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    national_id_passport = forms.CharField(label='National ID / Passport', required=False, max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport'}))
    gender = forms.ChoiceField(label='Gender', choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    driving_category = forms.ChoiceField(label='Driving Category', required=False, choices=[('', 'Select Category')], widget=forms.Select(attrs={'class': 'form-select'}))
    instructor_licence_number = forms.CharField(label='Instructor Licence Number', required=False, max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Instructor Licence Number'}))
    driving_licence_number = forms.CharField(label='Driving Licence Number', required=False, max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Driving Licence Number'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driving_category'].choices = [('', 'Select Category')] + list(Student._meta.get_field('driving_category').choices)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match')

        # username uniqueness check
        username = cleaned.get('username')
        User = get_user_model()
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError({'username': 'That username is already taken. Please choose another.'})

        role = cleaned.get('role')
        if role == 'student':
            if not cleaned.get('admission_number'):
                raise forms.ValidationError('Admission number is required for student users.')
            if not cleaned.get('full_name'):
                raise forms.ValidationError('Full name is required for student users.')
            # ensure admission_number is unique among students
            adm = cleaned.get('admission_number')
            if adm and Student.objects.filter(admission_number=adm).exists():
                raise forms.ValidationError({'admission_number': 'This admission number is already in use.'})
        elif role == 'instructor':
            if not cleaned.get('full_name'):
                raise forms.ValidationError('Full name is required for instructor users.')

        return cleaned

    def save(self, commit=True):
        User = get_user_model()
        data = self.cleaned_data
        role = data['role']

        user = User.objects.create_user(
            username=data['username'],
            password=data['password1'],
            email=data.get('email', '')
        )
        user.is_staff = role == 'instructor'
        if commit:
            user.save()

        if role == 'student':
            Student.objects.create(
                user=user,
                admission_number=data['admission_number'],
                full_name=data['full_name'],
                phone_number=data.get('phone_number', ''),
                email=data.get('email', ''),
                national_id_passport=data.get('national_id_passport', ''),
                gender=data.get('gender', ''),
                driving_category=data.get('driving_category', ''),
            )
        else:
            Instructor.objects.create(
                user=user,
                full_name=data['full_name'],
                instructor_licence_number=data.get('instructor_licence_number', ''),
                phone_number=data.get('phone_number', ''),
                email=data.get('email', ''),
                national_id_passport=data.get('national_id_passport', ''),
                gender=data.get('gender', ''),
                driving_licence_number=data.get('driving_licence_number', ''),
            )

        return user


class InstructorRegistrationForm(forms.Form):
    full_name = forms.CharField(label='Full Name', max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    instructor_licence_number = forms.CharField(label='Instructor Licence Number', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Instructor Licence Number'}))
    phone_number = forms.CharField(label='Phone Number', max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    national_id_passport = forms.CharField(label='National ID / Passport', max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport'}))
    gender = forms.ChoiceField(label='Gender', choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    driving_licence_number = forms.CharField(label='Driving Licence Number', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Driving Licence Number'}))
    username = forms.CharField(label='Username', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match')
        return cleaned

    def save(self, commit=True):
        """Create a user and instructor from the registration form data."""
        User = get_user_model()
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password1'],
            email=data.get('email', '')
        )
        # set basic name fields if provided
        full_name = data.get('full_name', '').strip()
        if full_name:
            name_parts = full_name.split(None, 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.is_staff = True
        if commit:
            user.save()

        Instructor.objects.create(
            user=user,
            full_name=full_name,
            instructor_licence_number=data.get('instructor_licence_number', ''),
            phone_number=data.get('phone_number', ''),
            email=data.get('email', ''),
            national_id_passport=data.get('national_id_passport', ''),
            gender=data.get('gender', ''),
            driving_licence_number=data.get('driving_licence_number', ''),
        )
        return user


class InstructorProfileForm(forms.ModelForm):
    username = forms.CharField(label='Username', max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))

    class Meta:
        model = Instructor
        fields = [
            'full_name',
            'instructor_licence_number',
            'phone_number',
            'email',
            'national_id_passport',
            'gender',
            'driving_licence_number',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'instructor_licence_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Instructor Licence Number'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'national_id_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'driving_licence_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Driving Licence Number'}),
        }

    def __init__(self, *args, **kwargs):
        # accept an instructor instance to populate username
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'user', None):
            self.fields['username'].initial = self.instance.user.username

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = get_user_model()
        if User.objects.filter(username=username).exclude(pk=getattr(self.instance.user, 'pk', None)).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def save(self, commit=True):
        instructor = super().save(commit=False)
        # update linked user
        if getattr(instructor, 'user', None):
            user = instructor.user
            user.username = self.cleaned_data.get('username')
            user.email = instructor.email
            user.save(update_fields=['username', 'email'])
        if commit:
            instructor.save()
        return instructor

    def save(self, commit=True):
        instructor = super().save(commit=False)
        # update linked user
        if getattr(instructor, 'user', None):
            user = instructor.user
            user.username = self.cleaned_data.get('username')
            user.email = instructor.email
            user.save(update_fields=['username', 'email'])
        if commit:
            instructor.save()
        return instructor


class AdminUserPasswordChangeForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label='User',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
    )
    new_password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.order_by('username')

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned
