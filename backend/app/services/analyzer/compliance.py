import re
from .base import BaseAnalyzer, AnalysisResult, TestCase


class ComplianceAnalyzer(BaseAnalyzer):
    category = "compliance"
    tests = [
        TestCase("pii_handling", "Detect PII processing patterns", 1.3),
        TestCase("data_retention_policy", "Check for data cleanup mechanisms", 1.0),
        TestCase("audit_logging", "Detect audit trail patterns", 1.0),
        TestCase("gdpr_indicators", "Right to deletion, consent patterns", 1.2),
        TestCase("license_compatibility", "Detect license headers", 0.8),
        TestCase("tos_compliance", "Detect ToS-aware patterns", 0.8),
        TestCase("output_filtering", "Detect content filtering mechanisms", 1.0),
        TestCase("user_consent_mechanisms", "Check for consent checks", 1.0),
        TestCase("data_minimization", "Unnecessary data collection detection", 1.0),
        TestCase("regulatory_framework_awareness", "HIPAA, FERPA patterns for sensitive domains", 1.2),
    ]

    def _run_test(self, test_name: str, code: str, language: str) -> AnalysisResult:
        handlers = {
            "pii_handling": self._test_pii,
            "data_retention_policy": self._test_data_retention,
            "audit_logging": self._test_audit_logging,
            "gdpr_indicators": self._test_gdpr,
            "license_compatibility": self._test_license,
            "tos_compliance": self._test_tos,
            "output_filtering": self._test_output_filtering,
            "user_consent_mechanisms": self._test_consent,
            "data_minimization": self._test_data_minimization,
            "regulatory_framework_awareness": self._test_regulatory,
        }
        fn = handlers.get(test_name)
        if fn:
            return fn(code, language)
        return AnalysisResult(test_name=test_name, status="skip", score=50.0)

    def _test_pii(self, code: str, language: str) -> AnalysisResult:
        pii_collection = self._find_matches(code, [
            r"(?i)(email|phone|ssn|social_security|date_of_birth|dob|address|zip_code|credit_card)",
            r"(?i)(full_name|first_name|last_name|username|user_id|personal)",
            r"(?i)(medical|health|diagnosis|prescription|insurance)",
        ])
        pii_protection = self._has_pattern(code, [
            r"encrypt|decrypt",
            r"hash\s*\(",
            r"bcrypt|argon2|pbkdf2",
            r"anonymize|pseudonymize|mask",
            r"redact",
            r"pii_filter",
            r"scrub\s*\(",
            r"sha\d+\s*\(",
        ])

        if not pii_collection:
            return AnalysisResult(
                test_name="pii_handling", status="pass", score=90.0,
                details={"message": "No PII collection patterns detected", "pii_fields": []}
            )

        if pii_protection:
            return AnalysisResult(
                test_name="pii_handling", status="pass", score=80.0,
                details={"message": f"PII fields detected with protection measures",
                         "pii_fields": pii_collection[:5], "has_protection": True}
            )
        else:
            return AnalysisResult(
                test_name="pii_handling", status="warning", score=40.0,
                details={"message": f"PII fields detected without explicit protection measures",
                         "pii_fields": pii_collection[:5], "has_protection": False}
            )

    def _test_data_retention(self, code: str, language: str) -> AnalysisResult:
        retention_patterns = [
            r"delete.*old",
            r"purge\s*\(",
            r"cleanup\s*\(",
            r"expire\s*=",
            r"ttl\s*=",
            r"retention",
            r"max_age",
            r"scheduled_deletion",
            r"cascade.*delete",
            r"DELETE.*WHERE.*date",
        ]
        count = self._count_pattern(code, retention_patterns)

        if count >= 2:
            return AnalysisResult(
                test_name="data_retention_policy", status="pass", score=88.0,
                details={"message": f"Data retention/cleanup mechanisms detected ({count})",
                         "retention_indicators": count}
            )
        elif count == 1:
            return AnalysisResult(
                test_name="data_retention_policy", status="warning", score=60.0,
                details={"message": "Minimal data retention policy detected", "retention_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="data_retention_policy", status="warning", score=35.0,
                details={"message": "No data retention/cleanup mechanisms found; data may accumulate indefinitely",
                         "retention_indicators": 0}
            )

    def _test_audit_logging(self, code: str, language: str) -> AnalysisResult:
        audit_patterns = [
            r"audit_log",
            r"audit\s*\(",
            r"log_action",
            r"log_event",
            r"activity_log",
            r"access_log",
            r"logger\.(info|warning|error|critical)\s*\(",
            r"logging\.(info|warning|error|critical)\s*\(",
            r"structured_log",
            r"log\.write",
        ]
        count = self._count_pattern(code, audit_patterns)
        fn_count = self._count_functions(code, language)
        ratio = count / max(fn_count, 1)

        if ratio >= 0.5 or count >= 5:
            return AnalysisResult(
                test_name="audit_logging", status="pass", score=92.0,
                details={"message": f"Comprehensive audit logging detected ({count} patterns)",
                         "audit_count": count, "function_count": fn_count}
            )
        elif count >= 2:
            return AnalysisResult(
                test_name="audit_logging", status="pass", score=70.0,
                details={"message": f"Some audit logging present ({count} patterns)",
                         "audit_count": count, "function_count": fn_count}
            )
        elif count >= 1:
            return AnalysisResult(
                test_name="audit_logging", status="warning", score=50.0,
                details={"message": "Minimal audit logging", "audit_count": count}
            )
        else:
            return AnalysisResult(
                test_name="audit_logging", status="warning", score=25.0,
                details={"message": "No audit logging detected; consider adding audit trails",
                         "audit_count": 0}
            )

    def _test_gdpr(self, code: str, language: str) -> AnalysisResult:
        gdpr_patterns = [
            r"(?i)right.to.deletion|right.to.erasure",
            r"(?i)gdpr",
            r"(?i)data.subject",
            r"(?i)consent\s*=",
            r"(?i)withdraw.consent",
            r"(?i)data.portability",
            r"delete.user.data",
            r"forget.me",
            r"opt.?out",
            r"unsubscribe",
            r"privacy.policy",
        ]
        count = self._count_pattern(code, gdpr_patterns)

        if count >= 3:
            return AnalysisResult(
                test_name="gdpr_indicators", status="pass", score=90.0,
                details={"message": f"Strong GDPR compliance indicators ({count})", "gdpr_indicators": count}
            )
        elif count >= 1:
            return AnalysisResult(
                test_name="gdpr_indicators", status="warning", score=60.0,
                details={"message": f"Some GDPR-related patterns found ({count}); ensure full compliance",
                         "gdpr_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="gdpr_indicators", status="warning", score=35.0,
                details={"message": "No GDPR compliance patterns detected; review data handling requirements",
                         "gdpr_indicators": 0}
            )

    def _test_license(self, code: str, language: str) -> AnalysisResult:
        license_patterns = [
            r"(?i)MIT License",
            r"(?i)Apache License",
            r"(?i)GNU General Public License",
            r"(?i)BSD License",
            r"(?i)Copyright \(c\)",
            r"(?i)SPDX-License-Identifier",
            r"(?i)Licensed under",
            r"(?i)All rights reserved",
        ]
        has_license = self._has_pattern(code, license_patterns)

        if has_license:
            return AnalysisResult(
                test_name="license_compatibility", status="pass", score=90.0,
                details={"message": "License header detected in code"}
            )
        else:
            return AnalysisResult(
                test_name="license_compatibility", status="warning", score=50.0,
                details={"message": "No license header detected; consider adding license information"}
            )

    def _test_tos(self, code: str, language: str) -> AnalysisResult:
        tos_patterns = [
            r"(?i)terms.of.service",
            r"(?i)terms.and.conditions",
            r"(?i)acceptable.use",
            r"(?i)usage.policy",
            r"(?i)api.usage",
            r"(?i)rate.limit.*policy",
            r"(?i)prohibited",
            r"(?i)not.allowed",
            r"content_policy",
            r"usage_guidelines",
        ]
        count = self._count_pattern(code, tos_patterns)

        if count >= 2:
            return AnalysisResult(
                test_name="tos_compliance", status="pass", score=85.0,
                details={"message": f"ToS-aware patterns detected ({count})", "tos_indicators": count}
            )
        elif count == 1:
            return AnalysisResult(
                test_name="tos_compliance", status="warning", score=60.0,
                details={"message": "Minimal ToS awareness detected", "tos_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="tos_compliance", status="warning", score=40.0,
                details={"message": "No Terms of Service compliance patterns detected",
                         "tos_indicators": 0}
            )

    def _test_output_filtering(self, code: str, language: str) -> AnalysisResult:
        filter_patterns = [
            r"content.filter",
            r"output.filter",
            r"moderate\s*\(",
            r"moderation",
            r"safe.content",
            r"harmful.content",
            r"profanity",
            r"nsfw",
            r"content.guard",
            r"filter.response",
            r"sanitize.output",
            r"guardrail",
        ]
        count = self._count_pattern(code, filter_patterns)

        # Check if it's an LLM agent
        is_llm = self._has_pattern(code, [r"openai\.", r"anthropic\.", r"llm\.", r"completion"])

        if not is_llm:
            return AnalysisResult(
                test_name="output_filtering", status="skip", score=70.0,
                details={"message": "No LLM output detected; output filtering test not fully applicable"}
            )

        if count >= 2:
            return AnalysisResult(
                test_name="output_filtering", status="pass", score=90.0,
                details={"message": f"Output filtering/moderation patterns detected ({count})",
                         "filter_indicators": count}
            )
        elif count == 1:
            return AnalysisResult(
                test_name="output_filtering", status="warning", score=60.0,
                details={"message": "Minimal output filtering detected", "filter_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="output_filtering", status="warning", score=30.0,
                details={"message": "No output filtering for LLM responses detected",
                         "filter_indicators": 0}
            )

    def _test_consent(self, code: str, language: str) -> AnalysisResult:
        consent_patterns = [
            r"(?i)user.consent",
            r"(?i)consent\s*==\s*True",
            r"(?i)has.consent",
            r"(?i)accepted.terms",
            r"(?i)agreed.to",
            r"(?i)opt.in",
            r"(?i)permission\s*=",
            r"(?i)user.agreed",
            r"(?i)confirm\s*\(",
            r"(?i)ask.permission",
        ]
        count = self._count_pattern(code, consent_patterns)

        if count >= 2:
            return AnalysisResult(
                test_name="user_consent_mechanisms", status="pass", score=88.0,
                details={"message": f"User consent mechanisms detected ({count})", "consent_indicators": count}
            )
        elif count == 1:
            return AnalysisResult(
                test_name="user_consent_mechanisms", status="warning", score=58.0,
                details={"message": "Minimal consent mechanisms detected", "consent_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="user_consent_mechanisms", status="warning", score=30.0,
                details={"message": "No explicit user consent mechanisms detected",
                         "consent_indicators": 0}
            )

    def _test_data_minimization(self, code: str, language: str) -> AnalysisResult:
        # Detect patterns that collect excessive data
        excessive_collection = self._find_matches(code, [
            r"SELECT\s+\*\s+FROM",
            r"\*\s+FROM\s+\w+",
            r"get_all_fields",
            r"dump\s*\(\)",
            r"\.to_dict\s*\(\)",
            r"vars\s*\(\)",
            r"__dict__",
        ])
        minimization = self._has_pattern(code, [
            r"SELECT\s+\w+(?:,\s*\w+)*\s+FROM",
            r"only\s*=\s*\[",
            r"fields\s*=\s*\[",
            r"exclude\s*=\s*\[",
            r"select_related",
        ])

        if len(excessive_collection) == 0:
            return AnalysisResult(
                test_name="data_minimization", status="pass", score=85.0,
                details={"message": "No excessive data collection patterns detected"}
            )
        elif minimization:
            return AnalysisResult(
                test_name="data_minimization", status="pass", score=72.0,
                details={"message": "Broad data access found with field selection patterns",
                         "broad_queries": len(excessive_collection)}
            )
        else:
            return AnalysisResult(
                test_name="data_minimization", status="warning", score=45.0,
                details={"message": f"Found {len(excessive_collection)} broad data access pattern(s); use field selection",
                         "broad_queries": len(excessive_collection)}
            )

    def _test_regulatory(self, code: str, language: str) -> AnalysisResult:
        hipaa_patterns = [
            r"(?i)hipaa",
            r"(?i)phi\s*=",
            r"(?i)protected.health",
            r"(?i)medical.record",
            r"(?i)patient.data",
        ]
        ferpa_patterns = [
            r"(?i)ferpa",
            r"(?i)student.record",
            r"(?i)educational.record",
        ]
        general_regulatory = [
            r"(?i)pci.dss",
            r"(?i)sox\s",
            r"(?i)ccpa",
            r"(?i)regulatory",
            r"(?i)compliance",
            r"(?i)data.protection",
        ]

        hipaa_count = self._count_pattern(code, hipaa_patterns)
        ferpa_count = self._count_pattern(code, ferpa_patterns)
        general_count = self._count_pattern(code, general_regulatory)

        total = hipaa_count + ferpa_count + general_count

        if hipaa_count > 0 or ferpa_count > 0:
            frameworks = []
            if hipaa_count > 0:
                frameworks.append("HIPAA")
            if ferpa_count > 0:
                frameworks.append("FERPA")
            return AnalysisResult(
                test_name="regulatory_framework_awareness", status="pass", score=85.0,
                details={"message": f"Regulatory framework awareness detected: {', '.join(frameworks)}",
                         "frameworks": frameworks, "indicator_count": total}
            )
        elif general_count >= 2:
            return AnalysisResult(
                test_name="regulatory_framework_awareness", status="pass", score=75.0,
                details={"message": f"General compliance awareness detected ({general_count} patterns)",
                         "indicator_count": general_count}
            )
        elif general_count == 1:
            return AnalysisResult(
                test_name="regulatory_framework_awareness", status="warning", score=55.0,
                details={"message": "Minimal regulatory awareness", "indicator_count": general_count}
            )
        else:
            return AnalysisResult(
                test_name="regulatory_framework_awareness", status="warning", score=40.0,
                details={"message": "No regulatory framework patterns detected; review applicable regulations",
                         "indicator_count": 0}
            )
