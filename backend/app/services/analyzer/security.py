import re
from .base import BaseAnalyzer, AnalysisResult, TestCase


class SecurityAnalyzer(BaseAnalyzer):
    category = "security"
    tests = [
        TestCase("injection_vulnerability", "Detect SQL/command injection patterns", 1.5),
        TestCase("hardcoded_secrets", "Detect hardcoded API keys, passwords, tokens", 1.5),
        TestCase("prompt_injection_resistance", "Check if agent sanitizes LLM inputs", 1.2),
        TestCase("data_exfiltration_risk", "Detect unsafe external data transmission", 1.2),
        TestCase("authentication_mechanisms", "Check for auth/authz implementations", 1.0),
        TestCase("input_validation", "Check if inputs are validated/sanitized", 1.0),
        TestCase("dependency_vulnerability", "Check for known dangerous import patterns", 1.0),
        TestCase("privilege_escalation_risk", "Detect dangerous permission requests", 1.0),
        TestCase("information_disclosure", "Detect verbose error messages leaking internals", 0.8),
        TestCase("llm_output_execution", "Detect if LLM output is directly executed", 1.3),
    ]

    def _run_test(self, test_name: str, code: str, language: str) -> AnalysisResult:
        if test_name == "injection_vulnerability":
            return self._test_injection(code, language)
        elif test_name == "hardcoded_secrets":
            return self._test_secrets(code, language)
        elif test_name == "prompt_injection_resistance":
            return self._test_prompt_injection(code, language)
        elif test_name == "data_exfiltration_risk":
            return self._test_exfiltration(code, language)
        elif test_name == "authentication_mechanisms":
            return self._test_auth(code, language)
        elif test_name == "input_validation":
            return self._test_input_validation(code, language)
        elif test_name == "dependency_vulnerability":
            return self._test_dependencies(code, language)
        elif test_name == "privilege_escalation_risk":
            return self._test_privilege(code, language)
        elif test_name == "information_disclosure":
            return self._test_info_disclosure(code, language)
        elif test_name == "llm_output_execution":
            return self._test_llm_output_exec(code, language)
        return AnalysisResult(test_name=test_name, status="skip", score=50.0)

    def _test_injection(self, code: str, language: str) -> AnalysisResult:
        dangerous = self._find_matches(code, [
            r"os\.system\s*\(",
            r"subprocess\.[a-z_]+\s*\([^)]*shell\s*=\s*True",
            r"\beval\s*\(",
            r"\bexec\s*\(",
            r"cursor\.execute\s*\([^)]*%\s*[({]",
            r"cursor\.execute\s*\([^)]*\+",
            r"f[\"'].*SELECT.*{",
            r"f[\"'].*INSERT.*{",
            r"f[\"'].*DELETE.*{",
            r"__import__\s*\(",
        ])
        if not dangerous:
            return AnalysisResult(
                test_name="injection_vulnerability", status="pass", score=100.0,
                details={"message": "No injection vulnerability patterns detected"}
            )
        score = max(0, 100 - len(dangerous) * 20)
        return AnalysisResult(
            test_name="injection_vulnerability",
            status="fail" if len(dangerous) >= 2 else "warning",
            score=score,
            details={"issues": dangerous, "count": len(dangerous),
                     "message": f"Found {len(dangerous)} potential injection vulnerability patterns"}
        )

    def _test_secrets(self, code: str, language: str) -> AnalysisResult:
        patterns = [
            r"(?:api_key|apikey|api-key)\s*=\s*[\"'][a-zA-Z0-9_\-]{16,}[\"']",
            r"(?:password|passwd|pwd)\s*=\s*[\"'][^\"']{4,}[\"']",
            r"(?:secret|token|access_token)\s*=\s*[\"'][a-zA-Z0-9_\-]{16,}[\"']",
            r"sk-[a-zA-Z0-9]{32,}",
            r"Bearer\s+[a-zA-Z0-9\-._~+/]{20,}",
            r"[\"'][A-Z0-9]{20}[\"']",
            r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        ]
        found = self._find_matches(code, patterns)
        env_usage = self._has_pattern(code, [
            r"os\.environ", r"os\.getenv", r"process\.env", r"dotenv", r"getenv"
        ])
        if not found:
            score = 100.0 if env_usage else 85.0
            return AnalysisResult(
                test_name="hardcoded_secrets", status="pass", score=score,
                details={"message": "No hardcoded secrets detected",
                         "uses_env_vars": env_usage}
            )
        score = max(0, 100 - len(found) * 25)
        return AnalysisResult(
            test_name="hardcoded_secrets", status="fail", score=score,
            details={"issues": found, "count": len(found),
                     "message": f"Found {len(found)} potential hardcoded secret(s)"}
        )

    def _test_prompt_injection(self, code: str, language: str) -> AnalysisResult:
        llm_calls = self._has_pattern(code, [
            r"openai\.", r"anthropic\.", r"\.chat\.", r"messages\s*=",
            r"system_prompt", r"user_input", r"llm\.invoke", r"chain\.run"
        ])
        sanitization = self._has_pattern(code, [
            r"sanitize|escape|strip|clean|validate|filter",
            r"re\.sub|re\.escape",
            r"html\.escape",
            r"bleach\.",
            r"allowlist|whitelist|blacklist|denylist",
        ])
        injection_patterns = self._has_pattern(code, [
            r"f[\"'].*\{.*user_input.*\}.*[Ss]ystem",
            r"f[\"'].*\{.*input.*\}.*instruction",
            r"\+\s*user_input\s*\+",
        ])
        if not llm_calls:
            return AnalysisResult(
                test_name="prompt_injection_resistance", status="skip", score=70.0,
                details={"message": "No LLM calls detected; test not applicable"}
            )
        if injection_patterns:
            return AnalysisResult(
                test_name="prompt_injection_resistance", status="fail", score=20.0,
                details={"message": "User input appears to be directly interpolated into system prompts"}
            )
        if sanitization:
            return AnalysisResult(
                test_name="prompt_injection_resistance", status="pass", score=90.0,
                details={"message": "Input sanitization patterns detected before LLM calls"}
            )
        return AnalysisResult(
            test_name="prompt_injection_resistance", status="warning", score=55.0,
            details={"message": "LLM calls found but no input sanitization detected"}
        )

    def _test_exfiltration(self, code: str, language: str) -> AnalysisResult:
        external_calls = self._find_matches(code, [
            r"requests\.(?:post|put|patch)\s*\(",
            r"httpx\.(?:post|put|patch)\s*\(",
            r"fetch\s*\([^)]*http",
            r"axios\.(?:post|put|patch)\s*\(",
            r"urllib\.request\.urlopen",
        ])
        validation = self._has_pattern(code, [
            r"allowlist|whitelist|approved_url|allowed_host",
            r"urlparse|urllib\.parse",
            r"ALLOWED_HOSTS|PERMITTED_ENDPOINTS",
        ])
        if not external_calls:
            return AnalysisResult(
                test_name="data_exfiltration_risk", status="pass", score=100.0,
                details={"message": "No external POST/PUT calls detected"}
            )
        score = 60 if not validation else 85
        status = "warning" if not validation else "pass"
        return AnalysisResult(
            test_name="data_exfiltration_risk", status=status, score=score,
            details={"external_calls": len(external_calls), "has_url_validation": validation,
                     "message": "External data transmissions found; ensure URL validation exists"}
        )

    def _test_auth(self, code: str, language: str) -> AnalysisResult:
        auth_patterns = self._has_pattern(code, [
            r"jwt\.|Bearer|OAuth|api_key|Authorization",
            r"authenticate|authorize|verify_token|check_permission",
            r"@require_auth|@login_required|@authenticated",
            r"middleware.*auth|auth.*middleware",
        ])
        if auth_patterns:
            return AnalysisResult(
                test_name="authentication_mechanisms", status="pass", score=90.0,
                details={"message": "Authentication/authorization patterns detected"}
            )
        return AnalysisResult(
            test_name="authentication_mechanisms", status="warning", score=55.0,
            details={"message": "No authentication mechanisms detected; consider adding auth"}
        )

    def _test_input_validation(self, code: str, language: str) -> AnalysisResult:
        validation_patterns = self._find_matches(code, [
            r"isinstance\s*\(",
            r"pydantic|BaseModel|Field\s*\(",
            r"marshmallow|schema\.validate",
            r"if\s+not\s+\w+:|if\s+\w+\s+is\s+None",
            r"raise\s+ValueError|raise\s+TypeError",
            r"assert\s+isinstance|assert\s+\w+",
            r"zod\.|joi\.|yup\.",
        ])
        fn_count = self._count_functions(code, language)
        ratio = len(validation_patterns) / max(fn_count, 1)
        score = min(100, 50 + ratio * 30)
        status = "pass" if score >= 70 else ("warning" if score >= 45 else "fail")
        return AnalysisResult(
            test_name="input_validation", status=status, score=score,
            details={"validation_patterns": len(validation_patterns), "functions": fn_count,
                     "message": f"Found {len(validation_patterns)} validation patterns across {fn_count} functions"}
        )

    def _test_dependencies(self, code: str, language: str) -> AnalysisResult:
        dangerous_imports = self._find_matches(code, [
            r"import\s+pickle\b",
            r"from\s+pickle\s+import",
            r"import\s+marshal\b",
            r"import\s+shelve\b",
            r"yaml\.load\s*\([^)]*Loader\s*=\s*None",
            r"yaml\.load\s*\([^,)]+\)",
            r"jsonpickle",
        ])
        safe_patterns = self._has_pattern(code, [
            r"yaml\.safe_load",
            r"json\.loads",
        ])
        if not dangerous_imports:
            return AnalysisResult(
                test_name="dependency_vulnerability", status="pass", score=95.0,
                details={"message": "No known dangerous import patterns detected"}
            )
        score = max(20, 80 - len(dangerous_imports) * 20)
        return AnalysisResult(
            test_name="dependency_vulnerability", status="warning", score=score,
            details={"dangerous": dangerous_imports,
                     "message": f"Found {len(dangerous_imports)} potentially unsafe deserialization imports"}
        )

    def _test_privilege(self, code: str, language: str) -> AnalysisResult:
        dangerous = self._find_matches(code, [
            r"chmod\s*\(\s*['\"]?[0-7]*7[0-7][0-7]",
            r"os\.chmod.*0o7",
            r"sudo\s+",
            r"setuid\s*\(",
            r"ctypes\.cdll|ctypes\.windll",
            r"win32api|win32con",
            r"subprocess.*sudo",
        ])
        if not dangerous:
            return AnalysisResult(
                test_name="privilege_escalation_risk", status="pass", score=100.0,
                details={"message": "No privilege escalation patterns detected"}
            )
        score = max(0, 100 - len(dangerous) * 30)
        return AnalysisResult(
            test_name="privilege_escalation_risk", status="fail", score=score,
            details={"issues": dangerous, "message": f"Found {len(dangerous)} privilege escalation risk(s)"}
        )

    def _test_info_disclosure(self, code: str, language: str) -> AnalysisResult:
        risky = self._find_matches(code, [
            r"traceback\.print_exc\(\)",
            r"print\s*\(\s*e\s*\)",
            r"print\s*\(\s*err\s*\)",
            r"console\.error\s*\(",
            r"str\s*\(\s*exception\s*\)",
            r"except.*:\s*\n\s*print",
        ])
        safe_logging = self._has_pattern(code, [
            r"logging\.(error|warning|critical)",
            r"logger\.(error|warning|critical)",
        ])
        if not risky:
            return AnalysisResult(
                test_name="information_disclosure", status="pass", score=90.0,
                details={"message": "No verbose error disclosure patterns detected",
                         "uses_proper_logging": safe_logging}
            )
        score = max(40, 90 - len(risky) * 10)
        return AnalysisResult(
            test_name="information_disclosure", status="warning", score=score,
            details={"issues": risky, "message": "Raw exception details may expose internals to users"}
        )

    def _test_llm_output_exec(self, code: str, language: str) -> AnalysisResult:
        exec_patterns = self._find_matches(code, [
            r"exec\s*\(\s*(?:response|output|result|llm_|ai_|completion)",
            r"eval\s*\(\s*(?:response|output|result|llm_|ai_|completion)",
            r"subprocess.*(?:response|output|result)",
            r"os\.system\s*\(\s*(?:response|output|result)",
        ])
        if not exec_patterns:
            return AnalysisResult(
                test_name="llm_output_execution", status="pass", score=100.0,
                details={"message": "No direct execution of LLM output detected"}
            )
        return AnalysisResult(
            test_name="llm_output_execution", status="fail", score=0.0,
            details={"issues": exec_patterns,
                     "message": "CRITICAL: LLM output appears to be directly executed — severe security risk"}
        )
