from cases.providers import DemoProvider


def test_demo_provider_only_returns_evidence_from_input():
    text = "This is urgent. The customer reports a privacy breach and asks for an immediate response."
    result = DemoProvider().analyze(text).result
    assert result.findings
    for finding in result.findings:
        for evidence in finding.evidence:
            assert evidence.quote in text
