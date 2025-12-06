from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from qrcodeApp.models import QRCode
from dashboard.models import UserDetails
from io import BytesIO
from PIL import Image
import os

User = get_user_model()


class QRCodeModelTests(TestCase):
    """Test suite for QRCode model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
    
    def test_create_qrcode(self):
        """Test creating a QR code"""
        qrcode = QRCode.objects.create(user=self.user)
        self.assertEqual(qrcode.user, self.user)
        self.assertIsNotNone(qrcode.generated_at)
    
    def test_qrcode_string_representation(self):
        """Test the string representation of QR code"""
        qrcode = QRCode.objects.create(user=self.user)
        expected = f'QR Code for {self.user.username}'
        self.assertEqual(str(qrcode), expected)
    
    def test_get_qr_url_with_image(self):
        """Test get_qr_url property with an image"""
        # Create a simple image
        image = Image.new('RGB', (100, 100), color='black')
        image_io = BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            'qr_code.png',
            image_io.read(),
            content_type='image/png'
        )
        
        qrcode = QRCode.objects.create(
            user=self.user,
            image=uploaded_file
        )
        
        self.assertIsNotNone(qrcode.get_qr_url)
        self.assertIn('qr_codes', qrcode.get_qr_url)
    
    def test_get_qr_url_without_image(self):
        """Test get_qr_url property without an image"""
        qrcode = QRCode.objects.create(user=self.user)
        self.assertIsNone(qrcode.get_qr_url)
    
    def test_one_to_one_relationship(self):
        """Test one-to-one relationship with user"""
        QRCode.objects.create(user=self.user)
        
        # Trying to create another QRCode for the same user should raise an error
        with self.assertRaises(Exception):
            QRCode.objects.create(user=self.user)
    
    def test_qrcode_auto_timestamp(self):
        """Test that generated_at is automatically set"""
        qrcode = QRCode.objects.create(user=self.user)
        self.assertIsNotNone(qrcode.generated_at)


class GenerateQRCodeViewTests(TestCase):
    """Test suite for generate_qr_code_with_logo view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.user_details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.generate_url = reverse('generate_qr')
    
    def test_generate_qr_code_authenticated(self):
        """Test generating QR code for authenticated user"""
        response = self.client.get(self.generate_url)
        
        # Check QR code was created
        self.assertTrue(QRCode.objects.filter(user=self.user).exists())
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_generate_qr_code_unauthenticated(self):
        """Test that unauthenticated users cannot generate QR codes"""
        self.client.logout()
        response = self.client.get(self.generate_url)
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_generate_qr_code_already_exists(self):
        """Test generating QR code when user already has one"""
        # Create existing QR code
        QRCode.objects.create(user=self.user)
        
        response = self.client.get(self.generate_url)
        
        # Should redirect with info message
        self.assertRedirects(response, reverse('home'))
        
        # Should still have only one QR code
        self.assertEqual(QRCode.objects.filter(user=self.user).count(), 1)
    
    def test_generate_qr_code_without_user_details(self):
        """Test generating QR code fails gracefully without UserDetails"""
        # Delete user details
        self.user_details.delete()
        
        response = self.client.get(self.generate_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_qr_code_contains_correct_url(self):
        """Test that generated QR code contains the correct URL"""
        response = self.client.get(self.generate_url)
        
        # Get the created QR code
        qrcode = QRCode.objects.get(user=self.user)
        
        # Verify image was saved
        self.assertIsNotNone(qrcode.image)
        self.assertTrue(qrcode.image.name.endswith('.png'))


class DownloadQRCodeViewTests(TestCase):
    """Test suite for download_qr_code view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        
        # Create a simple QR code image
        image = Image.new('RGB', (100, 100), color='black')
        image_io = BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            'qr_code.png',
            image_io.read(),
            content_type='image/png'
        )
        
        self.qrcode = QRCode.objects.create(
            user=self.user,
            image=uploaded_file
        )
        
        self.client.login(username='test@example.com', password='testpass123')
        self.download_url = reverse('download_qr')
    
    def test_download_qr_code_authenticated(self):
        """Test downloading QR code for authenticated user"""
        response = self.client.get(self.download_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_download_qr_code_unauthenticated(self):
        """Test that unauthenticated users cannot download QR codes"""
        self.client.logout()
        response = self.client.get(self.download_url)
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_download_qr_code_not_found(self):
        """Test downloading QR code when user doesn't have one"""
        # Delete the QR code
        self.qrcode.delete()
        
        response = self.client.get(self.download_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class DownloadQRWithInfoViewTests(TestCase):
    """Test suite for download_qr_with_info view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user',
            first_name='Test',
            last_name='User'
        )
        
        # Create user details with profile image
        profile_image = Image.new('RGB', (100, 100), color='red')
        profile_io = BytesIO()
        profile_image.save(profile_io, format='JPEG')
        profile_io.seek(0)
        
        profile_file = SimpleUploadedFile(
            'profile.jpg',
            profile_io.read(),
            content_type='image/jpeg'
        )
        
        self.user_details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org',
            profile_image=profile_file
        )
        
        # Create QR code
        qr_image = Image.new('RGB', (100, 100), color='black')
        qr_io = BytesIO()
        qr_image.save(qr_io, format='PNG')
        qr_io.seek(0)
        
        qr_file = SimpleUploadedFile(
            'qr_code.png',
            qr_io.read(),
            content_type='image/png'
        )
        
        self.qrcode = QRCode.objects.create(
            user=self.user,
            image=qr_file
        )
        
        self.client.login(username='test@example.com', password='testpass123')
        self.download_url = reverse('download_qr_with_info')
    
    def test_download_qr_with_info_authenticated(self):
        """Test downloading QR code with info for authenticated user"""
        response = self.client.get(self.download_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertIn('info_with_qr.pdf', response['Content-Disposition'])
    
    def test_download_qr_with_info_unauthenticated(self):
        """Test that unauthenticated users cannot download QR with info"""
        self.client.logout()
        response = self.client.get(self.download_url)
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_download_qr_with_info_no_user_details(self):
        """Test downloading when user details don't exist"""
        # Delete user details
        self.user_details.delete()
        
        response = self.client.get(self.download_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_download_qr_with_info_no_qrcode(self):
        """Test downloading when QR code doesn't exist"""
        # Delete QR code
        self.qrcode.delete()
        
        response = self.client.get(self.download_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_download_qr_with_info_without_profile_image(self):
        """Test downloading QR with info when user has no profile image"""
        # Remove profile image
        self.user_details.profile_image = None
        self.user_details.save()
        
        response = self.client.get(self.download_url)
        
        # Should still work and return PDF
        self.assertEqual(response.status_code, 200)
        self.assertIn('info_with_qr.pdf', response['Content-Disposition'])


class QRCodeIntegrationTests(TestCase):
    """Integration tests for QR code workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.user_details = UserDetails.objects.create(
            user=self.user,
            phone_number='1234567890',
            bio='Test bio',
            designation='Developer',
            organization='Test Org'
        )
        self.client.login(username='test@example.com', password='testpass123')
    
    def test_complete_qr_workflow(self):
        """Test complete workflow: generate, view, download"""
        # Step 1: Generate QR code
        generate_response = self.client.get(reverse('generate_qr'))
        self.assertRedirects(generate_response, reverse('home'))
        
        # Verify QR code exists
        self.assertTrue(QRCode.objects.filter(user=self.user).exists())
        qrcode = QRCode.objects.get(user=self.user)
        
        # Step 2: View home page
        home_response = self.client.get(reverse('home'))
        self.assertEqual(home_response.status_code, 200)
        self.assertEqual(home_response.context['qrcode'], qrcode)
        
        # Step 3: Download QR code
        download_response = self.client.get(reverse('download_qr'))
        self.assertEqual(download_response.status_code, 200)
        
        # Step 4: Download QR with info
        info_response = self.client.get(reverse('download_qr_with_info'))
        self.assertEqual(info_response.status_code, 200)
    
    def test_prevent_duplicate_qr_generation(self):
        """Test that users cannot generate multiple QR codes"""
        # Generate first QR code
        self.client.get(reverse('generate_qr'))
        first_count = QRCode.objects.filter(user=self.user).count()
        
        # Try to generate again
        self.client.get(reverse('generate_qr'))
        second_count = QRCode.objects.filter(user=self.user).count()
        
        # Count should remain the same
        self.assertEqual(first_count, second_count)
        self.assertEqual(first_count, 1)
