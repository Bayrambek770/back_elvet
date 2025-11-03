from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from users.models import User, RoleChoices
from clinic.models import Pet, MedicalCard, Payment, PaymentStatus, PaymentMethod, Service, PaymentDay


class PaymentSummaryTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        # Create users and profiles via signals
        self.admin = User.objects.create_user(
            phone_number="+10000000001", password="pass", first_name="A", last_name="D", role=RoleChoices.ADMIN
        )
        self.moderator = User.objects.create_user(
            phone_number="+10000000002", password="pass", first_name="M", last_name="O", role=RoleChoices.MODERATOR
        )
        self.doctor = User.objects.create_user(
            phone_number="+10000000003", password="pass", first_name="D", last_name="R", role=RoleChoices.DOCTOR
        )
        self.client_user = User.objects.create_user(
            phone_number="+10000000004", password="pass", first_name="C", last_name="L", role=RoleChoices.CLIENT
        )

        # Domain: Pet, MedicalCard
        self.pet = Pet.objects.create(client=self.client_user.client_profile, name="Buddy", breed="", age=3, gender="male")
        # Create at least one service to avoid null m2m dependencies (not strictly required for payments)
        self.service = Service.objects.create(name="Checkup", price=Decimal("50000"), created_by=self.admin.admin_profile)
        self.card = MedicalCard.objects.create(
            client=self.client_user.client_profile,
            pet=self.pet,
            doctor=self.doctor.doctor_profile,
            nurse=None,
            diagnosis="",
        )

        self.client_api.force_authenticate(user=self.admin)

    def test_payment_summary_group_by_day(self):
        today = timezone.now()
        day1 = today - timedelta(days=2)
        day2 = today - timedelta(days=1)

        # Create payments on different days
        p1 = Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PAID,
            method=PaymentMethod.CASH,
            amount=Decimal("150000.00"),
            processed_by=self.moderator.moderator_profile,
        )
        Payment.objects.filter(pk=p1.pk).update(created_at=day1)

        p2 = Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PAID,
            method=PaymentMethod.CARD,
            amount=Decimal("50000.00"),
            processed_by=self.moderator.moderator_profile,
        )
        Payment.objects.filter(pk=p2.pk).update(created_at=day2)

        p3 = Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PAID,
            method=PaymentMethod.CASH,
            amount=Decimal("25000.00"),
            processed_by=self.moderator.moderator_profile,
        )
        # p3 stays at today

        start = (today - timedelta(days=3)).date().isoformat()
        end = today.date().isoformat()
        resp = self.client_api.get(f"/api/clinic/payment-summary/?start={start}&end={end}&group_by=day")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_amount", data)
        self.assertIn("items", data)
        # Totals
        self.assertEqual(Decimal(str(data["total_amount"])), Decimal("225000.00"))
        self.assertEqual(data.get("total_count"), 3)
        # Should have 3 day buckets
        self.assertEqual(len(data["items"]), 3)

    def test_payment_summary_group_by_month(self):
        today = timezone.now()
        last_month = (today - timedelta(days=31))

        p_last = Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PAID,
            method=PaymentMethod.CASH,
            amount=Decimal("100000.00"),
            processed_by=self.moderator.moderator_profile,
        )
        Payment.objects.filter(pk=p_last.pk).update(created_at=last_month)

        p_now = Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PAID,
            method=PaymentMethod.CARD,
            amount=Decimal("50000.00"),
            processed_by=self.moderator.moderator_profile,
        )

        start = (last_month - timedelta(days=2)).date().isoformat()
        end = today.date().isoformat()
        resp = self.client_api.get(f"/api/clinic/payment-summary/?start={start}&end={end}&group_by=month")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("items", data)
        # Expect 2 months aggregation
        self.assertEqual(len(data["items"]), 2)
        # Total amount equals sum
        self.assertEqual(Decimal(str(data["total_amount"])), Decimal("150000.00"))
        

class PaymentDayTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin = User.objects.create_user(
            phone_number="+20000000001", password="pass", first_name="A", last_name="D", role=RoleChoices.ADMIN
        )
        self.moderator = User.objects.create_user(
            phone_number="+20000000002", password="pass", first_name="M", last_name="O", role=RoleChoices.MODERATOR
        )
        self.doctor = User.objects.create_user(
            phone_number="+20000000003", password="pass", first_name="D", last_name="R", role=RoleChoices.DOCTOR
        )
        self.client_user = User.objects.create_user(
            phone_number="+20000000004", password="pass", first_name="C", last_name="L", role=RoleChoices.CLIENT
        )
        self.pet = Pet.objects.create(client=self.client_user.client_profile, name="Rocky", breed="", age=4, gender="male")
        self.service = Service.objects.create(name="X-Ray", price=Decimal("40000"), created_by=self.admin.admin_profile)
        self.card = MedicalCard.objects.create(
            client=self.client_user.client_profile,
            pet=self.pet,
            doctor=self.doctor.doctor_profile,
            nurse=None,
            diagnosis="",
        )
        self.client_api.force_authenticate(user=self.admin)

    def test_payment_day_increment_on_paid(self):
        amt = Decimal("123000.00")
        pay = Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PENDING,
            method=PaymentMethod.CASH,
            amount=amt,
            processed_by=self.moderator.moderator_profile,
        )
        # Transition to PAID
        pay.status = PaymentStatus.PAID
        pay.save()
        today = timezone.localdate()
        pd = PaymentDay.objects.get(date=today)
        self.assertEqual(pd.price, amt)

    def test_payment_day_view_zero_fill(self):
        # Ensure only today has a payment
        amt = Decimal("50000.00")
        Payment.objects.create(
            medical_card=self.card,
            status=PaymentStatus.PAID,
            method=PaymentMethod.CASH,
            amount=amt,
            processed_by=self.moderator.moderator_profile,
        )
        resp = self.client_api.get("/api/clinic/payment-days/?days=3")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Expect 3 items (older two may be 0)
        self.assertEqual(len(data), 3)
        # Last item should be today and equal amt
        self.assertEqual(Decimal(str(data[-1]["price"])), amt)
