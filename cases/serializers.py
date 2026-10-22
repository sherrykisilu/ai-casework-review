import hashlib

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import AnalysisRun, Case


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = ["username", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class AnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = [
            "id", "status", "provider", "model", "prompt_version", "input_tokens",
            "output_tokens", "latency_ms", "retry_count", "correlation_id",
            "error_code", "created_at", "completed_at",
        ]


class CaseSerializer(serializers.ModelSerializer):
    runs = AnalysisRunSerializer(many=True, read_only=True)
    deduplicated = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Case
        fields = [
            "id", "title", "source_text", "status", "progress", "result", "error_code",
            "error_message", "trace_id", "created_at", "updated_at", "runs", "deduplicated",
        ]
        read_only_fields = [
            "status", "progress", "result", "error_code", "error_message", "trace_id",
            "created_at", "updated_at", "runs",
        ]

    def validate_source_text(self, value):
        value = value.strip()
        if len(value) < 30:
            raise serializers.ValidationError("Provide at least 30 characters of case context.")
        if len(value) > settings.AI_MAX_INPUT_CHARS:
            raise serializers.ValidationError(f"Case text must not exceed {settings.AI_MAX_INPUT_CHARS} characters.")
        return value

    def create(self, validated_data):
        owner = self.context["request"].user
        today_count = Case.objects.filter(owner=owner, created_at__date=timezone.localdate()).count()
        if today_count >= settings.AI_DAILY_CASE_LIMIT:
            raise serializers.ValidationError({"detail": "Daily case submission limit reached."})
        content_hash = hashlib.sha256(validated_data["source_text"].encode()).hexdigest()
        case, created = Case.objects.get_or_create(
            owner=owner,
            content_hash=content_hash,
            defaults=validated_data,
        )
        case._deduplicated = not created
        return case

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["deduplicated"] = getattr(instance, "_deduplicated", False)
        return data
