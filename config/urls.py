"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from clinic.views import MedicalCardsByUserView, MedicalCardsByDoctorView
from users.views import CreateUserView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls', namespace='authentication')),
    path('api/', include('support_requests.urls', namespace='support_requests')),
    path('api/clinic/', include('clinic.urls', namespace='clinic')),
    # Aliased medical card endpoints requested
    path('api/client/medical_card/by_user/<int:user_id>/', MedicalCardsByUserView.as_view(), name='client-medical-cards-by-user'),
    path('api/client/medical_card/by_doctor/<int:doctor_id>/', MedicalCardsByDoctorView.as_view(), name='client-medical-cards-by-doctor'),
    path('api/users/', include('users.urls', namespace='users')),
    # Direct user creation endpoint
    path('api/create_user/', CreateUserView.as_view(), name='create-user'),
    path('bot/', include('telegram_bot.urls')),
    # OpenAPI schema and documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
