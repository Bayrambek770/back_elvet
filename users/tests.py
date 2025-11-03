from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model

User = get_user_model()


class CreateUserViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.url = reverse("create-user")

    def test_anonymous_can_create_client(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+998900000001",
            "password": "secret12",
            "role": "client",
        }
        res = self.client_api.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Ensure user exists and client profile created by signal
        user = User.objects.get(phone_number=payload["phone_number"]) 
        self.assertEqual(user.role, "client")
        self.assertTrue(hasattr(user, "client_profile"))

    def test_anonymous_cannot_create_doctor(self):
        payload = {
            "first_name": "Doc",
            "last_name": "Tor",
            "phone_number": "+998900000002",
            "password": "secret12",
            "role": "doctor",
        }
        res = self.client_api.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_create_client(self):
        moderator = User.objects.create_user(
            phone_number="+998900000010",
            password="pass1234",
            first_name="Mod",
            last_name="Erator",
            role="moderator",
        )
        self.client_api.force_authenticate(moderator)
        payload = {
            "first_name": "Cli",
            "last_name": "Ent",
            "phone_number": "+998900000011",
            "password": "secret12",
            "role": "client",
        }
        res = self.client_api.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(phone_number=payload["phone_number"]) 
        self.assertEqual(user.role, "client")
        self.assertTrue(hasattr(user, "client_profile"))

    def test_moderator_cannot_create_doctor(self):
        moderator = User.objects.create_user(
            phone_number="+998900000020",
            password="pass1234",
            first_name="Mod",
            last_name="Erator",
            role="moderator",
        )
        self.client_api.force_authenticate(moderator)
        payload = {
            "first_name": "Doc",
            "last_name": "Tor",
            "phone_number": "+998900000021",
            "password": "secret12",
            "role": "doctor",
        }
        res = self.client_api.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_doctor(self):
        admin = User.objects.create_superuser(
            phone_number="+998900000030",
            password="pass1234",
            first_name="Ad",
            last_name="Min",
        )
        self.client_api.force_authenticate(admin)
        payload = {
            "first_name": "Doc",
            "last_name": "Tor",
            "phone_number": "+998900000031",
            "password": "secret12",
            "role": "doctor",
        }
        res = self.client_api.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(phone_number=payload["phone_number"]) 
        self.assertEqual(user.role, "doctor")
        self.assertTrue(hasattr(user, "doctor_profile"))

    def test_client_cannot_create_any_user(self):
        client_user = User.objects.create_user(
            phone_number="+998900000040",
            password="pass1234",
            first_name="Cli",
            last_name="Ent",
            role="client",
        )
        self.client_api.force_authenticate(client_user)
        payload = {
            "first_name": "Another",
            "last_name": "Client",
            "phone_number": "+998900000041",
            "password": "secret12",
            "role": "client",
        }
        res = self.client_api.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
