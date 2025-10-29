from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from .models import Request

User = get_user_model()


class RequestValidationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number="+998901234567", password="pass1234", first_name="U", last_name="S")
        self.client.force_authenticate(self.user)

    def test_phone_validation_and_uniqueness_for_open_requests(self):
        url = reverse("support_requests:request-list")
        payload = {"full_name": "John Doe", "phone_number": "+998901234567", "text": "Hello"}
        res1 = self.client.post(url, payload, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        res2 = self.client.post(url, payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", res2.data)


class RequestPermissionsTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.moderator_user = User.objects.create_user(phone_number="+998901234568", password="pass1234", first_name="M", last_name="O", role="moderator", is_staff=False)
        self.normal_user = User.objects.create_user(phone_number="+998901234569", password="pass1234", first_name="N", last_name="U")
        self.request_obj = Request.objects.create(full_name="Jane Doe", phone_number="+998901111111")

    def test_list_requires_moderator(self):
        url = reverse("support_requests:request-list")
        self.client_api.force_authenticate(self.normal_user)
        res = self.client_api.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.client_api.force_authenticate(self.moderator_user)
        res = self.client_api.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_moderator_only(self):
        url = reverse("support_requests:request-detail", args=[self.request_obj.id])
        # Normal user should not retrieve
        self.client_api.force_authenticate(self.normal_user)
        res = self.client_api.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # Moderator allowed
        self.client_api.force_authenticate(self.moderator_user)
        res = self.client_api.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_answer_action_moderator_only(self):
        url = reverse("support_requests:request-answer-request", args=[self.request_obj.id])
        self.client_api.force_authenticate(self.normal_user)
        res = self.client_api.patch(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.client_api.force_authenticate(self.moderator_user)
        res = self.client_api.patch(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.request_obj.refresh_from_db()
        self.assertTrue(self.request_obj.is_answered)
        self.assertEqual(self.request_obj.answered_by_id, self.moderator_user.id)
