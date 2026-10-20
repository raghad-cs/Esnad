"""ALARB semantic search component for Esnad."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import torch
from sentence_transformers import SentenceTransformer

from alarb_artifacts import load_alarb_artifacts


class AlarbSearchEngine:
    """Load the saved ALARB artifacts and search them with BGE-M3."""

    def __init__(self, artifact_dir: str | Path | None = None) -> None:
        project_dir = Path(__file__).resolve().parent
        self.artifact_dir = (
            Path(artifact_dir)
            if artifact_dir is not None
            else project_dir / "artifacts" / "alarb"
        )

        self.index, self.metadata, self.config = load_alarb_artifacts(
            self.artifact_dir
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(
            self.config["model_name"],
            device=self.device,
        )
        self.model.max_seq_length = self.config["max_sequence_length"]

        if self.device == "cuda":
            self.model.half()

        model_dimension = self.model.get_embedding_dimension()
        expected_dimension = self.config["embedding_dimension"]
        if model_dimension != expected_dimension:
            raise ValueError(
                "Model and index dimensions do not match: "
                f"model={model_dimension}, expected={expected_dimension}."
            )

    def search(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Return the most semantically similar ALARB judgments."""
        query = query.strip()
        if not query:
            raise ValueError("The query must not be empty.")
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        top_k = min(top_k, self.index.ntotal)

        embedding_start = time.perf_counter()
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        embedding_seconds = time.perf_counter() - embedding_start

        search_start = time.perf_counter()
        scores, positions = self.index.search(query_embedding, top_k)
        search_seconds = time.perf_counter() - search_start

        results: list[dict[str, Any]] = []
        for rank, (position, score) in enumerate(
            zip(positions[0], scores[0]),
            start=1,
        ):
            row = self.metadata.iloc[int(position)]
            results.append(
                {
                    "rank": rank,
                    "source": "ALARB",
                    "case_id": int(row["case_id"]),
                    "similarity_score": float(score),
                    "case_facts": row["case_facts"],
                    "court_reasoning": row["court_reasoning"],
                    "applicable_laws": row["applicable_laws"],
                    "verdict": row["verdict"],
                }
            )

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
            "timings": {
                "query_embedding_seconds": embedding_seconds,
                "faiss_search_seconds": search_seconds,
                "total_seconds": embedding_seconds + search_seconds,
            },
        }


if __name__ == "__main__":
    engine = AlarbSearchEngine()
    test_query = (
        "شركة وفرت عمالة لشركة أخرى، لكن الشركة الثانية "
        "لم تدفع المستحقات ثم اتفق الطرفان على الصلح وجدولة المبلغ."
    )
    search_response = engine.search(test_query, top_k=5)

    print("Query:", search_response["query"])
    print("Results:", search_response["result_count"])
    for result in search_response["results"]:
        print(
            result["rank"],
            result["case_id"],
            f'{result["similarity_score"]:.4f}',
            result["verdict"][:100],
        )
