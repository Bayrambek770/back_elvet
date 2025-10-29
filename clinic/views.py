"""ViewSets for Clinic domain.

Includes Pets, Medicines, Services, Medical Cards, Payments, Stationary Rooms,
and Nurse Management (Schedules, Tasks, Salaries).
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import (
    NurseDailySalary,
    Schedule,
    Task,
    StationaryRoom,
    Pet,
    Medicine,
    Service,
    MedicalCard,
    Payment,
)
from .permissions import IsDoctorForScheduleWrite, IsDoctorOrAssignedNurseForTask
from .serializers import (
    NurseDailySalarySerializer,
    ScheduleSerializer,
    TaskSerializer,
    StationaryRoomSerializer,
    PetSerializer,
    MedicineSerializer,
    ServiceSerializer,
    MedicalCardSerializer,
    PaymentSerializer,
)


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
