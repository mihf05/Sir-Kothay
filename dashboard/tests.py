from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from dashboard.models import UserDetails
from broadcast.models import BroadcastMessage
from qrcodeApp.models import QRCode
from io import BytesIO
from PIL import Image

User = get_user_model()


class UserDetailsModelTests(TestCase):
    """Test suite for UserDetails model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
    
    def test_create_user_details(self):
        """Test creating user details"""
        details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        self.assertEqual(details.user, self.user)
        self.assertEqual(details.phone_number, '1234567890')
        self.assertEqual(details.bio, 'Test bio')
        self.assertEqual(details.designation, 'Developer')
        self.assertEqual(details.organization, 'Test Org')
    
    def test_user_details_string_representation(self):
        """Test the string representation of user details"""
        details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        expected = 'Developer at Test Org'
        self.assertEqual(str(details), expected)
    
    def test_slug_auto_generation(self):
        """Test that slug is automatically generated on save"""
        details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        self.assertIsNotNone(details._slug)
        self.assertIn(self.user.username, details._slug)
    
    def test_slug_property(self):
        """Test the slug property"""
        details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        slug = details.slug
        self.assertIsNotNone(slug)
        self.assertEqual(slug, details._slug)
    
    def test_slug_unique(self):
        """Test that slug is unique"""
        details1 = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            username='test_user'
        )
        
        details2 = UserDetails.objects.create(
            user=user2,
            phone_number='0987654321',
            bio='Test bio 2',
            designation='Designer',
            organization='Test Org 2'
        )
        
        self.assertNotEqual(details1._slug, details2._slug)
    
    def test_get_image_url_with_image(self):
        """Test get_image_url property with an image"""
        # Create a simple image
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            'test_image.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org',
            profile_image=uploaded_file
        )
        
        self.assertIsNotNone(details.get_image_url)
        self.assertIn('profile_images', details.get_image_url)
    
    def test_get_image_url_without_image(self):
        """Test get_image_url property without an image"""
        details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        
        self.assertIsNone(details.get_image_url)
    
    def test_one_to_one_relationship(self):
        """Test one-to-one relationship with user"""
        UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        
        # Trying to create another UserDetails for the same user should raise an error
        with self.assertRaises(Exception):
            UserDetails.objects.create(
                user=self.user,
                phone_number='0987654321',
                bio='Another bio',
                designation='Manager',
                organization='Another Org'
            )


class HomeViewTests(TestCase):
    """Test suite for home_view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.home_url = reverse('home')
    
    def test_home_view_authenticated(self):
        """Test home view for authenticated user"""
        response = self.client.get(self.home_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')
    
    def test_home_view_unauthenticated(self):
        """Test home view redirects unauthenticated users"""
        self.client.logout()
        response = self.client.get(self.home_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_home_view_creates_user_details(self):
        """Test that home view creates UserDetails if it doesn't exist"""
        response = self.client.get(self.home_url)
        
        self.assertTrue(UserDetails.objects.filter(user=self.user).exists())
    
    def test_home_view_with_messages(self):
        """Test home view displays user's broadcast messages"""
        message = BroadcastMessage.objects.create(
            user=self.user,
            message='Test message'
        )
        
        response = self.client.get(self.home_url)
        
        self.assertIn('messages', response.context)
        self.assertIn(message, response.context['messages'])
    
    def test_home_view_with_qrcode(self):
        """Test home view with QR code"""
        qrcode = QRCode.objects.create(user=self.user)
        
        response = self.client.get(self.home_url)
        
        self.assertEqual(response.context['qrcode'], qrcode)
    
    def test_home_view_without_qrcode(self):
        """Test home view without QR code"""
        response = self.client.get(self.home_url)
        
        self.assertIsNone(response.context['qrcode'])
    
    def test_home_view_username_display(self):
        """Test that username with underscores is displayed with spaces"""
        response = self.client.get(self.home_url)
        
        self.assertEqual(response.context['username'], 'test user')


class ProfileViewTests(TestCase):
    """Test suite for profile_view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.profile_url = reverse('profile')
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/profile.html')
    
    def test_profile_view_unauthenticated(self):
        """Test profile view redirects unauthenticated users"""
        self.client.logout()
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_profile_view_creates_user_details(self):
        """Test that profile view creates UserDetails if it doesn't exist"""
        response = self.client.get(self.profile_url)
        
        self.assertTrue(UserDetails.objects.filter(user=self.user).exists())
    
    def test_profile_view_context_data(self):
        """Test profile view context contains required data"""
        response = self.client.get(self.profile_url)
        
        self.assertIn('user', response.context)
        self.assertIn('userd', response.context)
        self.assertIn('messages', response.context)
        self.assertIn('username', response.context)


class UserDetailViewTests(TestCase):
    """Test suite for user_detail_view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.update_url = reverse('user_details_update')
    
    def test_update_user_details_post(self):
        """Test updating user details via POST"""
        data = {
            'username': 'updated_user',
            'email': 'updated@example.com',
            'bio': 'Updated bio',
            'organization': 'Updated Org',
            'designation': 'Updated Designation',
            'phone_number': '9876543210'
        }
        response = self.client.post(self.update_url, data)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.username, 'updated_user')
        self.assertEqual(self.user.email, 'updated@example.com')
        
        # Check UserDetails was created/updated
        details = UserDetails.objects.get(user=self.user)
        self.assertEqual(details.bio, 'Updated bio')
        self.assertEqual(details.organization, 'Updated Org')
        self.assertEqual(details.designation, 'Updated Designation')
        self.assertEqual(details.phone_number, '9876543210')
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_update_with_profile_image(self):
        """Test updating profile with image"""
        # Create a simple image
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            'profile.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'bio': 'Test bio',
            'organization': 'Test Org',
            'designation': 'Developer',
            'phone_number': '1234567890',
            'profile_image': uploaded_file
        }
        response = self.client.post(self.update_url, data)
        
        # Check image was saved
        details = UserDetails.objects.get(user=self.user)
        self.assertTrue(details.profile_image)
        self.assertIn('profile_images', details.profile_image.name)
    
    def test_update_user_details_get_redirects(self):
        """Test GET request redirects to home"""
        response = self.client.get(self.update_url)
        
        self.assertRedirects(response, reverse('home'))
    
    def test_update_user_details_unauthenticated(self):
        """Test that unauthenticated users cannot update details"""
        self.client.logout()
        data = {
            'username': 'hacker',
            'email': 'hacker@example.com'
        }
        response = self.client.post(self.update_url, data)
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_update_creates_user_details_if_not_exists(self):
        """Test that update creates UserDetails if it doesn't exist"""
        # Ensure no UserDetails exists
        UserDetails.objects.filter(user=self.user).delete()
        
        data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'bio': 'New bio',
            'organization': 'New Org',
            'designation': 'New Designation',
            'phone_number': '1234567890'
        }
        response = self.client.post(self.update_url, data)
        
        # Check UserDetails was created
        self.assertTrue(UserDetails.objects.filter(user=self.user).exists())
    
    def test_partial_update(self):
        """Test updating only some fields"""
        # Create initial details
        UserDetails.objects.create(
            user=self.user,
            phone_number='1111111111',
            bio='Original bio',
            designation='Original',
            organization='Original Org'
        )
        
        data = {
            'bio': 'Updated bio only'
        }
        response = self.client.post(self.update_url, data)
        
        # Refresh from database
        details = UserDetails.objects.get(user=self.user)
        
        # Bio should be updated
        self.assertEqual(details.bio, 'Updated bio only')
        # Other fields should remain unchanged
        self.assertEqual(details.phone_number, '1111111111')
        self.assertEqual(details.designation, 'Original')
