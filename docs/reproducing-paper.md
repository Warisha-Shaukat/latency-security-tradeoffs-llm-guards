# Reproducing the paper in a lightweight CPU-friendly form

This repository reproduces the core idea behind the RAGDefender paper in minimal form:

- retrieve a candidate set of passages for a query;
- group those passages by semantic relatedness;
- identify outlier passages that conflict with the dominant support cluster;
- benchmark the end-to-end cost of the defense in a containerized microservice.

## Datasets used in the reproduction

The original paper evaluates on NQ, HotpotQA, and MS MARCO. The code in this repository uses a synthetic corpus that mimics the same retrieval-poisoning pattern so it remains runnable without downloading and preprocessing massive public datasets.

| Dataset | Source | Size | Notes |
|---|---|---:|---|
| NQ | Natural Questions | Real public corpus | Open-domain QA with retrieval over article snippets |
| HotpotQA | HotpotQA | Real public corpus | Multi-hop QA requiring aggregated evidence |
| MS MARCO | Microsoft MARCO | Real public corpus | Large-scale passage retrieval and answer generation |

The synthetic equivalent keeps the same failure mode: a user query is paired with a few relevant passages and one maliciously inserted contradiction.

## Reproduction workflow

1. Install dependencies: `pip install -r requirements.txt`
2. Run the quick-start example: `python examples/basic_usage.py`
3. Execute the claim script: `./claims/claim1_poisonedrag/run.sh`
4. Benchmark the service: `python -m ragdefender.cli benchmark --claim claim1_poisonedrag`
5. Review the generated JSON report in `artifacts/results/`

## Notes on the research gap

The original paper focuses on prevention quality. This repository extends the same idea with a service-level lens to measure latency, throughput, and memory overhead in a containerized RAG microservice. This is the gap the project addresses: the paper evaluates detection metrics, while the deployment view measures the cost of defense under load.
