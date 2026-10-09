# Latency-security trade-offs of inline runtime security guards in containerized RAG microservices

This repository is a lightweight reproduction of the defense idea behind the paper "Rescuing the Unpoisoned: Efficient Defense against Knowledge Corruption Attacks on RAG Systems". The goal is to make the underlying algorithm runnable, benchmarkable, and easy to extend while keeping the paper's two-stage logic intact.

## Project goal

The original paper focuses on detection accuracy for poisoned retrieval. This project intentionally adds the missing service-level angle by benchmarking the cost of running such guards inline in a containerized system.

## What is implemented

- A minimal RAGDefender-style defense pipeline
- Synthetic benchmark datasets modeled after the NQ / HotpotQA / MS MARCO retrieval setting
- A containerized FastAPI service for latency and throughput measurement
- A CLI and claim-style scripts for reproducible runs
- A benchmark output format that can be compared against a paper table

## Repository layout

- `ragdefender/` — implementation code
- `examples/` — quick-start examples
- `artifacts/` — environment and benchmark output directory
- `claims/` — claim-style run scripts
- `docs/` — reproduction notes

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python examples/basic_usage.py
python -m ragdefender.cli reproduce --claim claim1_poisonedrag --seed 42
```

## Run the claim scripts

```bash
./claims/claim1_poisonedrag/run.sh
./claims/claim2_tan/run.sh
./claims/claim3_garag/run.sh
```

## Run the benchmark service

```bash
uvicorn ragdefender.service:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/benchmark
```

## Research gap and motivation

The likely gap is not purely algorithmic; it is service-level: the defense is evaluated on detection quality, but the deployment cost of filtering adversarial passages under load is not measured. This repository measures:

- median / p95 / p99 latency
- throughput under contention
- memory and CPU overhead of the guard
- effect of the filter on answer quality and attack removal rate

## Minimal reproduction summary

The project uses a CPU-friendly synthetic dataset instead of the full public datasets to keep the pipeline reproducible and testable in a limited environment. The logic still preserves the core pattern of the paper: semantic clustering plus adversarial outlier filtering.

## Reproduction notes

See [docs/reproducing-paper.md](docs/reproducing-paper.md) for a deeper summary of how this maps onto the public paper and the dataset structure.
