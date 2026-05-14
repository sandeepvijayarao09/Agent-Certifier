import re
from .base import BaseAnalyzer, AnalysisResult, TestCase


class InformaticsAnalyzer(BaseAnalyzer):
    category = "informatics"
    tests = [
        TestCase("code_complexity", "Cyclomatic complexity estimation", 1.2),
        TestCase("documentation_coverage", "Docstring ratio to functions/classes", 1.1),
        TestCase("function_modularity", "Average function length", 1.0),
        TestCase("type_annotation_coverage", "Typed vs untyped parameters", 1.1),
        TestCase("response_format_consistency", "Consistent return type patterns", 0.9),
        TestCase("logging_implementation", "Proper logging vs raw print statements", 1.0),
        TestCase("configuration_externalization", "Env vars vs hardcoded config values", 1.2),
        TestCase("api_contract_clarity", "Clear input/output definitions", 1.0),
        TestCase("naming_convention", "PEP8/camelCase consistency", 0.8),
        TestCase("code_duplication_risk", "Repeated code block patterns", 0.8),
    ]

    def _run_test(self, test_name: str, code: str, language: str) -> AnalysisResult:
        dispatch = {
            "code_complexity": self._test_complexity,
            "documentation_coverage": self._test_documentation,
            "function_modularity": self._test_modularity,
            "type_annotation_coverage": self._test_types,
            "response_format_consistency": self._test_response_format,
            "logging_implementation": self._test_logging,
            "configuration_externalization": self._test_config,
            "api_contract_clarity": self._test_api_contract,
            "naming_convention": self._test_naming,
            "code_duplication_risk": self._test_duplication,
        }
        fn = dispatch.get(test_name)
        if fn:
            return fn(code, language)
        return AnalysisResult(test_name=test_name, status="skip", score=50.0)

    def _test_complexity(self, code: str, language: str) -> AnalysisResult:
        decision_points = len(re.findall(
            r"\b(?:if|elif|else|for|while|try|except|case|when|&&|\|\|)\b", code))
        fn_count = max(self._count_functions(code, language), 1)
        avg_complexity = decision_points / fn_count
        if avg_complexity <= 5:
            score, status, msg = 95, "pass", "Low complexity — excellent"
        elif avg_complexity <= 10:
            score, status, msg = 75, "pass", "Moderate complexity — acceptable"
        elif avg_complexity <= 20:
            score, status, msg = 50, "warning", "High complexity — consider refactoring"
        else:
            score, status, msg = 25, "fail", "Very high complexity — refactoring strongly recommended"
        return AnalysisResult(
            test_name="code_complexity", status=status, score=score,
            details={"decision_points": decision_points, "functions": fn_count,
                     "avg_cyclomatic": round(avg_complexity, 1), "message": msg}
        )

    def _test_documentation(self, code: str, language: str) -> AnalysisResult:
        if language == "Python":
            docstrings = len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code))
            fns = self._count_functions(code, language)
            classes = len(re.findall(r"^class\s+\w+", code, re.MULTILINE))
            total = fns + classes
        else:
            docstrings = len(re.findall(
                r"/\*\*[\s\S]*?\*/|///[^\n]*|#\s+\w{3,}[^\n]*", code))
            total = max(self._count_functions(code, language), 1)

        ratio = docstrings / max(total, 1)
        score = min(100, ratio * 100)
        status = "pass" if score >= 60 else ("warning" if score >= 30 else "fail")
        return AnalysisResult(
            test_name="documentation_coverage", status=status, score=score,
            details={"docstrings": docstrings, "documentable_items": total,
                     "coverage_pct": round(ratio * 100, 1),
                     "message": f"{round(ratio*100)}% documentation coverage"}
        )

    def _test_modularity(self, code: str, language: str) -> AnalysisResult:
        lines = self._count_lines(code)
        fn_count = max(self._count_functions(code, language), 1)
        avg_len = lines / fn_count
        if avg_len <= 20:
            score, status = 100, "pass"
        elif avg_len <= 40:
            score, status = 80, "pass"
        elif avg_len <= 60:
            score, status = 60, "warning"
        elif avg_len <= 100:
            score, status = 40, "warning"
        else:
            score, status = 20, "fail"
        return AnalysisResult(
            test_name="function_modularity", status=status, score=score,
            details={"total_lines": lines, "functions": fn_count,
                     "avg_function_lines": round(avg_len, 1),
                     "message": f"Average function length: {round(avg_len)} lines"}
        )

    def _test_types(self, code: str, language: str) -> AnalysisResult:
        if language in ("TypeScript", "Java", "C#", "Rust", "Go"):
            return AnalysisResult(
                test_name="type_annotation_coverage", status="pass", score=95.0,
                details={"message": f"{language} is statically typed — full type coverage assumed"}
            )
        typed_params = len(re.findall(r"def\s+\w+\s*\([^)]*:\s*\w+[^)]*\)", code))
        untyped_fns = len(re.findall(r"def\s+\w+\s*\([^)]*\)\s*:", code))
        return_types = len(re.findall(r"def\s+\w+\s*\([^)]*\)\s*->\s*\w+", code))
        total = max(untyped_fns, 1)
        ratio = (typed_params + return_types) / (total * 2)
        score = min(100, ratio * 100)
        status = "pass" if score >= 60 else ("warning" if score >= 30 else "fail")
        return AnalysisResult(
            test_name="type_annotation_coverage", status=status, score=score,
            details={"typed_functions": typed_params, "return_typed": return_types,
                     "total_functions": total, "coverage_pct": round(ratio * 100, 1),
                     "message": f"{round(ratio*100)}% type annotation coverage"}
        )

    def _test_response_format(self, code: str, language: str) -> AnalysisResult:
        returns = len(re.findall(r"\breturn\b", code))
        consistent_patterns = self._find_matches(code, [
            r"return\s*\{['\"](?:status|result|data|error|success)['\"]",
            r"return\s+\w+Model\s*\(",
            r"return\s+dataclass",
            r"JSONResponse|jsonify|json\.dumps",
            r"TypedDict|dataclass|@dataclass",
        ])
        if returns == 0:
            return AnalysisResult(
                test_name="response_format_consistency", status="skip", score=70.0,
                details={"message": "No return statements found"}
            )
        ratio = len(consistent_patterns) / max(returns / 3, 1)
        score = min(100, 50 + ratio * 30)
        status = "pass" if score >= 65 else "warning"
        return AnalysisResult(
            test_name="response_format_consistency", status=status, score=score,
            details={"return_statements": returns, "consistent_patterns": len(consistent_patterns),
                     "message": f"{len(consistent_patterns)} structured response patterns detected"}
        )

    def _test_logging(self, code: str, language: str) -> AnalysisResult:
        print_statements = len(re.findall(r"\bprint\s*\(|console\.log\s*\(", code))
        proper_logging = len(re.findall(
            r"logging\.\w+\s*\(|logger\.\w+\s*\(|log\.\w+\s*\(|winston\.|pino\.", code))
        total = print_statements + proper_logging
        if total == 0:
            return AnalysisResult(
                test_name="logging_implementation", status="warning", score=60.0,
                details={"message": "No logging or print statements found"}
            )
        ratio = proper_logging / total
        score = min(100, ratio * 100)
        if print_statements == 0:
            score = min(100, score + 10)
        status = "pass" if score >= 70 else ("warning" if score >= 40 else "fail")
        return AnalysisResult(
            test_name="logging_implementation", status=status, score=score,
            details={"print_statements": print_statements, "proper_logging": proper_logging,
                     "logging_ratio": round(ratio * 100, 1),
                     "message": f"{proper_logging} proper log calls vs {print_statements} print statements"}
        )

    def _test_config(self, code: str, language: str) -> AnalysisResult:
        env_usage = len(re.findall(
            r"os\.environ|os\.getenv|process\.env\.|dotenv|getenv|config\[", code))
        hardcoded = self._find_matches(code, [
            r"[\"']https?://[a-zA-Z0-9.-]+[\"']",
            r"port\s*=\s*\d{4,5}",
            r"host\s*=\s*[\"'][\d.]+[\"']",
            r"db_name\s*=\s*[\"']\w+[\"']",
        ])
        if env_usage > 0 and len(hardcoded) == 0:
            return AnalysisResult(
                test_name="configuration_externalization", status="pass", score=95.0,
                details={"env_vars_used": env_usage, "message": "Configuration properly externalized via env vars"}
            )
        if len(hardcoded) == 0:
            return AnalysisResult(
                test_name="configuration_externalization", status="pass", score=80.0,
                details={"message": "No hardcoded config values detected"}
            )
        score = max(30, 80 - len(hardcoded) * 10 + env_usage * 5)
        return AnalysisResult(
            test_name="configuration_externalization", status="warning", score=min(score, 100),
            details={"hardcoded_values": hardcoded, "env_vars_used": env_usage,
                     "message": f"{len(hardcoded)} hardcoded config value(s) found — prefer env vars"}
        )

    def _test_api_contract(self, code: str, language: str) -> AnalysisResult:
        contract_patterns = self._find_matches(code, [
            r"@app\.\w+\s*\([\"']/",
            r"pydantic|BaseModel|TypedDict|dataclass",
            r"openapi|swagger|@api\.",
            r"FastAPI|Flask|Express|gin\.",
            r"def\s+\w+\s*\([^)]*:\s*\w+[^)]*\)\s*->",
        ])
        score = min(100, 40 + len(contract_patterns) * 12)
        status = "pass" if score >= 70 else "warning"
        return AnalysisResult(
            test_name="api_contract_clarity", status=status, score=score,
            details={"contract_patterns": len(contract_patterns),
                     "message": f"{len(contract_patterns)} API contract definition pattern(s) detected"}
        )

    def _test_naming(self, code: str, language: str) -> AnalysisResult:
        if language in ("JavaScript", "TypeScript", "Java", "C#"):
            camel = len(re.findall(r"\b[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b", code))
            snake = len(re.findall(r"\b[a-z][a-z0-9]*_[a-z][a-z0-9_]*\b", code))
            dominant = max(camel, snake)
            total = camel + snake
            ratio = dominant / max(total, 1)
        elif language == "Python":
            snake = len(re.findall(r"\b[a-z][a-z0-9]*_[a-z][a-z0-9_]*\b", code))
            camel = len(re.findall(r"\b[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b", code))
            fn_names = re.findall(r"def\s+([a-zA-Z_]\w*)", code)
            snake_fns = sum(1 for f in fn_names if "_" in f or f.islower())
            ratio = snake_fns / max(len(fn_names), 1)
        else:
            ratio = 0.7
        score = min(100, ratio * 100)
        status = "pass" if score >= 70 else "warning"
        return AnalysisResult(
            test_name="naming_convention", status=status, score=score,
            details={"consistency_ratio": round(ratio, 2),
                     "message": f"{round(ratio*100)}% naming convention consistency"}
        )

    def _test_duplication(self, code: str, language: str) -> AnalysisResult:
        lines = [l.strip() for l in code.splitlines() if len(l.strip()) > 20]
        seen = {}
        dupes = 0
        for line in lines:
            seen[line] = seen.get(line, 0) + 1
            if seen[line] == 2:
                dupes += 1
        total = max(len(lines), 1)
        dupe_ratio = dupes / total
        score = max(0, 100 - dupe_ratio * 200)
        status = "pass" if score >= 80 else ("warning" if score >= 60 else "fail")
        return AnalysisResult(
            test_name="code_duplication_risk", status=status, score=score,
            details={"duplicate_lines": dupes, "total_lines": total,
                     "duplication_pct": round(dupe_ratio * 100, 1),
                     "message": f"{round(dupe_ratio*100, 1)}% code duplication estimated"}
        )
