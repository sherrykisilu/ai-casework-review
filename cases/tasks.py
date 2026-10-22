from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError

from .models import AnalysisRun, Case
from .providers import (
    PROMPT_VERSION,
    DemoProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    get_provider,
)


@shared_task(
    bind=True,
    max_retries=3,
)
def analyze_case(self, case_id: str):
    with transaction.atomic():
        case = Case.objects.select_for_update().get(id=case_id)
        if case.status == Case.Status.COMPLETED:
            return case.result
        case.status = Case.Status.PROCESSING
        case.progress = 15
        case.error_code = ""
        case.error_message = ""
        case.save(update_fields=["status", "progress", "error_code", "error_message", "updated_at"])

    provider = get_provider()
    run = AnalysisRun.objects.create(
        case=case,
        status=AnalysisRun.Status.STARTED,
        provider=provider.__class__.__name__,
        model=getattr(provider, "model", "configured"),
        prompt_version=PROMPT_VERSION,
        retry_count=self.request.retries,
    )
    try:
        case.progress = 45
        case.save(update_fields=["progress", "updated_at"])
        response = provider.analyze(case.source_text)
        case.result = response.result.model_dump()
        case.status = Case.Status.COMPLETED
        case.progress = 100
        case.save(update_fields=["result", "status", "progress", "updated_at"])
        run.status = AnalysisRun.Status.SUCCEEDED
        run.provider = response.provider
        run.model = response.model
        run.input_tokens = response.input_tokens
        run.output_tokens = response.output_tokens
        run.latency_ms = response.latency_ms
        run.completed_at = timezone.now()
        run.save()
        return case.result
    except SoftTimeLimitExceeded:
        _mark_failed(case, run, "analysis_timeout", "Analysis exceeded the worker time limit", AnalysisRun.Status.TIMED_OUT)
        raise
    except (ProviderRateLimitError, ProviderTimeoutError) as exc:
        if self.request.retries < self.max_retries:
            run.status = AnalysisRun.Status.FAILED
            run.error_code = "provider_retry"
            run.completed_at = timezone.now()
            run.save()
            raise self.retry(exc=exc, countdown=2 ** (self.request.retries + 1))
        return _use_fallback(case, run, exc)
    except (ProviderError, ValidationError, KeyError, ValueError) as exc:
        return _use_fallback(case, run, exc)
    except Exception:
        _mark_failed(case, run, "analysis_failed", "Analysis failed and can be retried", AnalysisRun.Status.FAILED)
        raise


def _mark_failed(case, run, code, message, run_status):
    case.status = Case.Status.FAILED
    case.progress = 0
    case.error_code = code
    case.error_message = message
    case.save()
    run.status = run_status
    run.error_code = code
    run.completed_at = timezone.now()
    run.save()


def _use_fallback(case, run, exc):
    fallback = DemoProvider().analyze(case.source_text)
    case.result = fallback.result.model_copy(
        update={"limitations": fallback.result.limitations + ["Configured provider failed; deterministic fallback was used."]}
    ).model_dump()
    case.status = Case.Status.COMPLETED
    case.progress = 100
    case.error_code = "provider_fallback"
    case.error_message = str(exc)[:500]
    case.save()
    run.status = AnalysisRun.Status.FAILED
    run.error_code = "provider_fallback"
    run.completed_at = timezone.now()
    run.save()
    return case.result
