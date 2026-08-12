"""A deliberately runaway analyzer used to exercise the timeout hard-kill.

Kept in its own importable module so it unpickles cleanly in a worker process
regardless of the multiprocessing start method.
"""
import os
import time

from app.services.analyzer.base import BaseAnalyzer, AnalysisResult, TestCase


class SlowAnalyzer(BaseAnalyzer):
    category = "security"
    tests = [TestCase("slow_test", "spins far longer than the timeout")]

    def _run_test(self, test_name, code, language):
        return AnalysisResult(test_name=test_name, status="pass", score=100.0)

    def analyze(self, code, language):
        pid_file = os.environ.get("SLOW_PID_FILE")
        if pid_file:
            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))
        end = time.time() + 120
        x = 0
        while time.time() < end:
            x += 1  # busy-spin; a killed worker stops here
        return [AnalysisResult(test_name="slow_test", status="pass", score=100.0)]
