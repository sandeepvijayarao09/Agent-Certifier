import re
from .base import BaseAnalyzer, AnalysisResult, TestCase


class PerformanceAnalyzer(BaseAnalyzer):
    category = "performance"
    tests = [
        TestCase("caching_implementation", "Detect cache decorators/patterns", 1.2),
        TestCase("async_await_usage", "Sync vs async I/O operations", 1.3),
        TestCase("batch_processing_support", "Single vs batch-capable operations", 1.0),
        TestCase("connection_pooling", "Detect connection pool patterns", 1.0),
        TestCase("lazy_loading", "Detect eager vs lazy evaluation", 0.8),
        TestCase("algorithm_complexity", "Detect O(n²) patterns like nested loops on large data", 1.2),
        TestCase("streaming_support", "Detect streaming response patterns", 1.0),
        TestCase("rate_limit_awareness", "Detect rate limit handling", 1.0),
        TestCase("resource_cleanup", "Efficient resource usage", 1.0),
        TestCase("token_cost_optimization", "Detect token counting or cost-awareness patterns", 0.8),
    ]

    def _run_test(self, test_name: str, code: str, language: str) -> AnalysisResult:
        handlers = {
            "caching_implementation": self._test_caching,
            "async_await_usage": self._test_async,
            "batch_processing_support": self._test_batch,
            "connection_pooling": self._test_connection_pooling,
            "lazy_loading": self._test_lazy_loading,
            "algorithm_complexity": self._test_complexity,
            "streaming_support": self._test_streaming,
            "rate_limit_awareness": self._test_rate_limiting,
            "resource_cleanup": self._test_resource_cleanup,
            "token_cost_optimization": self._test_token_optimization,
        }
        fn = handlers.get(test_name)
        if fn:
            return fn(code, language)
        return AnalysisResult(test_name=test_name, status="skip", score=50.0)

    def _test_caching(self, code: str, language: str) -> AnalysisResult:
        cache_patterns = [
            r"@lru_cache",
            r"@cache",
            r"@functools\.cache",
            r"functools\.lru_cache",
            r"redis\.",
            r"memcache",
            r"cache\[",
            r"cache\.get\s*\(",
            r"cache\.set\s*\(",
            r"TTLCache|LRUCache|LFUCache",
            r"memoize|memoization",
            r"\.cache\s*=",
            r"_cache\s*=\s*\{\}",
            r"React\.memo|useMemo\(",
        ]
        count = self._count_pattern(code, cache_patterns)

        if count >= 3:
            return AnalysisResult(
                test_name="caching_implementation", status="pass", score=95.0,
                details={"message": f"Strong caching implementation detected ({count} patterns)", "cache_indicators": count}
            )
        elif count >= 1:
            return AnalysisResult(
                test_name="caching_implementation", status="pass", score=75.0,
                details={"message": f"Caching patterns detected ({count})", "cache_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="caching_implementation", status="warning", score=40.0,
                details={"message": "No caching patterns detected; consider adding caching for repeated operations", "cache_indicators": 0}
            )

    def _test_async(self, code: str, language: str) -> AnalysisResult:
        async_patterns = [
            r"\basync\s+def\b",
            r"\bawait\b",
            r"asyncio\.",
            r"aiohttp\.",
            r"httpx\.AsyncClient",
            r"aiofiles\.",
            r"Promise\.",
            r"\.then\s*\(",
            r"async\s*\(",
        ]
        sync_io_patterns = [
            r"requests\.get\s*\(",
            r"requests\.post\s*\(",
            r"time\.sleep\s*\(",
            r"open\s*\(",
            r"urllib\.request\.urlopen",
        ]
        async_count = self._count_pattern(code, async_patterns)
        sync_count = self._count_pattern(code, sync_io_patterns)
        total_io = async_count + sync_count

        if total_io == 0:
            return AnalysisResult(
                test_name="async_await_usage", status="skip", score=70.0,
                details={"message": "No I/O operations detected; async test not applicable"}
            )

        ratio = async_count / max(total_io, 1)
        if ratio >= 0.7:
            score = 90.0
            status = "pass"
            msg = f"Primarily async I/O ({async_count} async, {sync_count} sync)"
        elif ratio >= 0.4:
            score = 70.0
            status = "pass"
            msg = f"Mixed async/sync I/O ({async_count} async, {sync_count} sync)"
        elif async_count > 0:
            score = 50.0
            status = "warning"
            msg = f"Mostly synchronous I/O ({async_count} async, {sync_count} sync)"
        else:
            score = 25.0
            status = "warning"
            msg = "No async I/O patterns detected; consider async for better performance"

        return AnalysisResult(
            test_name="async_await_usage", status=status, score=score,
            details={"async_count": async_count, "sync_count": sync_count,
                     "async_ratio": round(ratio, 2), "message": msg}
        )

    def _test_batch(self, code: str, language: str) -> AnalysisResult:
        batch_patterns = [
            r"batch\s*=",
            r"chunks?\s*=",
            r"bulk\s*=",
            r"batch_size",
            r"chunk_size",
            r"\.batch\s*\(",
            r"bulk_create|bulk_insert|bulk_update",
            r"executemany\s*\(",
            r"pipe\s*\(",
            r"\[.*\bfor\b.*\].*\.map",
        ]
        count = self._count_pattern(code, batch_patterns)

        if count >= 2:
            return AnalysisResult(
                test_name="batch_processing_support", status="pass", score=90.0,
                details={"message": f"Batch processing patterns detected ({count})", "batch_indicators": count}
            )
        elif count == 1:
            return AnalysisResult(
                test_name="batch_processing_support", status="pass", score=70.0,
                details={"message": "Some batch processing support detected", "batch_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="batch_processing_support", status="warning", score=45.0,
                details={"message": "No batch processing patterns; single-item operations only", "batch_indicators": 0}
            )

    def _test_connection_pooling(self, code: str, language: str) -> AnalysisResult:
        pool_patterns = [
            r"connection_pool",
            r"ConnectionPool\s*\(",
            r"pool\s*=",
            r"Pool\s*\(",
            r"create_engine.*pool",
            r"pool_size",
            r"max_overflow",
            r"QueuePool",
            r"StaticPool",
            r"httpx\.Client\s*\(",
            r"requests\.Session\s*\(",
            r"keep_alive",
        ]
        no_pool_patterns = [
            r"requests\.get\s*\(",
            r"requests\.post\s*\(",
            r"sqlite3\.connect\s*\(",
            r"psycopg2\.connect\s*\(",
        ]
        has_pool = self._count_pattern(code, pool_patterns)
        no_pool = self._count_pattern(code, no_pool_patterns)

        if has_pool >= 1:
            return AnalysisResult(
                test_name="connection_pooling", status="pass", score=90.0,
                details={"message": f"Connection pooling patterns detected ({has_pool})", "pool_indicators": has_pool}
            )
        elif no_pool > 3:
            return AnalysisResult(
                test_name="connection_pooling", status="warning", score=35.0,
                details={"message": f"Found {no_pool} unpooled connections; consider using connection pools",
                         "unpooled_connections": no_pool}
            )
        elif no_pool > 0:
            return AnalysisResult(
                test_name="connection_pooling", status="warning", score=55.0,
                details={"message": "Direct connections detected; pooling could improve performance",
                         "unpooled_connections": no_pool}
            )
        else:
            return AnalysisResult(
                test_name="connection_pooling", status="skip", score=70.0,
                details={"message": "No database/HTTP connection patterns detected; test not applicable"}
            )

    def _test_lazy_loading(self, code: str, language: str) -> AnalysisResult:
        lazy_patterns = [
            r"\byield\b",
            r"\byield from\b",
            r"lazy\s*=\s*True",
            r"lazy_attribute",
            r"@property",
            r"__iter__",
            r"__next__",
            r"iter\s*\(",
            r"islice\s*\(",
            r"chain\s*\(",
        ]
        eager_patterns = [
            r"list\s*\(.*for.*in",
            r"\[.*for.*in.*\]",
            r"\.fetchall\s*\(",
        ]
        lazy_count = self._count_pattern(code, lazy_patterns)
        eager_count = self._count_pattern(code, eager_patterns)

        if lazy_count >= 3:
            return AnalysisResult(
                test_name="lazy_loading", status="pass", score=90.0,
                details={"message": f"Good lazy loading patterns ({lazy_count})", "lazy_indicators": lazy_count}
            )
        elif lazy_count >= 1:
            return AnalysisResult(
                test_name="lazy_loading", status="pass", score=70.0,
                details={"message": f"Some lazy evaluation patterns detected ({lazy_count})", "lazy_indicators": lazy_count}
            )
        elif eager_count > 5:
            return AnalysisResult(
                test_name="lazy_loading", status="warning", score=40.0,
                details={"message": "Primarily eager loading; consider generators for large datasets",
                         "eager_count": eager_count}
            )
        else:
            return AnalysisResult(
                test_name="lazy_loading", status="warning", score=55.0,
                details={"message": "No lazy loading patterns detected", "lazy_indicators": 0}
            )

    def _test_complexity(self, code: str, language: str) -> AnalysisResult:
        # Detect O(n²) patterns: nested loops
        nested_loop_patterns = [
            r"for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in\s+",
            r"for\s*\(.*\)\s*\{[^}]*for\s*\(",
            r"\.forEach.*\.forEach",
            r"for\s+\w+\s+in\s+\w+:\s*\n(?:.*\n)*?\s+for\s+\w+\s+in\s+\w+",
        ]
        sort_patterns = [
            r"\.sort\s*\(",
            r"sorted\s*\(",
            r"heapq\.",
            r"bisect\.",
        ]
        nested_count = self._count_pattern(code, nested_loop_patterns)
        sort_count = self._count_pattern(code, sort_patterns)
        lines = self._count_lines(code)

        # Estimate complexity
        if nested_count == 0:
            return AnalysisResult(
                test_name="algorithm_complexity", status="pass", score=90.0,
                details={"message": "No obvious O(n²) nested loop patterns detected",
                         "nested_loops": 0, "sort_operations": sort_count}
            )
        elif nested_count <= 2 and lines < 200:
            return AnalysisResult(
                test_name="algorithm_complexity", status="warning", score=60.0,
                details={"message": f"Found {nested_count} nested loop(s) — verify data sizes",
                         "nested_loops": nested_count, "sort_operations": sort_count}
            )
        else:
            return AnalysisResult(
                test_name="algorithm_complexity", status="fail", score=30.0,
                details={"message": f"Found {nested_count} nested loop(s) — potential O(n²) complexity",
                         "nested_loops": nested_count, "sort_operations": sort_count}
            )

    def _test_streaming(self, code: str, language: str) -> AnalysisResult:
        stream_patterns = [
            r"stream\s*=\s*True",
            r"yield\s+",
            r"StreamingResponse",
            r"EventSourceResponse",
            r"Server-Sent Events",
            r"stream\s*:",
            r"ReadableStream",
            r"asyncGenerator",
            r"async\s+for\s+",
            r"aiter\s*\(",
            r"stream_callback",
        ]
        count = self._count_pattern(code, stream_patterns)

        if count >= 2:
            return AnalysisResult(
                test_name="streaming_support", status="pass", score=90.0,
                details={"message": f"Streaming support patterns detected ({count})", "stream_indicators": count}
            )
        elif count == 1:
            return AnalysisResult(
                test_name="streaming_support", status="pass", score=70.0,
                details={"message": "Some streaming patterns detected", "stream_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="streaming_support", status="warning", score=45.0,
                details={"message": "No streaming patterns; consider streaming for large responses", "stream_indicators": 0}
            )

    def _test_rate_limiting(self, code: str, language: str) -> AnalysisResult:
        rate_patterns = [
            r"rate.?limit",
            r"RateLimiter",
            r"throttle",
            r"backoff",
            r"retry",
            r"sleep\s*\(\s*\d",
            r"time\.sleep",
            r"429",  # HTTP Too Many Requests
            r"Retry-After",
            r"ratelimit",
            r"tenacity\.",
        ]
        count = self._count_pattern(code, rate_patterns)

        if count >= 3:
            return AnalysisResult(
                test_name="rate_limit_awareness", status="pass", score=95.0,
                details={"message": f"Good rate limit handling ({count} patterns)", "rate_limit_indicators": count}
            )
        elif count >= 1:
            return AnalysisResult(
                test_name="rate_limit_awareness", status="pass", score=72.0,
                details={"message": f"Some rate limit awareness detected ({count})", "rate_limit_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="rate_limit_awareness", status="warning", score=35.0,
                details={"message": "No rate limit handling detected; API throttling may cause failures",
                         "rate_limit_indicators": 0}
            )

    def _test_resource_cleanup(self, code: str, language: str) -> AnalysisResult:
        cleanup_patterns = [
            r"with\s+",
            r"finally\s*:",
            r"__exit__",
            r"\.close\s*\(\)",
            r"\.cleanup\s*\(\)",
            r"\.dispose\s*\(\)",
            r"atexit\.",
            r"contextlib",
            r"defer\s+",  # Go
            r"using\s+\(",  # C#
        ]
        fn_count = self._count_functions(code, language)
        cleanup_count = self._count_pattern(code, cleanup_patterns)
        ratio = cleanup_count / max(fn_count, 1)

        if ratio >= 0.5:
            return AnalysisResult(
                test_name="resource_cleanup", status="pass", score=92.0,
                details={"message": f"Good resource cleanup practices ({cleanup_count} patterns)",
                         "cleanup_count": cleanup_count, "function_count": fn_count}
            )
        elif ratio >= 0.2:
            return AnalysisResult(
                test_name="resource_cleanup", status="pass", score=72.0,
                details={"message": f"Some resource cleanup patterns ({cleanup_count})",
                         "cleanup_count": cleanup_count, "function_count": fn_count}
            )
        elif cleanup_count > 0:
            return AnalysisResult(
                test_name="resource_cleanup", status="warning", score=50.0,
                details={"message": "Limited resource cleanup; check for leaks",
                         "cleanup_count": cleanup_count, "function_count": fn_count}
            )
        else:
            return AnalysisResult(
                test_name="resource_cleanup", status="warning", score=35.0,
                details={"message": "No explicit resource cleanup detected", "cleanup_count": 0}
            )

    def _test_token_optimization(self, code: str, language: str) -> AnalysisResult:
        token_patterns = [
            r"token_count",
            r"count_tokens",
            r"tiktoken",
            r"max_tokens",
            r"prompt_tokens",
            r"completion_tokens",
            r"total_tokens",
            r"cost\s*=",
            r"\.usage\.",
            r"truncate.*prompt",
            r"context_window",
            r"num_tokens",
        ]
        count = self._count_pattern(code, token_patterns)

        # Check if it's an LLM agent at all
        llm_patterns = [
            r"openai\.",
            r"anthropic\.",
            r"langchain",
            r"llm\.",
            r"completion\(",
        ]
        is_llm = self._has_pattern(code, llm_patterns)

        if not is_llm:
            return AnalysisResult(
                test_name="token_cost_optimization", status="skip", score=70.0,
                details={"message": "No LLM usage detected; token optimization test not applicable"}
            )

        if count >= 3:
            return AnalysisResult(
                test_name="token_cost_optimization", status="pass", score=95.0,
                details={"message": f"Strong token/cost awareness ({count} patterns)", "token_indicators": count}
            )
        elif count >= 1:
            return AnalysisResult(
                test_name="token_cost_optimization", status="pass", score=70.0,
                details={"message": f"Some token management patterns detected ({count})", "token_indicators": count}
            )
        else:
            return AnalysisResult(
                test_name="token_cost_optimization", status="warning", score=40.0,
                details={"message": "No token counting or cost optimization detected; may lead to unexpected costs",
                         "token_indicators": 0}
            )
