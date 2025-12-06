from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from authApp.forms import EmailAuthenticationForm, RegisterForm, UserPasswordUpdateForm
from dashboard.models import UserDetails

User = get_user_model()


class CustomUserManagerTests(TestCase):
    """Test suite for CustomUserManager"""
    
    def test_create_user_with_email(self):
        """Test creating a regular user with email"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')
    
    def test_create_user_normalizes_email(self):
        """Test email normalization in user creation"""
        user = User.objects.create_user(
            email='test@EXAMPLE.COM',
            password='testpass123',
            username='test_user'
        )
        self.assertEqual(user.email, 'test@example.com')
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            username='admin_user'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class CustomUserModelTests(TestCase):
    """Test suite for CustomUser model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='john_doe'
        )
    
    def test_email_is_unique(self):
        """Test that email field is unique"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                password='anotherpass',
                username='another_user'
            )
    
    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email"""
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_readable_name_property(self):
        """Test readable_name property converts underscores to spaces and titlecases"""
        self.assertEqual(self.user.readable_name, 'John Doe')
    
    def test_readable_name_with_multiple_underscores(self):
        """Test readable_name with complex username"""
        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            username='john_paul_smith'
        )
        self.assertEqual(user.readable_name, 'John Paul Smith')


class RegisterFormTests(TestCase):
    """Test suite for RegisterForm"""
    
    def test_valid_registration_form(self):
        """Test form with valid data"""
        form_data = {
            'email': 'newuser@example.com',
            'username': 'New User',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_password_mismatch(self):
        """Test form validation when passwords don't match"""
        form_data = {
            'email': 'newuser@example.com',
            'username': 'New User',
            'password': 'securepass123',
            'confirm_password': 'differentpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_username_with_spaces_converted_to_underscores(self):
        """Test that spaces in username are converted to underscores"""
        form_data = {
            'email': 'newuser@example.com',
            'username': 'John Paul Smith',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'John_Paul_Smith')


class EmailAuthenticationFormTests(TestCase):
    """Test suite for EmailAuthenticationForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
    
    def test_valid_authentication_form(self):
        """Test form with valid credentials"""
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        form = EmailAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_nonexistent_email(self):
        """Test form validation with non-existent email"""
        form_data = {
            'username': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        form = EmailAuthenticationForm(data=form_data)
        self.assertFalse(form.is_valid())


class UserPasswordUpdateFormTests(TestCase):
    """Test suite for UserPasswordUpdateForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='oldpass123',
            username='test_user'
        )
    
    def test_valid_password_update(self):
        """Test form with valid password update"""
        form_data = {
            'current_password': 'oldpass123',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }
        form = UserPasswordUpdateForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_incorrect_current_password(self):
        """Test form validation with incorrect current password"""
        form_data = {
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }
        form = UserPasswordUpdateForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())


class RegisterViewTests(TestCase):
    """Test suite for register_view"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
    
    def test_register_view_get(self):
        """Test GET request to register view"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/register.html')
    
    def test_register_view_post_valid_data(self):
        """Test POST request with valid registration data"""
        form_data = {
            'email': 'newuser@example.com',
            'username': 'New User',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }
        response = self.client.post(self.register_url, data=form_data)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(UserDetails.objects.filter(user=user).exists())
    
    def test_register_view_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from register page"""
        user = User.objects.create_user(
            email='existing@example.com',
            password='testpass123',
            username='existing_user'
        )
        self.client.login(username='existing@example.com', password='testpass123')
        response = self.client.get(self.register_url)
        self.assertRedirects(response, reverse('home'))


class LoginViewTests(TestCase):
    """Test suite for login_view"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
    
    def test_login_view_get(self):
        """Test GET request to login view"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
    
    def test_login_view_post_valid_credentials(self):
        """Test POST request with valid login credentials"""
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data=form_data)
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class LogoutViewTests(TestCase):
    """Test suite for logout_view"""
    
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
    
    def test_logout_view_authenticated_user(self):
        """Test logout for authenticated user"""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(self.logout_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertRedirects(response, reverse('login'))
