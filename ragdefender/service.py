from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .benchmark import run_service_benchmark
from .datasets import generate_synthetic_dataset
from .defense import RAGDefender

app = FastAPI(title="RAGDefender reproduction service")


def _query_backend(question: str, top_k: int = 3):
    dataset = generate_synthetic_dataset(seed=42, examples=4)
    example = next((item for item in dataset if item.query.lower() in question.lower() or question.lower() in item.query.lower()), dataset[0])
    defender = RAGDefender(top_k=top_k)
    defended = defender.defend(example.query, example.documents, top_k=top_k)
    return {
        "query": question,
        "documents": example.documents,
        "filtered": defended.kept_documents,
        "removed": defended.removed_documents,
        "scores": defended.scores,
    }


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ragdefender-repro"}


@app.post("/query")
def query_endpoint(payload: QueryRequest) -> dict:
    return _query_backend(payload.question, top_k=payload.top_k)


@app.get("/benchmark")
def benchmark_endpoint() -> dict:
    report = run_service_benchmark(claim_name="claim1_poisonedrag", seed=42, repetitions=10)
    return report.to_json()
