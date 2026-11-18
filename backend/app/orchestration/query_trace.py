"""
query_trace.py
~~~~~~~~~~~~~~
Lightweight per-request pipeline tracer.

Usage:
    trace = QueryTrace()
    with trace.step("embed"):
        embeddings = embedder.embed(texts)
    # Later:
    print(trace.summary())
"""

import time
from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import Generator


@dataclass
class StepTiming:
    name: str
    duration_ms: float


@dataclass
class QueryTrace:
    steps: list[StepTiming] = field(default_factory=list)

    @contextmanager
    def step(self, name: str) -> Generator[None, None, None]:
        """Context manager to time a named pipeline step."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.steps.append(StepTiming(name=name, duration_ms=round(elapsed_ms, 2)))

    def summary(self) -> dict[str, float]:
        """Return a dict of step_name → duration_ms."""
        return {s.name: s.duration_ms for s in self.steps}

    def total_ms(self) -> float:
        return sum(s.duration_ms for s in self.steps)
