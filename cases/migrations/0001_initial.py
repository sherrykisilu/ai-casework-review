import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Case",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=160)),
                ("source_text", models.TextField()),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="queued", max_length=20)),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                ("result", models.JSONField(blank=True, null=True)),
                ("error_code", models.CharField(blank=True, max_length=80)),
                ("error_message", models.TextField(blank=True)),
                ("trace_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cases", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AnalysisRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("started", "Started"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("timed_out", "Timed out")], max_length=20)),
                ("provider", models.CharField(max_length=80)),
                ("model", models.CharField(max_length=120)),
                ("prompt_version", models.CharField(max_length=40)),
                ("input_tokens", models.PositiveIntegerField(default=0)),
                ("output_tokens", models.PositiveIntegerField(default=0)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("retry_count", models.PositiveSmallIntegerField(default=0)),
                ("correlation_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ("error_code", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="cases.case")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="case",
            constraint=models.UniqueConstraint(fields=("owner", "content_hash"), name="unique_owner_case_content"),
        ),
    ]
