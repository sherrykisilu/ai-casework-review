import json
from pathlib import Path

from cases.providers import DemoProvider


def evaluate():
    fixtures = json.loads((Path(__file__).parent / "fixtures" / "v1" / "cases.json").read_text())
    provider = DemoProvider()
    unsupported = false_positives = missed = total_expected = total_forbidden = total_findings = 0
    for fixture in fixtures:
        result = provider.analyze(fixture["text"]).result
        categories = {finding.category for finding in result.findings}
        total_findings += len(result.findings)
        total_expected += len(fixture["expected_categories"])
        total_forbidden += len(fixture["forbidden_categories"])
        missed += len(set(fixture["expected_categories"]) - categories)
        false_positives += len(set(fixture["forbidden_categories"]) & categories)
        unsupported += sum(
            1
            for finding in result.findings
            for evidence in finding.evidence
            if evidence.quote not in fixture["text"]
        )
    metrics = {
        "unsupported_claim_rate": unsupported / max(1, total_findings),
        "false_positive_rate": false_positives / max(1, total_forbidden),
        "miss_rate": missed / max(1, total_expected),
        "fixture_version": "v1",
    }
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    evaluate()
