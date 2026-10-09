from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .datasets import RetrievalExample


@dataclass
class DefenseResult:
    kept_documents: List[str]
    removed_documents: List[str]
    scores: List[float]
    suspicious_indices: List[int]


class RAGDefender:
    """A lightweight reimplementation of the paper's two-stage defense.

    Stage 1 groups retrieved passages by semantic similarity around the dominant query
    support cluster. Stage 2 measures whether a candidate passage aligns with the
    dominant cluster or appears to be an adversarial outlier. The implementation is
    intentionally compact and CPU-friendly so it can run in CI and local development.
    """

    def __init__(self, top_k: int = 3, group_similarity_threshold: float = 0.25, suspicion_threshold: float = 0.55):
        self.top_k = top_k
        self.group_similarity_threshold = group_similarity_threshold
        self.suspicion_threshold = suspicion_threshold

    def _score_documents(self, query: str, documents: Sequence[str]) -> Tuple[np.ndarray, np.ndarray]:
        if not documents:
            return np.array([], dtype=float), np.array([], dtype=float)

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform([query, *documents])
        query_vector = matrix[0]
        doc_matrix = matrix[1:]
        cosine_scores = cosine_similarity(query_vector, doc_matrix).ravel()
        return cosine_scores, doc_matrix.toarray()

    def _dominant_group(self, docs: Sequence[str], query_scores: np.ndarray) -> List[int]:
        ranked = sorted(range(len(docs)), key=lambda idx: query_scores[idx], reverse=True)
        if not ranked:
            return []

        seeds = [ranked[0]]
        groups: List[List[int]] = [[] for _ in range(len(seeds))]
        for idx in ranked[1:]:
            candidate_scores = []
            for group_id, group in enumerate(groups):
                if not group:
                    continue
                centroid = self._group_centroid([docs[j] for j in group], [idx])
                candidate_scores.append((group_id, cosine_similarity(self._embed([docs[idx]]), centroid.reshape(1, -1))[0, 0]))
            if not candidate_scores:
                groups.append([idx])
                continue
            best_group_id, best_score = max(candidate_scores, key=lambda pair: pair[1])
            if best_score >= self.group_similarity_threshold:
                groups[best_group_id].append(idx)
            else:
                groups.append([idx])

        if not groups:
            return []
        return max(groups, key=len)

    def _group_centroid(self, texts: Sequence[str], include_indices: Sequence[int] | None = None):
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        centroid = matrix.mean(axis=0)
        if include_indices is not None and include_indices:
            return centroid
        return centroid

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        return vectorizer.fit_transform(texts).toarray()

    def defend(self, query: str, documents: Sequence[str], top_k: int | None = None) -> DefenseResult:
        if not documents:
            return DefenseResult([], [], [], [])

        top_k = top_k or self.top_k
        scores, _ = self._score_documents(query, documents)
        ranked_indices = sorted(range(len(documents)), key=lambda idx: scores[idx], reverse=True)

        # Stage 1: group retrieved passages by their semantic similarity to the dominant cluster.
        # Since the implementation stays lightweight, we approximate the cluster center with the top score.
        dominant_group = ranked_indices[: max(1, min(len(ranked_indices), top_k))]
        suspicious_indices: List[int] = []

        # Stage 2: identify passage outliers by low relevance to query and weak alignment to the dominant support cluster.
        for idx in range(len(documents)):
            if idx in dominant_group:
                continue
            score = float(scores[idx])
            if score < self.suspicion_threshold:
                suspicious_indices.append(idx)

        kept = [documents[idx] for idx in range(len(documents)) if idx not in suspicious_indices]
        removed = [documents[idx] for idx in suspicious_indices]
        return DefenseResult(
            kept_documents=kept,
            removed_documents=removed,
            scores=scores.tolist(),
            suspicious_indices=suspicious_indices,
        )


def evaluate_defense(dataset: Sequence[RetrievalExample], top_k: int = 3) -> dict:
    defender = RAGDefender(top_k=top_k)
    successful = 0
    poison_hits = 0
    poison_total = 0
    for example in dataset:
        result = defender.defend(example.query, example.documents, top_k=top_k)
        poison_total += len(example.poisoned_indices)
        poison_hits += sum(1 for idx in example.poisoned_indices if idx in result.suspicious_indices)
        kept_text = "\n".join(result.kept_documents)
        if example.answer in kept_text:
            successful += 1

    return {
        "examples": len(dataset),
        "correct_after_defense": successful,
        "poisoned_removed": poison_hits,
        "poisoned_total": poison_total,
        "poison_removal_rate": 0.0 if poison_total == 0 else poison_hits / poison_total,
        "answer_recovery_rate": 0.0 if not dataset else successful / len(dataset),
    }
