from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import asdict, dataclass
from typing import List

from .datasets import RetrievalExample, generate_synthetic_dataset
from .defense import RAGDefender


@dataclass
class BenchmarkReport:
    claim_name: str
    average_no_defense_latency_ms: float
    average_defended_latency_ms: float
    p50_no_defense_ms: float
    p95_no_defense_ms: float
    p99_no_defense_ms: float
    p50_defended_ms: float
    p95_defended_ms: float
    p99_defended_ms: float
    throughput_rps: float
    poison_removal_rate: float
    answer_recovery_rate: float

    def to_json(self, path: str | None = None) -> dict:
        payload = asdict(self)
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        return payload


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def run_service_benchmark(claim_name: str = "claim1_poisonedrag", seed: int = 42, repetitions: int = 30) -> BenchmarkReport:
    dataset = generate_synthetic_dataset(seed=seed, examples=64)
    defender = RAGDefender(top_k=3)

    no_defense_latencies: List[float] = []
    defended_latencies: List[float] = []

    total_poison_removed = 0
    total_poison_total = 0
    total_correct = 0

    for example in dataset[:repetitions]:
        start = time.perf_counter()
        _ = sorted(example.documents, key=lambda text: len(text), reverse=True)
        no_defense_latencies.append((time.perf_counter() - start) * 1000.0)

        start = time.perf_counter()
        result = defender.defend(example.query, example.documents, top_k=3)
        defended_latencies.append((time.perf_counter() - start) * 1000.0)

        total_poison_total += len(example.poisoned_indices)
        total_poison_removed += sum(1 for idx in example.poisoned_indices if idx in result.suspicious_indices)
        if example.answer in "\n".join(result.kept_documents):
            total_correct += 1

    throughput_rps = 1000.0 / max(statistics.median(defended_latencies), 1e-6)
    return BenchmarkReport(
        claim_name=claim_name,
        average_no_defense_latency_ms=float(statistics.mean(no_defense_latencies)),
        average_defended_latency_ms=float(statistics.mean(defended_latencies)),
        p50_no_defense_ms=float(_percentile(no_defense_latencies, 50)),
        p95_no_defense_ms=float(_percentile(no_defense_latencies, 95)),
        p99_no_defense_ms=float(_percentile(no_defense_latencies, 99)),
        p50_defended_ms=float(_percentile(defended_latencies, 50)),
        p95_defended_ms=float(_percentile(defended_latencies, 95)),
        p99_defended_ms=float(_percentile(defended_latencies, 99)),
        throughput_rps=float(throughput_rps),
        poison_removal_rate=(0.0 if total_poison_total == 0 else total_poison_removed / total_poison_total),
        answer_recovery_rate=(0.0 if not dataset else total_correct / len(dataset[:repetitions])),
    )
