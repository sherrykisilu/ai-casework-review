import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings

from .schemas import AnalysisResult

PROMPT_VERSION = "case-review-v1"


class ProviderError(Exception):
    pass


class ProviderRateLimitError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass


@dataclass
class ProviderResponse:
    result: AnalysisResult
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class BaseProvider:
    def analyze(self, text: str) -> ProviderResponse:
        raise NotImplementedError


class DemoProvider(BaseProvider):
    rules = [
        ("compliance", "high", ("breach", "regulator", "gdpr", "privacy", "consent")),
        ("customer_risk", "high", ("cancel", "fraud", "unsafe", "harm", "legal")),
        ("urgency", "high", ("urgent", "immediately", "today", "deadline")),
        ("support_quality", "medium", ("ignored", "no response", "unresolved", "escalate")),
    ]

    def analyze(self, text: str) -> ProviderResponse:
        started = time.monotonic()
        findings = []
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        lowered = text.lower()
        for category, severity, terms in self.rules:
            matches = [term for term in terms if term in lowered]
            if not matches:
                continue
            evidence_sentence = next(
                (sentence for sentence in sentences if any(term in sentence.lower() for term in matches)),
                text[:500],
            )
            findings.append(
                {
                    "category": category,
                    "severity": severity,
                    "summary": f"Potential {category.replace('_', ' ')} signal detected.",
                    "evidence": [
                        {
                            "quote": evidence_sentence[:500],
                            "rationale": f"Matched review signal: {', '.join(matches[:3])}.",
                        }
                    ],
                }
            )
        result = AnalysisResult.model_validate(
            {
                "summary": (
                    f"Deterministic review identified {len(findings)} evidence-backed signal(s)."
                    if findings
                    else "No configured risk signals were found in the supplied text."
                ),
                "findings": findings,
                "recommended_actions": (
                    ["Verify the cited evidence and route confirmed issues to the responsible reviewer."]
                    if findings
                    else ["Record the review outcome; no automated escalation is suggested."]
                ),
                "limitations": [
                    "Demo mode uses transparent keyword rules and does not infer intent.",
                    "A human reviewer must verify every finding before action.",
                ],
                "confidence": 0.85 if findings else 0.65,
            }
        )
        return ProviderResponse(
            result=result,
            provider="demo",
            model="demo-rules-v1",
            input_tokens=max(1, len(text.split())),
            output_tokens=max(1, len(result.model_dump_json().split())),
            latency_ms=max(1, int((time.monotonic() - started) * 1000)),
        )


class OpenAICompatibleProvider(BaseProvider):
    def analyze(self, text: str) -> ProviderResponse:
        if not settings.AI_API_KEY:
            raise ProviderError("AI_API_KEY is required for the configured provider")
        started = time.monotonic()
        prompt = (
            "Return JSON only. Review the case text for customer risk, compliance, support quality, "
            "and urgency. Every finding must include a verbatim quote. Follow this JSON schema: "
            f"{json.dumps(AnalysisResult.model_json_schema())}\nCASE TEXT:\n{text}"
        )
        payload = json.dumps(
            {
                "model": settings.AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
        ).encode()
        request = urllib.request.Request(
            settings.AI_API_URL,
            data=payload,
            headers={"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise ProviderRateLimitError("Provider rate limit exceeded") from exc
            raise ProviderError(f"Provider returned HTTP {exc.code}") from exc
        except TimeoutError as exc:
            raise ProviderTimeoutError("Provider request timed out") from exc
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return ProviderResponse(
            result=AnalysisResult.model_validate_json(content),
            provider=settings.AI_PROVIDER,
            model=settings.AI_MODEL,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=max(1, int((time.monotonic() - started) * 1000)),
        )


def get_provider() -> BaseProvider:
    if settings.AI_PROVIDER == "demo":
        return DemoProvider()
    return OpenAICompatibleProvider()
