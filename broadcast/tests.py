from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from broadcast.models import BroadcastMessage
from dashboard.models import UserDetails

User = get_user_model()


class BroadcastMessageModelTests(TestCase):
    """Test suite for BroadcastMessage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
    
    def test_create_broadcast_message(self):
        """Test creating a broadcast message"""
        message = BroadcastMessage.objects.create(
            user=self.user,
            message='Test broadcast message'
        )
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.message, 'Test broadcast message')
        self.assertTrue(message.active)
    
    def test_broadcast_message_string_representation(self):
        """Test the string representation of broadcast message"""
        message = BroadcastMessage.objects.create(
            user=self.user,
            message='This is a long test broadcast message that should be truncated'
        )
        expected = f'{self.user.username}: This is a long test b'
        self.assertEqual(str(message), expected)
    
    def test_save_deactivates_other_messages(self):
        """Test that saving active message deactivates other active messages"""
        message1 = BroadcastMessage.objects.create(
            user=self.user,
            message='First message',
            active=True
        )
        message2 = BroadcastMessage.objects.create(
            user=self.user,
            message='Second message',
            active=True
        )
        
        # Refresh message1 from database
        message1.refresh_from_db()
        
        # First message should now be inactive
        self.assertFalse(message1.active)
        # Second message should be active
        self.assertTrue(message2.active)
    
    def test_multiple_users_can_have_active_messages(self):
        """Test that different users can have their own active messages"""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            username='test_user2'
        )
        
        message1 = BroadcastMessage.objects.create(
            user=self.user,
            message='User 1 message',
            active=True
        )
        message2 = BroadcastMessage.objects.create(
            user=user2,
            message='User 2 message',
            active=True
        )
        
        # Both messages should remain active
        self.assertTrue(message1.active)
        self.assertTrue(message2.active)
    
    def test_inactive_message_save(self):
        """Test saving an inactive message doesn't affect other messages"""
        message1 = BroadcastMessage.objects.create(
            user=self.user,
            message='First message',
            active=True
        )
        message2 = BroadcastMessage.objects.create(
            user=self.user,
            message='Second message',
            active=False
        )
        
        # First message should still be active
        message1.refresh_from_db()
        self.assertTrue(message1.active)


class ShowBroadcastMessagesViewTests(TestCase):
    """Test suite for show_broadcast_messages view"""
    
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
        self.message = BroadcastMessage.objects.create(
            user=self.user,
            message='Active test message',
            active=True
        )
    
    def test_show_broadcast_messages_view(self):
        """Test viewing broadcast messages by slug"""
        url = reverse('show_broadcast_messages', kwargs={'user_slug': self.user_details.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'broadcast/message.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertEqual(response.context['active_messages'], self.message)
    
    def test_show_broadcast_messages_nonexistent_slug(self):
        """Test viewing broadcast messages with nonexistent slug"""
        url = reverse('show_broadcast_messages', kwargs={'user_slug': 'nonexistent-slug'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_show_broadcast_messages_no_active_message(self):
        """Test viewing when user has no active messages"""
        self.message.active = False
        self.message.save()
        
        url = reverse('show_broadcast_messages', kwargs={'user_slug': self.user_details.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['active_messages'])
    
    def test_username_display_with_underscores(self):
        """Test that username with underscores is displayed with spaces"""
        url = reverse('show_broadcast_messages', kwargs={'user_slug': self.user_details.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.context['username'], 'test user')


class AddBroadcastMessageViewTests(TestCase):
    """Test suite for add_broadcast_message view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.add_url = reverse('add_broadcast_message')
    
    def test_add_broadcast_message_valid(self):
        """Test adding a valid broadcast message"""
        response = self.client.post(self.add_url, {'message': 'New test message'})
        
        # Check message was created
        self.assertTrue(BroadcastMessage.objects.filter(
            user=self.user,
            message='New test message'
        ).exists())
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_add_broadcast_message_empty(self):
        """Test adding an empty broadcast message"""
        response = self.client.post(self.add_url, {'message': ''})
        
        # Check no message was created
        self.assertEqual(BroadcastMessage.objects.count(), 0)
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_add_broadcast_message_unauthenticated(self):
        """Test that unauthenticated users cannot add messages"""
        self.client.logout()
        response = self.client.post(self.add_url, {'message': 'New test message'})
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_add_broadcast_message_whitespace_only(self):
        """Test adding a message with only whitespace"""
        response = self.client.post(self.add_url, {'message': '   '})
        
        # Message with only whitespace should be accepted (truthiness check passes)
        self.assertTrue(BroadcastMessage.objects.filter(user=self.user).exists())


class DeleteBroadcastMessageViewTests(TestCase):
    """Test suite for delete_broadcast_message view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.message = BroadcastMessage.objects.create(
            user=self.user,
            message='Test message'
        )
    
    def test_delete_own_message(self):
        """Test deleting user's own message"""
        url = reverse('delete_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.get(url)
        
        # Check message was deleted
        self.assertFalse(BroadcastMessage.objects.filter(id=self.message.id).exists())
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_delete_nonexistent_message(self):
        """Test deleting a nonexistent message"""
        url = reverse('delete_broadcast_message', kwargs={'message_id': 99999})
        response = self.client.get(url)
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_delete_another_users_message(self):
        """Test that users cannot delete other users' messages"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            username='other_user'
        )
        other_message = BroadcastMessage.objects.create(
            user=other_user,
            message='Other user message'
        )
        
        url = reverse('delete_broadcast_message', kwargs={'message_id': other_message.id})
        response = self.client.get(url)
        
        # Check message was not deleted
        self.assertTrue(BroadcastMessage.objects.filter(id=other_message.id).exists())
    
    def test_delete_message_unauthenticated(self):
        """Test that unauthenticated users cannot delete messages"""
        self.client.logout()
        url = reverse('delete_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.get(url)
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class UpdateBroadcastMessageViewTests(TestCase):
    """Test suite for update_broadcast_message view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.message = BroadcastMessage.objects.create(
            user=self.user,
            message='Original message'
        )
    
    def test_update_own_message(self):
        """Test updating user's own message"""
        url = reverse('update_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.post(url, {'message': 'Updated message'})
        
        # Refresh message from database
        self.message.refresh_from_db()
        self.assertEqual(self.message.message, 'Updated message')
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_update_nonexistent_message(self):
        """Test updating a nonexistent message"""
        url = reverse('update_broadcast_message', kwargs={'message_id': 99999})
        response = self.client.post(url, {'message': 'Updated message'})
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_update_another_users_message(self):
        """Test that users cannot update other users' messages"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            username='other_user'
        )
        other_message = BroadcastMessage.objects.create(
            user=other_user,
            message='Other user message'
        )
        
        url = reverse('update_broadcast_message', kwargs={'message_id': other_message.id})
        response = self.client.post(url, {'message': 'Hacked message'})
        
        # Check message was not updated
        other_message.refresh_from_db()
        self.assertEqual(other_message.message, 'Other user message')
    
    def test_update_message_unauthenticated(self):
        """Test that unauthenticated users cannot update messages"""
        self.client.logout()
        url = reverse('update_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.post(url, {'message': 'Updated message'})
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class ToggleBroadcastMessageViewTests(TestCase):
    """Test suite for toggle_broadcast_message view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test_user'
        )
        self.client.login(username='test@example.com', password='testpass123')
        self.message = BroadcastMessage.objects.create(
            user=self.user,
            message='Test message',
            active=True
        )
    
    def test_toggle_message_from_active_to_inactive(self):
        """Test toggling message from active to inactive"""
        url = reverse('toggle_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.get(url)
        
        # Refresh message from database
        self.message.refresh_from_db()
        self.assertFalse(self.message.active)
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_toggle_message_from_inactive_to_active(self):
        """Test toggling message from inactive to active"""
        self.message.active = False
        self.message.save()
        
        url = reverse('toggle_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.get(url)
        
        # Refresh message from database
        self.message.refresh_from_db()
        self.assertTrue(self.message.active)
    
    def test_toggle_nonexistent_message(self):
        """Test toggling a nonexistent message"""
        url = reverse('toggle_broadcast_message', kwargs={'message_id': 99999})
        response = self.client.get(url)
        
        # Check redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_toggle_another_users_message(self):
        """Test that users cannot toggle other users' messages"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            username='other_user'
        )
        other_message = BroadcastMessage.objects.create(
            user=other_user,
            message='Other user message',
            active=True
        )
        
        url = reverse('toggle_broadcast_message', kwargs={'message_id': other_message.id})
        response = self.client.get(url)
        
        # Check message was not toggled
        other_message.refresh_from_db()
        self.assertTrue(other_message.active)
    
    def test_toggle_message_unauthenticated(self):
        """Test that unauthenticated users cannot toggle messages"""
        self.client.logout()
        url = reverse('toggle_broadcast_message', kwargs={'message_id': self.message.id})
        response = self.client.get(url)
        
        # Check redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_toggle_deactivates_other_active_messages(self):
        """Test that toggling to active deactivates other active messages"""
        message2 = BroadcastMessage.objects.create(
            user=self.user,
            message='Second message',
            active=False
        )
        
        url = reverse('toggle_broadcast_message', kwargs={'message_id': message2.id})
        response = self.client.get(url)
        
        # Refresh messages
        self.message.refresh_from_db()
        message2.refresh_from_db()
        
        # First message should be inactive
        self.assertFalse(self.message.active)
        # Second message should be active
        self.assertTrue(message2.active)
