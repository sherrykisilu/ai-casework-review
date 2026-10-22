from django.db import transaction
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Case
from .serializers import CaseSerializer, RegisterSerializer
from .tasks import analyze_case


def health(request):
    return JsonResponse({"status": "ok"})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(username=response.data["username"])
        response.data["token"] = Token.objects.create(user=user).key
        return response

    def get_queryset(self):
        from django.contrib.auth.models import User

        return User.objects.all()


class TokenView(ObtainAuthToken):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return Response({"token": response.data["token"]})


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.none()
    serializer_class = CaseSerializer
    http_method_names = ["get", "post", "head", "options"]
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return Case.objects.filter(owner=self.request.user).prefetch_related("runs")

    @extend_schema(responses=CaseSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = serializer.save()
        if not getattr(case, "_deduplicated", False) and not transaction.get_connection().in_atomic_block:
            analyze_case.delay(str(case.id))
        elif not getattr(case, "_deduplicated", False):
            transaction.on_commit(lambda: analyze_case.delay(str(case.id)))
        return Response(self.get_serializer(case).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        case = self.get_object()
        if case.status not in {Case.Status.FAILED, Case.Status.COMPLETED}:
            return Response({"detail": "Only failed or completed cases can be retried."}, status=409)
        case.status = Case.Status.QUEUED
        case.progress = 0
        case.result = None
        case.save(update_fields=["status", "progress", "result", "updated_at"])
        analyze_case.delay(str(case.id))
        return Response(self.get_serializer(case).data, status=status.HTTP_202_ACCEPTED)
