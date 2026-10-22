from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CaseViewSet, RegisterView, TokenView, health

router = DefaultRouter()
router.register("cases", CaseViewSet, basename="case")

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", TokenView.as_view(), name="token"),
    path("", include(router.urls)),
]
