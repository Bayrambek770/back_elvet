"""Aggregated serializers module for the clinic management system.

This module re-exports all DRF ModelSerializers from the dedicated apps:
- users.serializers
- clinic.serializers

It provides a single import surface for API layers without breaking app
structure and migrations.
"""

# Users app serializers
from users.serializers import (  # noqa: F401
    UserSerializer,
    AdminSerializer,
    ModeratorSerializer,
    DoctorSerializer,
    NurseSerializer,
    ClientSerializer,
)

# Clinic app serializers
from clinic.serializers import (  # noqa: F401
    PetSerializer,
    MedicineSerializer,
    ServiceSerializer,
    MedicalCardSerializer,
    PaymentSerializer,
    StationaryRoomSerializer,
)

__all__ = [
    # users
    "UserSerializer",
    "AdminSerializer",
    "ModeratorSerializer",
    "DoctorSerializer",
    "NurseSerializer",
    "ClientSerializer",
    # clinic
    "PetSerializer",
    "MedicineSerializer",
    "ServiceSerializer",
    "MedicalCardSerializer",
    "PaymentSerializer",
    "StationaryRoomSerializer",
]
