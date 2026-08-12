import time
from dataclasses import dataclass, field
from typing import List, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class TestCase:
    name: str
    description: str
    weight: float = 1.0


@dataclass
class AnalysisResult:
    test_name: str
    status: str  # pass/fail/warning/skip
    score: float  # 0-100
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


class BaseAnalyzer(ABC):
    category: str = "base"
    tests: List[TestCase] = []

    def analyze(self, agent_code: str, language: str) -> List[AnalysisResult]:
        results = []
        for test_case in self.tests:
            start = time.time()
            try:
                result = self._run_test(test_case.name, agent_code, language)
                result.duration_ms = (time.time() - start) * 1000
            except Exception as e:
                result = AnalysisResult(
                    test_name=test_case.name,
                    status="skip",
                    score=50.0,
                    details={"error": str(e), "message": "Test execution error"},
                    duration_ms=(time.time() - start) * 1000,
                )
            results.append(result)
        return results

    @abstractmethod
    def _run_test(self, test_name: str, code: str, language: str) -> AnalysisResult:
        pass

    def _count_pattern(self, code: str, patterns: List[str]) -> int:
        import re
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, code, re.IGNORECASE | re.MULTILINE))
        return count

    def _has_pattern(self, code: str, patterns: List[str]) -> bool:
        import re
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def _find_matches(self, code: str, patterns: List[str]) -> List[str]:
        import re
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
            matches.extend([str(f) if not isinstance(f, str) else f for f in found])
        return matches[:10]  # Limit to 10 matches

    def _count_functions(self, code: str, language: str) -> int:
        import re
        if language in ("Python",):
            return len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))
        elif language in ("JavaScript", "TypeScript"):
            fn_patterns = [
                r"function\s+\w+\s*\(",
                r"const\s+\w+\s*=\s*(?:async\s*)?\(",
                r"(?:async\s+)?(?:function\s*)?\w+\s*\([^)]*\)\s*(?::\s*\w+\s*)?\{",
            ]
            count = 0
            for p in fn_patterns:
                count += len(re.findall(p, code))
            return max(count, 1)
        elif language == "Go":
            return len(re.findall(r"^func\s+\w+", code, re.MULTILINE))
        elif language == "Java":
            return len(re.findall(r"(?:public|private|protected|static).*\w+\s*\(", code))
        else:
            return max(len(re.findall(r"def\s+\w+|function\s+\w+|func\s+\w+|\w+\s*\(", code)) // 3, 1)

    def _count_lines(self, code: str) -> int:
        return len([l for l in code.splitlines() if l.strip()])
