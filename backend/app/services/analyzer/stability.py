import re
from .base import BaseAnalyzer, AnalysisResult, TestCase


class StabilityAnalyzer(BaseAnalyzer):
    category = "stability"
    tests = [
        TestCase("error_handling_coverage", "Ratio of try/except blocks to function count", 1.3),
        TestCase("infinite_loop_detection", "Detect while True without break conditions", 1.2),
        TestCase("recursion_depth_protection", "Detect recursive calls without depth limit", 1.1),
        TestCase("resource_leak_detection", "Detect unclosed files/connections", 1.2),
        TestCase("timeout_implementation", "Check if API calls have timeouts", 1.0),
        TestCase("graceful_degradation", "Check for fallback mechanisms", 0.9),
        TestCase("state_management", "Detect global mutable state issues", 1.0),
        TestCase("memory_management", "Detect large allocations in loops", 0.8),
        TestCase("concurrency_safety", "Detect race condition patterns", 1.0),
        TestCase("exception_specificity", "Bare except vs specific exceptions", 0.9),
    ]

    def _run_test(self, test_name: str, code: str, language: str) -> AnalysisResult:
        dispatch = {
            "error_handling_coverage": self._test_error_handling,
            "infinite_loop_detection": self._test_infinite_loops,
            "recursion_depth_protection": self._test_recursion,
            "resource_leak_detection": self._test_resource_leaks,
            "timeout_implementation": self._test_timeouts,
            "graceful_degradation": self._test_degradation,
            "state_management": self._test_state,
            "memory_management": self._test_memory,
            "concurrency_safety": self._test_concurrency,
            "exception_specificity": self._test_exception_specificity,
        }
        fn = dispatch.get(test_name)
        if fn:
            return fn(code, language)
        return AnalysisResult(test_name=test_name, status="skip", score=50.0)

    def _test_error_handling(self, code: str, language: str) -> AnalysisResult:
        try_blocks = len(re.findall(r"\btry\s*[:{]", code, re.MULTILINE))
        catch_blocks = len(re.findall(
            r"\b(?:except|catch|rescue|rescue\s+=>)\s*", code, re.MULTILINE))
        fn_count = self._count_functions(code, language)
        ratio = (try_blocks + catch_blocks) / (2 * max(fn_count, 1))
        score = min(100, ratio * 120)
        status = "pass" if score >= 60 else ("warning" if score >= 30 else "fail")
        return AnalysisResult(
            test_name="error_handling_coverage", status=status, score=score,
            details={"try_blocks": try_blocks, "catch_blocks": catch_blocks,
                     "functions": fn_count, "coverage_ratio": round(ratio, 2),
                     "message": f"{try_blocks} try blocks across {fn_count} functions"}
        )

    def _test_infinite_loops(self, code: str, language: str) -> AnalysisResult:
        while_true = len(re.findall(r"\bwhile\s+True\s*:", code))
        while_1 = len(re.findall(r"\bwhile\s+1\s*[:{]", code))
        total = while_true + while_1
        if total == 0:
            return AnalysisResult(
                test_name="infinite_loop_detection", status="pass", score=100.0,
                details={"message": "No infinite loop patterns detected"}
            )
        # Check for break/return inside loops
        breaks = len(re.findall(r"\b(?:break|return|sys\.exit|exit)\b", code))
        has_exits = breaks >= total
        score = 75 if has_exits else 30
        status = "warning" if has_exits else "fail"
        return AnalysisResult(
            test_name="infinite_loop_detection", status=status, score=score,
            details={"infinite_loops": total, "exit_statements": breaks, "has_exits": has_exits,
                     "message": f"{total} infinite loop(s) found; {'break/exit found' if has_exits else 'no guaranteed exit'}"}
        )

    def _test_recursion(self, code: str, language: str) -> AnalysisResult:
        fn_names = re.findall(r"def\s+(\w+)\s*\(", code)
        recursive = []
        for fn in fn_names:
            # simple heuristic: function body calls itself
            body_pat = rf"def\s+{fn}\s*\([^)]*\).*?(?=\ndef\s|\Z)"
            match = re.search(body_pat, code, re.DOTALL)
            if match and re.search(rf"\b{fn}\s*\(", match.group(0)[match.group(0).find(':'):]):
                recursive.append(fn)
        if not recursive:
            return AnalysisResult(
                test_name="recursion_depth_protection", status="pass", score=100.0,
                details={"message": "No recursive functions detected"}
            )
        depth_limits = self._has_pattern(code, [
            r"sys\.setrecursionlimit|RecursionError|depth\s*[<>]=?\s*\d+",
            r"max_depth|recursion_limit|depth_limit",
        ])
        score = 80 if depth_limits else 40
        status = "pass" if depth_limits else "warning"
        return AnalysisResult(
            test_name="recursion_depth_protection", status=status, score=score,
            details={"recursive_functions": recursive, "has_depth_limit": depth_limits,
                     "message": f"{len(recursive)} recursive function(s); depth protection {'present' if depth_limits else 'missing'}"}
        )

    def _test_resource_leaks(self, code: str, language: str) -> AnalysisResult:
        raw_opens = len(re.findall(r"\bopen\s*\(", code))
        context_opens = len(re.findall(r"\bwith\s+open\s*\(", code))
        conn_opens = len(re.findall(r"\.connect\s*\(|\.get_connection\s*\(", code))
        conn_closes = len(re.findall(r"\.close\s*\(\)|\.disconnect\s*\(", code))
        context_managers = len(re.findall(r"\bwith\s+\w+", code))

        unclosed_files = max(0, raw_opens - context_opens)
        issues = []
        if unclosed_files > 0:
            issues.append(f"{unclosed_files} file(s) opened without context manager")
        if conn_opens > 0 and conn_closes == 0 and context_managers < conn_opens:
            issues.append(f"{conn_opens} connection(s) without explicit close")

        if not issues:
            return AnalysisResult(
                test_name="resource_leak_detection", status="pass", score=95.0,
                details={"message": "No resource leak patterns detected",
                         "context_managers_used": context_opens}
            )
        score = max(30, 90 - len(issues) * 20)
        return AnalysisResult(
            test_name="resource_leak_detection", status="warning", score=score,
            details={"issues": issues, "message": "; ".join(issues)}
        )

    def _test_timeouts(self, code: str, language: str) -> AnalysisResult:
        api_calls = self._has_pattern(code, [
            r"requests\.\w+\s*\(", r"httpx\.\w+\s*\(", r"urllib\.request",
            r"openai\.", r"anthropic\.", r"boto3\.", r"aiohttp\.",
        ])
        timeouts = self._has_pattern(code, [
            r"timeout\s*=\s*\d+",
            r"timeout\s*=\s*\w+",
            r"asyncio\.wait_for",
            r"asyncio\.timeout",
            r"signal\.alarm",
            r"socket\.settimeout",
        ])
        if not api_calls:
            return AnalysisResult(
                test_name="timeout_implementation", status="skip", score=75.0,
                details={"message": "No external API calls detected"}
            )
        if timeouts:
            return AnalysisResult(
                test_name="timeout_implementation", status="pass", score=95.0,
                details={"message": "Timeout parameters detected on external calls"}
            )
        return AnalysisResult(
            test_name="timeout_implementation", status="warning", score=40.0,
            details={"message": "External API calls found without timeout parameters — risk of hanging"}
        )

    def _test_degradation(self, code: str, language: str) -> AnalysisResult:
        fallbacks = self._find_matches(code, [
            r"except.*:\s*\n\s*return\s+(?:None|{}\|\[\]|default)",
            r"fallback|default_response|backup|retry",
            r"@retry|tenacity|backoff",
            r"or\s+default|\.get\s*\([^,]+,\s*\w+\)",
            r"if\s+\w+\s+is\s+None.*else",
        ])
        score = min(100, 50 + len(fallbacks) * 12)
        status = "pass" if score >= 70 else "warning"
        return AnalysisResult(
            test_name="graceful_degradation", status=status, score=score,
            details={"fallback_patterns": len(fallbacks),
                     "message": f"{len(fallbacks)} graceful degradation pattern(s) detected"}
        )

    def _test_state(self, code: str, language: str) -> AnalysisResult:
        globals_found = self._find_matches(code, [
            r"^[A-Z_]{3,}\s*=\s*\[",
            r"^[A-Z_]{3,}\s*=\s*\{",
            r"\bglobal\s+\w+",
        ])
        thread_safe = self._has_pattern(code, [
            r"threading\.Lock|asyncio\.Lock|RLock|Semaphore",
            r"@property|__slots__",
        ])
        if not globals_found:
            return AnalysisResult(
                test_name="state_management", status="pass", score=90.0,
                details={"message": "No problematic global mutable state detected"}
            )
        score = 70 if thread_safe else 45
        status = "warning"
        return AnalysisResult(
            test_name="state_management", status=status, score=score,
            details={"global_state": globals_found, "thread_safe": thread_safe,
                     "message": f"{len(globals_found)} mutable global state(s); {'thread-safe patterns present' if thread_safe else 'no thread safety'}"}
        )

    def _test_memory(self, code: str, language: str) -> AnalysisResult:
        issues = self._find_matches(code, [
            r"for\s+\w+\s+in\s+\w+:.*\n\s*\w+\.append",
            r"while.*:\s*\n.*list\s*\+=",
            r"\[\s*\w+\s+for\s+\w+\s+in\s+\w+\s*\]\s*\*",
            r"\.readlines\(\)",
        ])
        generators = self._has_pattern(code, [
            r"\byield\b|\bgenerator\b|itertools\.",
            r"\(.*for.*in.*\)",
        ])
        score = 100 if not issues else (80 if generators else 55)
        status = "pass" if score >= 70 else "warning"
        return AnalysisResult(
            test_name="memory_management", status=status, score=score,
            details={"potential_issues": len(issues), "uses_generators": generators,
                     "message": f"{len(issues)} potential memory issue(s) in loops"}
        )

    def _test_concurrency(self, code: str, language: str) -> AnalysisResult:
        async_code = self._has_pattern(code, [r"\basync\s+def\b", r"\bawait\b"])
        threading_code = self._has_pattern(code, [r"\bthreading\b", r"\bconcurrent\.futures\b"])
        locks = self._has_pattern(code, [
            r"threading\.Lock|asyncio\.Lock|asyncio\.Semaphore",
            r"with\s+lock|async\s+with\s+\w+lock",
        ])
        shared_state = self._has_pattern(code, [
            r"\bglobal\s+\w+",
            r"^[a-z_]+\s*=\s*\[\]|^[a-z_]+\s*=\s*\{\}",
        ])
        if not (async_code or threading_code):
            return AnalysisResult(
                test_name="concurrency_safety", status="pass", score=85.0,
                details={"message": "No concurrency patterns detected; single-threaded assumed"}
            )
        if shared_state and not locks:
            return AnalysisResult(
                test_name="concurrency_safety", status="warning", score=45.0,
                details={"message": "Concurrent code with shared state but no locking mechanisms detected"}
            )
        return AnalysisResult(
            test_name="concurrency_safety", status="pass", score=90.0,
            details={"async": async_code, "threading": threading_code, "has_locks": locks,
                     "message": "Concurrency patterns detected with appropriate synchronization"}
        )

    def _test_exception_specificity(self, code: str, language: str) -> AnalysisResult:
        bare_except = len(re.findall(r"\bexcept\s*:", code))
        broad_except = len(re.findall(r"\bexcept\s+Exception\s*:", code))
        specific = len(re.findall(
            r"\bexcept\s+(?:ValueError|TypeError|KeyError|IOError|OSError|RuntimeError|"
            r"AttributeError|IndexError|ImportError|NotImplementedError|"
            r"ConnectionError|TimeoutError|PermissionError)\b", code))
        total = bare_except + broad_except + specific
        if total == 0:
            return AnalysisResult(
                test_name="exception_specificity", status="skip", score=70.0,
                details={"message": "No exception handlers found"}
            )
        specificity_ratio = specific / total
        score = min(100, 50 + specificity_ratio * 50)
        status = "pass" if score >= 70 else ("warning" if score >= 40 else "fail")
        return AnalysisResult(
            test_name="exception_specificity", status=status, score=score,
            details={"bare_except": bare_except, "broad_except": broad_except,
                     "specific_except": specific, "specificity_ratio": round(specificity_ratio, 2),
                     "message": f"{specific}/{total} specific exception handlers ({round(specificity_ratio*100)}%)"}
        )
