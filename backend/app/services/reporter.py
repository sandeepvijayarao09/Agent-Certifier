from datetime import datetime, timedelta
from typing import List
from app.models.agent import Agent
from app.models.test_result import TestResult
from app.core.config import settings
from app.services.analyzer.standards import TEST_STANDARDS, resolve_standard, standards_for


CATEGORY_WEIGHTS = {
    "security": 0.30,
    "stability": 0.20,
    "performance": 0.15,
    "informatics": 0.15,
    "compliance": 0.10,
    "ethics": 0.10,
}


def get_certification_level(score: float) -> str:
    if score >= 90:
        return "PLATINUM"
    elif score >= 80:
        return "GOLD"
    elif score >= 70:
        return "SILVER"
    elif score >= 60:
        return "BRONZE"
    return "NOT_CERTIFIED"


class ReportGenerator:
    def generate(self, agent: Agent, test_results: List[TestResult]) -> dict:
        # Group by category
        categories: dict = {}
        for tr in test_results:
            cat = tr.category.lower()
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tr)

        # Calculate category scores
        category_scores = {}
        weighted_total = 0.0
        total_weight = 0.0

        for cat, weight in CATEGORY_WEIGHTS.items():
            tests = categories.get(cat, [])
            if tests:
                scores = [t.score for t in tests]
                avg_score = sum(scores) / len(scores)
                passed = sum(1 for t in tests if t.status.value == "pass")
                failed = sum(1 for t in tests if t.status.value == "fail")
                warnings = sum(1 for t in tests if t.status.value == "warning")
                skipped = sum(1 for t in tests if t.status.value == "skip")

                category_scores[cat] = {
                    "score": round(avg_score, 1),
                    "weight": weight,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings,
                    "skipped": skipped,
                    "total": len(tests),
                }
                weighted_total += avg_score * weight
                total_weight += weight
            else:
                category_scores[cat] = {
                    "score": 0.0,
                    "weight": weight,
                    "passed": 0,
                    "failed": 0,
                    "warnings": 0,
                    "skipped": 0,
                    "total": 0,
                }

        # Prefer the score the orchestrator persisted so every endpoint agrees
        if agent.overall_score is not None:
            overall_score = agent.overall_score
            certification_level = agent.certification_level or get_certification_level(overall_score)
        else:
            overall_score = round(weighted_total / total_weight, 1) if total_weight > 0 else 0.0
            certification_level = get_certification_level(overall_score)

        # Identify critical issues (failed tests)
        critical_issues = []
        for tr in test_results:
            if tr.status.value == "fail":
                critical_issues.append({
                    "category": tr.category,
                    "test_name": tr.test_name,
                    "score": tr.score,
                    "details": tr.details,
                    "standards": standards_for(tr.test_name),
                })

        # Collect warnings
        warnings = []
        for tr in test_results:
            if tr.status.value == "warning":
                warnings.append({
                    "category": tr.category,
                    "test_name": tr.test_name,
                    "score": tr.score,
                    "details": tr.details,
                    "standards": standards_for(tr.test_name),
                })

        # Generate recommendations
        recommendations = self._generate_recommendations(category_scores, critical_issues, warnings)

        # Build test details grouped by category
        test_details = {}
        for cat in CATEGORY_WEIGHTS:
            tests = categories.get(cat, [])
            test_details[cat] = [
                {
                    "test_name": t.test_name,
                    "status": t.status.value,
                    "score": t.score,
                    "details": t.details,
                    "duration_ms": t.duration_ms,
                    "standards": standards_for(t.test_name),
                }
                for t in tests
            ]

        # Standards coverage: which external controls / frameworks the agent
        # was measured against, and whether it passes them.
        standards_coverage, frameworks = self._standards_coverage(test_results)

        test_date = datetime.utcnow().isoformat() + "Z"
        valid_until = (datetime.utcnow() + timedelta(days=settings.certification_expiry_days)).isoformat() + "Z"

        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "filename": agent.filename,
            "language": agent.language,
            "file_size": agent.file_size,
            "test_date": test_date,
            "overall_score": overall_score,
            "certification_level": certification_level,
            "category_scores": category_scores,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "test_details": test_details,
            "standards_coverage": standards_coverage,
            "frameworks": frameworks,
            "certification_valid_until": valid_until,
            "total_tests": len(test_results),
            "passed_tests": sum(1 for t in test_results if t.status.value == "pass"),
            "failed_tests": sum(1 for t in test_results if t.status.value == "fail"),
            "warning_tests": sum(1 for t in test_results if t.status.value == "warning"),
            "skipped_tests": sum(1 for t in test_results if t.status.value == "skip"),
        }

    @staticmethod
    def _worst_status(current: str, incoming: str) -> str:
        """Combine two statuses keeping the most severe (fail > warning > pass > skip)."""
        severity = {"fail": 3, "warning": 2, "pass": 1, "skip": 0}
        return incoming if severity.get(incoming, 0) > severity.get(current, 0) else current

    def _standards_coverage(self, test_results: List[TestResult]):
        """Aggregate results per standard control and per framework.

        Returns (coverage, frameworks) where coverage is a list of per-control
        objects (ranked most-severe first) and frameworks is a per-framework
        rollup. A control's status is the most severe status among the tests
        mapped to it, so a single failing test flags the whole control.
        """
        by_code: dict = {}
        for tr in test_results:
            for code in TEST_STANDARDS.get(tr.test_name, []):
                entry = by_code.setdefault(code, {
                    "status": "skip", "scores": [],
                    "passed": 0, "failed": 0, "warnings": 0, "skipped": 0,
                    "tests": [],
                })
                status = tr.status.value
                entry["status"] = self._worst_status(entry["status"], status)
                entry["scores"].append(tr.score)
                entry["tests"].append(f"{tr.category}/{tr.test_name}")
                key = {"pass": "passed", "fail": "failed",
                       "warning": "warnings", "skip": "skipped"}.get(status)
                if key:
                    entry[key] += 1

        coverage = []
        for code, e in by_code.items():
            ref = resolve_standard(code)
            scores = e["scores"]
            coverage.append({
                **ref,
                "status": e["status"],
                "score": round(sum(scores) / len(scores), 1) if scores else 0.0,
                "passed": e["passed"],
                "failed": e["failed"],
                "warnings": e["warnings"],
                "skipped": e["skipped"],
                "total": len(scores),
                "tests": sorted(set(e["tests"])),
            })

        severity = {"fail": 3, "warning": 2, "pass": 1, "skip": 0}
        coverage.sort(key=lambda c: (-severity.get(c["status"], 0), c["framework"], c["code"]))

        # Per-framework rollup
        fw: dict = {}
        for c in coverage:
            f = fw.setdefault(c["framework"], {
                "framework": c["framework"], "url": c["url"],
                "controls": 0, "passed": 0, "failed": 0, "warnings": 0, "scores": [],
            })
            f["controls"] += 1
            f["scores"].append(c["score"])
            if c["status"] == "fail":
                f["failed"] += 1
            elif c["status"] == "warning":
                f["warnings"] += 1
            elif c["status"] == "pass":
                f["passed"] += 1

        frameworks = []
        for f in fw.values():
            scores = f.pop("scores")
            f["score"] = round(sum(scores) / len(scores), 1) if scores else 0.0
            frameworks.append(f)
        frameworks.sort(key=lambda f: (-f["failed"], -f["warnings"], f["framework"]))

        return coverage, frameworks

    def _generate_recommendations(
        self, category_scores: dict, critical_issues: list, warnings: list
    ) -> List[str]:
        recommendations = []

        # Category-specific recommendations based on low scores
        score_recommendations = {
            "security": {
                40: "CRITICAL: Address security vulnerabilities immediately — injection risks, hardcoded secrets, or direct LLM output execution detected.",
                65: "Review and remediate security findings. Consider adding input validation, authentication, and removing hardcoded credentials.",
                80: "Security posture is adequate. Consider adding more comprehensive authentication and authorization checks.",
            },
            "stability": {
                40: "CRITICAL: Stability issues found — add error handling, fix infinite loops, and address resource leaks.",
                65: "Improve error handling coverage and add timeouts to all external API calls.",
                80: "Stability looks good. Consider adding graceful degradation fallbacks.",
            },
            "performance": {
                40: "Performance needs significant improvement — consider async I/O, caching, and connection pooling.",
                65: "Add caching for frequently accessed data and consider async operations for I/O.",
                80: "Performance is reasonable. Consider adding streaming support and batch processing.",
            },
            "informatics": {
                40: "Code quality needs improvement — add documentation, reduce complexity, and improve naming conventions.",
                65: "Add docstrings to functions, improve type annotations, and use proper logging instead of print statements.",
                80: "Good code quality. Consider adding more type annotations and API contract definitions.",
            },
            "compliance": {
                40: "Compliance gaps detected — address PII handling, add audit logging, and implement data retention policies.",
                65: "Review GDPR requirements, add user consent mechanisms, and implement output filtering.",
                80: "Compliance is adequate. Consider adding explicit regulatory framework references.",
            },
            "ethics": {
                40: "Ethics concerns detected — add bias detection, transparency disclosures, and harm prevention mechanisms.",
                65: "Add AI transparency disclosures, refusal mechanisms for harmful requests, and human oversight hooks.",
                80: "Ethics implementation is good. Consider adding explainability features and accountability mechanisms.",
            },
        }

        for cat, thresholds in score_recommendations.items():
            cat_data = category_scores.get(cat, {})
            score = cat_data.get("score", 0)
            for threshold, rec in sorted(thresholds.items()):
                if score < threshold:
                    recommendations.append(rec)
                    break

        # Add specific recommendations from critical issues
        seen_categories = set()
        for issue in critical_issues[:3]:  # Top 3 critical issues
            cat = issue.get("category", "")
            if cat not in seen_categories:
                test_name = issue.get("test_name", "")
                details = issue.get("details", {})
                msg = details.get("message", f"Fix {test_name} in {cat} category")
                recommendations.append(f"Fix: {msg}")
                seen_categories.add(cat)

        return recommendations[:10]  # Limit to 10 recommendations
