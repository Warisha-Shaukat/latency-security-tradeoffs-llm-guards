from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .benchmark import run_service_benchmark
from .datasets import generate_synthetic_dataset
from .defense import RAGDefender, evaluate_defense


def _claim_result(claim: str, seed: int = 42) -> dict:
    dataset = generate_synthetic_dataset(seed=seed, examples=80)
    metrics = evaluate_defense(dataset, top_k=3)
    benchmark = run_service_benchmark(claim_name=claim, seed=seed, repetitions=25)
    payload = {
        "claim": claim,
        "dataset_size": len(dataset),
        "metrics": metrics,
        "benchmark": benchmark.to_json(),
    }
    output_dir = Path("artifacts/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{claim}.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="RAGDefender reproduction CLI")
    parser.add_argument("command", choices=["reproduce", "benchmark"], help="Which workflow to run")
    parser.add_argument("--claim", default="claim1_poisonedrag", help="Claim to execute")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible runs")
    args = parser.parse_args()

    if args.command == "reproduce":
        payload = _claim_result(args.claim, seed=args.seed)
        print(json.dumps(payload, indent=2))
    elif args.command == "benchmark":
        report = run_service_benchmark(claim_name=args.claim, seed=args.seed, repetitions=25)
        print(json.dumps(report.to_json(), indent=2))


if __name__ == "__main__":
    main()
