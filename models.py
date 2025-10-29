"""Aggregated models module for the clinic management system.

This module re-exports all ORM models from the dedicated Django apps:
- users: custom User and role profile models (Admin, Moderator, Doctor, Nurse, Client)
- clinic: domain models (Pet, Medicine, Service, MedicalCard, Payment, StationaryRoom)

Keeping models in their apps enables proper migrations and app separation,
while this file provides a single import location if desired.
"""

# Re-export user-related models
from users.models import (  # noqa: F401
    User,
    Admin,
    Moderator,
    Doctor,
    Nurse,
    Client,
)

# Re-export clinic-related models
from clinic.models import (  # noqa: F401
    Pet,
    Medicine,
    Service,
    MedicalCard,
    Payment,
    StationaryRoom,
)

__all__ = [
    # users
    "User",
    "Admin",
    "Moderator",
    "Doctor",
    "Nurse",
    "Client",
    # clinic
    "Pet",
    "Medicine",
    "Service",
    "MedicalCard",
    "Payment",
    "StationaryRoom",
]
