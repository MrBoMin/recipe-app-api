"""
Tests for the user API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)

class PulicUserApiTests(TestCase):
    """Test the public features of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful"""
        payload = {
            'email' : 'test@example.com',
            'password' : 'testpass123',
            'name' : 'Test Name'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        # Check that status code is 201 (created)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])

        # Check that the password is hashed
        self.assertTrue(user.check_password(payload['password']))

        # Ensure that password is not returned in the response
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists"""
        payload = {
            'email' : 'test@example.com',
            'password' : 'testpass123',
            'name' : 'Test Name'
        }

        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting 400 because the email already exists
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password is less than 5 chars"""
        payload = {
            'email' : 'test@example.com',
            'password' : 'pw',
            'name' : 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting 400 because the password is too short
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Ensure user is not created with the invalid password
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_for_user(self):
        """Test generates token for valid credentials"""
        user_details = {
            'name' : 'Test Name',
            'email' : 'test@example.com',
            'password' : 'test-user-password123' }
        create_user(**user_details)

        payload = {
            'email' : user_details.get('email'),
            'password' : user_details.get('password')
        }

        res = self.client.post(TOKEN_URL, payload)

        # Check if token is returned
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials are invalid"""
        create_user(email='test@example.com', password='goodpasss')
        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        # Check that token is not returned
        self.assertNotIn('token', res.data)

        # Expecting 400 because the credentials are incorrect
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        # Check that token is not returned
        self.assertNotIn('token', res.data)

        # Expecting 400 because password is required
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_retrieve_user_authorized(self):
        '''Test authentication is required for user!'''
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    '''Test API requests that require the authentication!'''
    def setUp(self):
        self.user = create_user(
            email = 'test@example.com',
            password = 'testpass123',
            name = 'Test Name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retriving the profile for logged in user."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name' : self.user.name,
            'email' : self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test Post is not allowed for the me endpoint"""
        res  = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    def test_update_user_profile(self):
        payload = {'name' : 'updated name', 'password' : 'newpassword123'}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)