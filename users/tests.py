from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

class UserTests(APITestCase):

    def setup(self):
        """
        Setup stuff: create three users to play with, two regular and one admin.
        """
        self.test_admin_user = User.objects.create_superuser('testadminuser', 'test@example.com', 'testadminpassword')
        self.test_user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        self.test_user2 = User.objects.create_user('testuser2', 'test@example.com', 'testpassword2')

    def test_setup_created_correct_test_users(self):
        """
        Confirm that we have both a regular user and an admin user to test with.
        """
        test_user = User.objects.get(username="testuser")
        test_user2 = User.objects.get(username="testuser2")
        test_admin_user = User.objects.get(username="testadminuser")

        self.assertIsInstance(test_user, User)
        self.assertIsInstance(test_user2, User)
        self.assertIsInstance(test_admin_user, User)

        self.assertTrue(test_user.is_active)
        self.assertFalse(test_user.is_staff)
        self.assertFalse(test_user.is_superuser)

        self.assertTrue(test_user2.is_active)
        self.assertFalse(test_user2.is_staff)
        self.assertFalse(test_user2.is_superuser)
        
        self.assertTrue(test_admin_user.is_active)
        self.assertTrue(test_admin_user.is_staff)
        self.assertTrue(test_admin_user.is_superuser)

    def test_can_create_user_anonymously(self):
        """
        Confirm that anyone can create a username via /api/v1/users/create/
        """
        url = reverse('create-user')
        data = {
            "username": "createduser",
            "first_name": "Created",
            "last_name": "User",
            "email": "created@example.com",
            "password": "regularUser!"
        }
        response = self.client.post(url, data, format='json')
        new_user = User.objects.get(username='createduser')
        ignore_response_fields = ['id', 'password']
        
        response_status = response.status_code

        self.assertEqual(response_status, status.HTTP_201_CREATED)
        self.assertIsInstance(new_user, User)

    def test_api_response_to_user_creation_matches_post_data(self):
        """
        Confirm that the API responds w/ the same fields it was told to create
        """
        url = reverse('create-user')
        data = {
            "username": "createduser",
            "first_name": "Created",
            "last_name": "User",
            "email": "created@example.com",
            "password": "regularUser!"
        }
        response = self.client.post(url, data, format='json')
        ignore_response_fields = ['id', 'password']
        for k, v in response.data.items():
            if k not in ignore_response_fields:
                self.assertEqual(v, data[k])

    def test_cannot_update_user_anonymously(self):
        """
        Confirm that we cannot update a user anonymously
        """
        url = reverse('update-user', args=[2]) # Try to update the test user (pk=2)
        data = {
            "username": "updated_test_user",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "totally_different_password!"
        }
        
        self.client.force_authenticate(user=None) # No authentication
        response = self.client.put(url, data, format='json')
        response_detail = response.data['detail']
        response_status = response.status_code

        self.assertEqual(response_status, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_detail, 'Authentication credentials were not provided.')

    def test_regular_user_cannot_update_other_users_info(self):
        """
        Confirm that one unprivileged (non-staff/su) user cannot update another's info
        """
        url = reverse('update-user', args=[2]) # Try to update the test user (pk=2)
        data = {
            "username": "updated_test_user",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "totally_different_password!"
        }
        
        self.client.login(username='testuser2', password='testpassword2')
        response = self.client.put(url, data, format='json')
        response_detail = response.data['detail']
        response_status = response.status_code

        self.assertEqual(response_status, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_detail, 'You do not have permission to perform this action.')

    def test_user_can_update_own_info(self):
        """
        Confirm that a user can update their own user info
        """
        url = reverse('update-user', args=[2]) # Try to update the test user (pk=2)
        data = {
            "username": "updated_test_user",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "totally_different_password!"
        }
        
        self.client.login(username='testuser', password='testpassword')
        response = self.client.put(url, data, format='json')
        response_status = response.status_code
        user = User.objects.get(username='updated_test_user')
        ignore_response_fields = ['id', 'password']

        self.assertEqual(response_status, status.HTTP_200_OK)
        self.assertIsInstance(user, User)
        for k, v in response.data.items():
            if k not in ignore_response_fields:
                self.assertEqual(v, getattr(user, k))

    def test_admin_user_can_update_regular_users_info(self):
        """
        Confirm that an admin user can update someone else's user info
        """
        url = reverse('update-user', args=[2]) # Try to update the test user (pk=2)
        data = {
            "username": "updated_test_user",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "totally_different_password!"
        }
        
        self.client.login(username='testadminuser', password='testadminpassword')
        response = self.client.put(url, data, format='json')
        response_status = response.status_code
        user = User.objects.get(username='updated_test_user')
        ignore_response_fields = ['id', 'password']

        self.assertEqual(response_status, status.HTTP_200_OK)
        self.assertIsInstance(user, User)
        for k, v in response.data.items():
            if k not in ignore_response_fields:
                self.assertEqual(v, getattr(user, k))

    def test_password_not_in_create_user_api_response(self):
        """
        Confirm that the API does not return the password in the response
        to creating a user.
        """
        url = reverse('create-user')
        data = {
            "username": "createduser",
            "first_name": "Created",
            "last_name": "User",
            "email": "created@example.com",
            "password": "regularUser!"
        }
        response = self.client.post(url, data, format='json')
        response_status = response.status_code

        self.assertEqual(response_status, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data.keys())

    def test_password_not_in_update_user_api_response(self):
        """
        Confirm that the API does not return the password in the response
        to updating a user.
        """
        url = reverse('update-user', args=[2]) # Try to update the test user (pk=2)
        data = {
            "username": "updated_test_user",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "totally_different_password!"
        }
        
        self.client.login(username='testadminuser', password='testadminpassword')
        response = self.client.put(url, data, format='json')
        response_status = response.status_code

        self.assertEqual(response_status, status.HTTP_200_OK)
        self.assertNotIn('password', response.data.keys())

    def test_password_not_in_delete_user_api_response(self):
        """
        Confirm that the API does not return the password in the response
        to updating a user.
        """
        url = reverse('delete-user', args=[2]) # Try to update the test user (pk=2)
        data = {
            "username": "updated_test_user",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "totally_different_password!"
        }
        
        self.client.login(username='testadminuser', password='testadminpassword')
        response = self.client.delete(url, data, format='json')
        response_status = response.status_code

        self.assertEqual(response_status, status.HTTP_204_NO_CONTENT)
        self.assertIs(response.data, None)