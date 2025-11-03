"""ViewSets for Clinic domain.

Includes Pets, Medicines, Services, Medical Cards, Payments, Stationary Rooms,
and Nurse Management (Schedules, Tasks, Salaries).
"""

from rest_framework import permissions, status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils.dateparse import parse_date
from datetime import timedelta
from django.utils import timezone

from .models import (
    NurseDailySalary,
    DoctorTask,
    DoctorIncome,
    Schedule,
    Task,
    StationaryRoom,
    Pet,
    Medicine,
    Service,
    MedicalCard,
    Payment,
    Visit,
)
from .permissions import IsDoctorForScheduleWrite, IsDoctorOrAssignedNurseForTask
from .serializers import (
    NurseDailySalarySerializer,
    DoctorTaskSerializer,
    DoctorIncomeSerializer,
    ScheduleSerializer,
    TaskSerializer,
    StationaryRoomSerializer,
    PetSerializer,
    MedicineSerializer,
    ServiceSerializer,
    MedicalCardSerializer,
    PaymentSerializer,
    MedicalUsageSerializer,
    PaymentSummarySerializer,
    PaymentDaySerializer,
    VisitSerializer,
)
from .permissions import IsDoctorOwnerOrAdmin, IsNurseOwnerOrAdmin, IsModeratorWriteVisits


# =========================
# Core CRUD: Pets
# =========================


@extend_schema_view(
    list=extend_schema(tags=["clinic:pets"], summary="List pets"),
    retrieve=extend_schema(tags=["clinic:pets"], summary="Retrieve pet"),
    create=extend_schema(tags=["clinic:pets"], summary="Create pet"),
    update=extend_schema(tags=["clinic:pets"], summary="Update pet"),
    partial_update=extend_schema(tags=["clinic:pets"], summary="Partially update pet"),
    destroy=extend_schema(tags=["clinic:pets"], summary="Delete pet"),
)
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.select_related("client__user").all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]


# =========================
# Core CRUD: Medicines
# =========================


@extend_schema_view(
    list=extend_schema(tags=["clinic:medicines"], summary="List medicines"),
    retrieve=extend_schema(tags=["clinic:medicines"], summary="Retrieve medicine"),
    create=extend_schema(tags=["clinic:medicines"], summary="Create medicine"),
    update=extend_schema(tags=["clinic:medicines"], summary="Update medicine"),
    partial_update=extend_schema(tags=["clinic:medicines"], summary="Partially update medicine"),
    destroy=extend_schema(tags=["clinic:medicines"], summary="Delete medicine"),
)
class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.select_related("created_by__user").all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]


# =========================
# Core CRUD: Services
# =========================


@extend_schema_view(
    list=extend_schema(tags=["clinic:services"], summary="List services"),
    retrieve=extend_schema(tags=["clinic:services"], summary="Retrieve service"),
    create=extend_schema(tags=["clinic:services"], summary="Create service"),
    update=extend_schema(tags=["clinic:services"], summary="Update service"),
    partial_update=extend_schema(tags=["clinic:services"], summary="Partially update service"),
    destroy=extend_schema(tags=["clinic:services"], summary="Delete service"),
)
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("created_by__user").all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]


# =========================
# Core CRUD: Medical Cards
# =========================


@extend_schema_view(
    list=extend_schema(tags=["clinic:medical-cards"], summary="List medical cards"),
    retrieve=extend_schema(tags=["clinic:medical-cards"], summary="Retrieve medical card"),
    create=extend_schema(tags=["clinic:medical-cards"], summary="Create medical card"),
    update=extend_schema(tags=["clinic:medical-cards"], summary="Update medical card"),
    partial_update=extend_schema(tags=["clinic:medical-cards"], summary="Partially update medical card"),
    destroy=extend_schema(tags=["clinic:medical-cards"], summary="Delete medical card"),
)
class MedicalCardViewSet(viewsets.ModelViewSet):
    queryset = (
        MedicalCard.objects.select_related(
            "client__user", "pet", "doctor__user", "nurse__user", "stationary_room"
        ).prefetch_related("services", "medicines")
    )
    serializer_class = MedicalCardSerializer
    permission_classes = [permissions.IsAuthenticated]


# ================
# Aliased endpoints (explicit paths requested):
#   /api/client/medical_card/by_user/<id>/
#   /api/client/medical_card/by_doctor/<id>/
# Reuse the same serializer and queryset/pagination via ListAPIView
# ================


@extend_schema(
    tags=["clinic:medical-cards"],
    summary="List medical cards by client user ID (alias)",
    responses={200: OpenApiResponse(response=MedicalCardSerializer)},
)
class MedicalCardsByUserView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicalCardSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return (
            MedicalCard.objects.select_related(
                "client__user", "pet", "doctor__user", "nurse__user", "stationary_room"
            ).prefetch_related("services", "medicines").filter(client__user_id=user_id)
        )


@extend_schema(
    tags=["clinic:medical-cards"],
    summary="List medical cards by doctor ID (alias)",
    responses={200: OpenApiResponse(response=MedicalCardSerializer)},
)
class MedicalCardsByDoctorView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicalCardSerializer

    def get_queryset(self):
        doctor_id = self.kwargs.get("doctor_id")
        return (
            MedicalCard.objects.select_related(
                "client__user", "pet", "doctor__user", "nurse__user", "stationary_room"
            ).prefetch_related("services", "medicines").filter(doctor_id=doctor_id)
        )


# =========================
# Payments
# =========================


@extend_schema_view(
    list=extend_schema(tags=["clinic:payments"], summary="List payments"),
    retrieve=extend_schema(tags=["clinic:payments"], summary="Retrieve payment"),
    create=extend_schema(tags=["clinic:payments"], summary="Create payment"),
    update=extend_schema(tags=["clinic:payments"], summary="Update payment"),
    partial_update=extend_schema(tags=["clinic:payments"], summary="Partially update payment"),
    destroy=extend_schema(tags=["clinic:payments"], summary="Delete payment"),
)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related(
        "medical_card__client__user", "medical_card__pet", "processed_by__user"
    ).all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(tags=["clinic:schedules"], summary="List schedules"),
    retrieve=extend_schema(tags=["clinic:schedules"], summary="Retrieve schedule"),
    create=extend_schema(tags=["clinic:schedules"], summary="Create schedule"),
    update=extend_schema(tags=["clinic:schedules"], summary="Update schedule"),
    partial_update=extend_schema(tags=["clinic:schedules"], summary="Partially update schedule"),
    destroy=extend_schema(tags=["clinic:schedules"], summary="Delete schedule"),
)
class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.select_related("medical_card", "created_by__user", "assigned_nurse__user").all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsDoctorForScheduleWrite]

    def perform_create(self, serializer):
        # If a doctor is authenticated, ensure created_by matches their profile
        user = self.request.user
        doctor_profile = getattr(user, "doctor_profile", None)
        if doctor_profile:
            serializer.save(created_by=doctor_profile)
        else:
            serializer.save()


@extend_schema_view(
    list=extend_schema(tags=["clinic:tasks"], summary="List tasks"),
    retrieve=extend_schema(tags=["clinic:tasks"], summary="Retrieve task"),
    create=extend_schema(tags=["clinic:tasks"], summary="Create task"),
    update=extend_schema(tags=["clinic:tasks"], summary="Update task"),
    partial_update=extend_schema(tags=["clinic:tasks"], summary="Partially update task"),
    destroy=extend_schema(tags=["clinic:tasks"], summary="Delete task"),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related("schedule", "nurse__user").all()
    serializer_class = TaskSerializer
    permission_classes = [IsDoctorOrAssignedNurseForTask]

    def update(self, request, *args, **kwargs):
        # Enforce that only the assigned nurse can mark is_done=True
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        if 'is_done' in data:
            if not getattr(instance, 'nurse', None) or getattr(instance.nurse, 'user_id', None) != request.user.id:
                # Only the assigned nurse can mark done
                if str(data.get('is_done')).lower() in {"true", "1", "yes"}:
                    return Response({"detail": "Only the assigned nurse can complete the task."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, partial=partial, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filtering by day
        day = self.request.query_params.get("day")
        if day:
            try:
                qs = qs.filter(day=day)
            except Exception:
                pass
        return qs


@extend_schema_view(
    list=extend_schema(tags=["clinic:nurse-daily-salaries"], summary="List nurse daily salaries"),
    retrieve=extend_schema(tags=["clinic:nurse-daily-salaries"], summary="Retrieve nurse daily salary"),
)
class NurseDailySalaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NurseDailySalary.objects.select_related("nurse__user").all()
    serializer_class = NurseDailySalarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Nurses can see their own records; doctors see all; others none by default
        if getattr(user, "role", None) == "nurse":
            nurse_profile = getattr(user, "nurse_profile", None)
            if nurse_profile:
                return qs.filter(nurse=nurse_profile)
            return qs.none()
        if getattr(user, "role", None) == "doctor":
            return qs
        if user.is_staff:
            return qs
        return qs.none()


@extend_schema_view(
    list=extend_schema(tags=["clinic:doctor-tasks"], summary="List doctor tasks"),
    retrieve=extend_schema(tags=["clinic:doctor-tasks"], summary="Retrieve doctor task"),
    create=extend_schema(tags=["clinic:doctor-tasks"], summary="Create doctor task"),
    update=extend_schema(tags=["clinic:doctor-tasks"], summary="Update doctor task"),
    partial_update=extend_schema(tags=["clinic:doctor-tasks"], summary="Partially update doctor task"),
    destroy=extend_schema(tags=["clinic:doctor-tasks"], summary="Delete doctor task"),
)
class DoctorTaskViewSet(viewsets.ModelViewSet):
    queryset = DoctorTask.objects.select_related("doctor__user", "medical_card", "service").all()
    serializer_class = DoctorTaskSerializer
    permission_classes = [IsDoctorOwnerOrAdmin]

    def perform_create(self, serializer):
        # Ensure the doctor is the requester for writes
        user = self.request.user
        doctor_profile = getattr(user, "doctor_profile", None)
        if doctor_profile:
            serializer.save(doctor=doctor_profile)
        else:
            serializer.save()


@extend_schema_view(
    list=extend_schema(tags=["clinic:doctor-incomes"], summary="List doctor incomes"),
    retrieve=extend_schema(tags=["clinic:doctor-incomes"], summary="Retrieve doctor income"),
)
class DoctorIncomeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DoctorIncome.objects.select_related("doctor__user").all()
    serializer_class = DoctorIncomeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "doctor":
            doc = getattr(user, "doctor_profile", None)
            if doc:
                return qs.filter(doctor=doc)
            return qs.none()
        if getattr(user, "role", None) in {"admin", "moderator"} or getattr(user, "is_staff", False):
            return qs
        return qs.none()


@extend_schema_view(
    list=extend_schema(tags=["clinic:nurse-incomes"], summary="List nurse incomes"),
    retrieve=extend_schema(tags=["clinic:nurse-incomes"], summary="Retrieve nurse income"),
)
class NurseIncomeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NurseDailySalary.objects.none()  # placeholder for type; overridden in get_queryset
    serializer_class = None  # set dynamically
    permission_classes = [IsNurseOwnerOrAdmin]

    def get_queryset(self):
        # Lazy import to avoid circulars
        from .models import NurseIncome
        return NurseIncome.objects.select_related("nurse__user").all()

    def get_serializer_class(self):
        from .serializers import NurseIncomeSerializer
        return NurseIncomeSerializer


@extend_schema_view(
    list=extend_schema(tags=["clinic:rooms"], summary="List stationary rooms"),
    retrieve=extend_schema(tags=["clinic:rooms"], summary="Retrieve stationary room"),
)
class StationaryRoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StationaryRoom.objects.select_related("pet").all()
    serializer_class = StationaryRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Doctors should only see available rooms
        if getattr(user, "role", None) == "doctor":
            return qs.filter(is_occupied=False)
        # Staff/admin see all; others see none
        if getattr(user, "is_staff", False):
            return qs
        return qs


# Optional: Allow admins/staff to manage rooms (CRU). Keep deletion out to preserve history.
@extend_schema_view(
    list=extend_schema(tags=["clinic:rooms:manage"], summary="List rooms (manage)"),
    retrieve=extend_schema(tags=["clinic:rooms:manage"], summary="Retrieve room (manage)"),
    create=extend_schema(tags=["clinic:rooms:manage"], summary="Create room"),
    update=extend_schema(tags=["clinic:rooms:manage"], summary="Update room"),
    partial_update=extend_schema(tags=["clinic:rooms:manage"], summary="Partially update room"),
)
class StationaryRoomManageViewSet(viewsets.ModelViewSet):
    queryset = StationaryRoom.objects.select_related("pet").all()
    serializer_class = StationaryRoomSerializer
    permission_classes = [permissions.IsAuthenticated]


# =========================
# Visits
# =========================


@extend_schema_view(
    list=extend_schema(tags=["clinic:visits"], summary="List visits"),
    retrieve=extend_schema(tags=["clinic:visits"], summary="Retrieve visit"),
    create=extend_schema(tags=["clinic:visits"], summary="Create visit"),
    update=extend_schema(tags=["clinic:visits"], summary="Update visit"),
    partial_update=extend_schema(tags=["clinic:visits"], summary="Partially update visit"),
    destroy=extend_schema(tags=["clinic:visits"], summary="Delete visit"),
)
class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.select_related("client__user", "doctor__user").all()
    serializer_class = VisitSerializer
    permission_classes = [IsModeratorWriteVisits]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, "role", None)
        if role == "doctor":
            doc = getattr(user, "doctor_profile", None)
            return qs.filter(doctor=doc) if doc else qs.none()
        if role in {"admin", "moderator"} or getattr(user, "is_staff", False):
            return qs
        return qs.none()

    @action(detail=False, methods=["get"], url_path="my-today", permission_classes=[permissions.IsAuthenticated])
    def my_today(self, request, *args, **kwargs):
        """For doctors: return today's visit count for the authenticated doctor."""
        user = request.user
        if getattr(user, "role", None) != "doctor":
            return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
        doc = getattr(user, "doctor_profile", None)
        if not doc:
            return Response({"count": 0})
        today = timezone.localdate()
        count = Visit.objects.filter(doctor=doc, date=today).count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="today", permission_classes=[permissions.IsAuthenticated])
    def today(self, request, *args, **kwargs):
        """Admin/moderator: return today's total visits and per-doctor breakdown."""
        user = request.user
        if not (getattr(user, "role", None) in {"admin", "moderator"} or getattr(user, "is_staff", False)):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        today = timezone.localdate()
        base = Visit.objects.filter(date=today)
        total = base.count()
        per_doc = (
            base.values("doctor_id", "doctor__user__first_name", "doctor__user__last_name")
            .annotate(count=Count("id"))
            .order_by("doctor_id")
        )
        data = {
            "date": today.isoformat(),
            "total": total,
            "by_doctor": [
                {
                    "doctor_id": row["doctor_id"],
                    "doctor_name": f"{row['doctor__user__first_name']} {row['doctor__user__last_name']}".strip(),
                    "count": row["count"],
                }
                for row in per_doc
            ],
        }
        return Response(data)


@extend_schema(
    tags=["clinic:analytics"],
    summary="Aggregated medicine usage per doctor",
    description=(
        "Return a list where each item shows which doctor used what medicine and how many times.\n"
        "Optional filters: ?doctor_id=<id>&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"
    ),
    responses={200: OpenApiResponse(response=MedicalUsageSerializer)},
)
class MedicalUsageView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicalUsageSerializer

    def list(self, request, *args, **kwargs):
        through = MedicalCard.medicines.through
        qs = through.objects.all()

        doctor_id = request.query_params.get("doctor_id")
        if doctor_id:
            qs = qs.filter(medicalcard__doctor_id=doctor_id)
        start_date = request.query_params.get("start_date")
        if start_date:
            qs = qs.filter(medicalcard__created_at__date__gte=start_date)
        end_date = request.query_params.get("end_date")
        if end_date:
            qs = qs.filter(medicalcard__created_at__date__lte=end_date)

        values_qs = (
            qs.values(
                "medicalcard__doctor_id",
                "medicalcard__doctor__user__first_name",
                "medicalcard__doctor__user__last_name",
                "medicine_id",
                "medicine__name",
            )
            .annotate(usage_count=Count("id"))
            .order_by("-usage_count", "medicalcard__doctor_id", "medicine_id")
        )

        data = [
            {
                "doctor_id": row["medicalcard__doctor_id"],
                "doctor_name": f"{row['medicalcard__doctor__user__first_name']} {row['medicalcard__doctor__user__last_name']}".strip(),
                "medicine_id": row["medicine_id"],
                "medicine_name": row["medicine__name"],
                "usage_count": row["usage_count"],
            }
            for row in values_qs
        ]

        page = self.paginate_queryset(data)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["clinic:analytics"],
    summary="Revenue summary (payments)",
    description=(
        "Aggregate paid payments by day, week, or month within a date range.\n"
        "Query params: start=YYYY-MM-DD, end=YYYY-MM-DD, group_by=day|week|month (default: day)."
    ),
    responses={200: OpenApiResponse(response=PaymentSummarySerializer)},
)
class PaymentSummaryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSummarySerializer

    def get(self, request, *args, **kwargs):
        group_by = request.query_params.get("group_by", "day").lower()
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        # Default range: last 30 days
        today = timezone.localdate()
        start_date = parse_date(start_str) if start_str else (today - timedelta(days=30))
        end_date = parse_date(end_str) if end_str else today
        if start_date and end_date and end_date < start_date:
            return Response({"detail": "end must be on or after start"}, status=status.HTTP_400_BAD_REQUEST)

        qs = Payment.objects.filter(status="paid")
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        # Overall totals
        agg = qs.aggregate(total_amount=Sum("amount"), total_count=Count("id"))
        total_amount = agg.get("total_amount") or 0
        total_count = agg.get("total_count") or 0

        # Grouping
        if group_by == "day":
            trunc = TruncDate("created_at")
            values_name = "period"
        elif group_by == "week":
            trunc = TruncWeek("created_at")
            values_name = "period"
        elif group_by == "month":
            trunc = TruncMonth("created_at")
            values_name = "period"
        else:
            return Response({"detail": "group_by must be one of: day, week, month"}, status=status.HTTP_400_BAD_REQUEST)

        grouped = (
            qs.annotate(period=trunc)
            .values(values_name)
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("period")
        )

        # Serialize items with string periods for consistency
        items = []
        for row in grouped:
            period = row.get("period")
            if period is None:
                p_str = "unknown"
            else:
                if group_by == "month":
                    p_str = period.strftime("%Y-%m")
                else:
                    p_str = period.date().isoformat() if hasattr(period, "date") else str(period)
            items.append({
                "period": p_str,
                "total": row.get("total") or 0,
                "count": row.get("count") or 0,
            })

        data = {
            "total_amount": total_amount,
            "total_count": total_count,
            "items": items,
        }
        serializer = self.get_serializer(data)
        serializer.is_valid(raise_exception=False)
        return Response(serializer.data)


@extend_schema(
    tags=["clinic:analytics"],
    summary="Payment days (last N days)",
    description=(
        "Return last N days of income, filling missing days with 0.\n"
        "Query params: days=1|7|30 (default: 7)."
    ),
    responses={200: OpenApiResponse(response=PaymentDaySerializer)},
)
class PaymentDayView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentDaySerializer

    def get_queryset(self):
        from .models import PaymentDay
        days = self.request.query_params.get("days")
        try:
            days = int(days) if days is not None else 7
        except Exception:
            days = 7
        days = max(1, min(days, 365))

        today = timezone.localdate()
        start = today - timedelta(days=days - 1)

        # Ensure records exist for each day in range (idempotent)
        cur = start
        while cur <= today:
            PaymentDay.objects.get_or_create(date=cur, defaults={"price": 0})
            cur += timedelta(days=1)

        return PaymentDay.objects.filter(date__gte=start, date__lte=today).order_by("date")
