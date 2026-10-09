"""Minimal reproduction of the RAGDefender two-stage adversarial passage filtering idea."""

from .benchmark import BenchmarkReport, run_service_benchmark
from .datasets import RetrievalExample, generate_synthetic_dataset
from .defense import RAGDefender, evaluate_defense

__all__ = [
    "RAGDefender",
    "RetrievalExample",
    "generate_synthetic_dataset",
    "evaluate_defense",
    "BenchmarkReport",
    "run_service_benchmark",
]
