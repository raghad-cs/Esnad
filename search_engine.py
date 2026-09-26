"""Unified semantic search across Esnad's ALARB and MOJ judgment indexes."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


class LegalSearchEngine:
    """Encode a query once, search both indexes, and rank all hits together."""

    def __init__(self, project_dir: str | Path | None = None) -> None:
        root = Path(project_dir) if project_dir else Path(__file__).resolve().parent
        alarb_dir = root / "artifacts" / "alarb"
        moj_dir = root / "artifacts"

        self.sources = {
            "ALARB": self._load_source(
                alarb_dir / "alarb_judgments_200.index",
                alarb_dir / "alarb_judgments_metadata_200.parquet",
                alarb_dir / "alarb_search_config.json",
            ),
            "MOJ": self._load_source(
                moj_dir / "precedents.index",
                moj_dir / "precedents_metadata.parquet",
                moj_dir / "moj_search_config.json",
            ),
        }
        configs = [source[2] for source in self.sources.values()]
        model_names = {config["model_name"] for config in configs}
        dimensions = {config["embedding_dimension"] for config in configs}
        if len(model_names) != 1 or len(dimensions) != 1:
            raise ValueError("Both indexes must use the same embedding model and dimension.")
        if any(config.get("normalize_embeddings") is not True for config in configs):
            raise ValueError("Both indexes must contain normalized embeddings.")
        self.model = SentenceTransformer(model_names.pop())
        self.model.max_seq_length = 1024  # Match the ALARB index build settings.
        if self.model.get_embedding_dimension() != dimensions.pop():
            raise ValueError("Model embedding dimension does not match the indexes.")

    @staticmethod
    def _load_source(index_path: Path, metadata_path: Path, config_path: Path):
        for path in (index_path, metadata_path, config_path):
            if not path.is_file():
                raise FileNotFoundError(f"Missing search artifact: {path}")
        index = faiss.read_index(str(index_path))
        metadata = pd.read_parquet(metadata_path)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if index.ntotal != len(metadata) or index.d != config["embedding_dimension"]:
            raise ValueError(f"Index and metadata/config do not match: {index_path}")
        if index.metric_type != faiss.METRIC_INNER_PRODUCT:
            raise ValueError(f"Expected an inner-product index: {index_path}")
        return index, metadata, config

    @staticmethod
    def _value(row: pd.Series, key: str):
        value = row.get(key)
        if value is None or isinstance(value, float) and np.isnan(value):
            return None
        return value

    def search(self, query: str, top_k: int = 5) -> dict:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Enter a nonempty search query.")
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")
        query = query.strip()
        vector = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")
        results = []
        for source_name, (index, metadata, _) in self.sources.items():
            scores, positions = index.search(vector, min(top_k, index.ntotal))
            for score, position in zip(scores[0], positions[0]):
                if position < 0:
                    continue
                row = metadata.iloc[int(position)]
                if source_name == "ALARB":
                    hit = {
                        "case_id": self._value(row, "case_id"),
                        "title": None,
                        "facts": self._value(row, "case_facts"),
                        "reasoning": self._value(row, "court_reasoning"),
                        "applicable_laws": self._value(row, "applicable_laws"),
                        "verdict": self._value(row, "verdict"),
                        "source_url": "https://huggingface.co/datasets/THIQAH-RD/ALARB",
                    }
                else:
                    hit = {
                        "case_id": self._value(row, "case_id"),
                        "title": self._value(row, "title"),
                        "facts": self._value(row, "facts"),
                        "reasoning": self._value(row, "legal_reasoning"),
                        "applicable_laws": self._value(row, "applicable_laws"),
                        "verdict": self._value(row, "verdict"),
                        "summary": self._value(row, "summary"),
                        "court": self._value(row, "court"),
                        "source_url": self._value(row, "source_url"),
                    }
                results.append({
                    "source": source_name,
                    "similarity_score": float(score),
                    **hit,
                })
        results.sort(key=lambda hit: hit["similarity_score"], reverse=True)
        results = results[:top_k]
        for rank, hit in enumerate(results, 1):
            hit["rank"] = rank
        return {"query": query, "result_count": len(results), "results": results}


if __name__ == "__main__":
    engine = LegalSearchEngine()
    response = engine.search("شركة وردت بضاعة والمشتري لم يسدد الثمن", top_k=5)
    for item in response["results"]:
        print(item["rank"], item["source"], item["similarity_score"], item["title"])
