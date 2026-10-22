import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from cases.models import AnalysisRun, Case
from cases.tasks import analyze_case


@pytest.fixture
def client(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    user = User.objects.create_user(username="reviewer", password="strong-password")
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db(transaction=True)
def test_submit_analyze_and_deduplicate_case(client):
    payload = {
        "title": "Escalated support complaint",
        "source_text": "The customer says the privacy breach is urgent and their prior escalation was ignored.",
    }
    first = client.post("/api/v1/cases/", payload, format="json")
    assert first.status_code == 201
    case = Case.objects.get(id=first.data["id"])
    assert case.status == Case.Status.COMPLETED
    assert case.result["findings"][0]["evidence"][0]["quote"]
    assert AnalysisRun.objects.filter(case=case).count() == 1

    analyze_case.delay(str(case.id))
    assert AnalysisRun.objects.filter(case=case).count() == 1

    second = client.post("/api/v1/cases/", payload, format="json")
    assert second.status_code == 201
    assert second.data["id"] == first.data["id"]
    assert second.data["deduplicated"] is True
    assert Case.objects.count() == 1


@pytest.mark.django_db
def test_case_text_validation(client):
    response = client.post("/api/v1/cases/", {"title": "Short", "source_text": "too short"}, format="json")
    assert response.status_code == 400
    assert "source_text" in response.data["error"]["detail"]


@pytest.mark.django_db
def test_users_cannot_read_other_users_cases(client):
    other = User.objects.create_user(username="other")
    case = Case.objects.create(
        owner=other,
        title="Private",
        source_text="A sufficiently long private case description for access control.",
        content_hash="x" * 64,
    )
    response = client.get(f"/api/v1/cases/{case.id}/")
    assert response.status_code == 404
