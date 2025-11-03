from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    NurseDailySalaryViewSet,
    DoctorTaskViewSet,
    DoctorIncomeViewSet,
    NurseIncomeViewSet,
    ScheduleViewSet,
    TaskViewSet,
    StationaryRoomViewSet,
    StationaryRoomManageViewSet,
    PetViewSet,
    MedicineViewSet,
    ServiceViewSet,
    MedicalCardViewSet,
    PaymentViewSet,
    MedicalUsageView,
    PaymentSummaryView,
    PaymentDayView,
)

app_name = "clinic"

router = DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedule")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"doctor-tasks", DoctorTaskViewSet, basename="doctor-task")
router.register(r"doctor-incomes", DoctorIncomeViewSet, basename="doctor-income")
router.register(r"nurse-incomes", NurseIncomeViewSet, basename="nurse-income")
router.register(r"nurse-daily-salaries", NurseDailySalaryViewSet, basename="nurse-daily-salary")
router.register(r"rooms", StationaryRoomViewSet, basename="stationary-room")
router.register(r"rooms-manage", StationaryRoomManageViewSet, basename="stationary-room-manage")
router.register(r"pets", PetViewSet, basename="pet")
router.register(r"medicines", MedicineViewSet, basename="medicine")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"medical-cards", MedicalCardViewSet, basename="medical-card")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
    path("medical-usages/", MedicalUsageView.as_view(), name="medical-usage"),
    path("payment-summary/", PaymentSummaryView.as_view(), name="payment-summary"),
    path("payment-days/", PaymentDayView.as_view(), name="payment-days"),
]
