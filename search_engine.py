"""Semantic search over Esnad's ArabiCCR commercial judgments."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from arabiccr_artifacts import load_arabiccr_artifacts, load_dispute_types
from dispute_classifier import DISPUTE_LABELS
from outcome_classifier import classify_outcome


class LegalSearchEngine:
    """Search ArabiCCR chunks and return unique, complete judgments."""

    def __init__(self, project_dir: str | Path | None = None) -> None:
        root = Path(project_dir) if project_dir else Path(__file__).resolve().parent
        (
            self.index,
            self.metadata,
            self.chunk_to_doc,
            self.config,
        ) = load_arabiccr_artifacts(root / "artifacts" / "arabiccr")
        self.dispute_types = load_dispute_types(
            root / "artifacts" / "arabiccr", len(self.metadata)
        )

        self.model = SentenceTransformer(self.config["model_name"])
        self.model.max_seq_length = self.config["max_sequence_length"]
        if self.model.get_embedding_dimension() != self.config["embedding_dimension"]:
            raise ValueError(
                "Embedding model dimension does not match the ArabiCCR index."
            )

    @staticmethod
    def _value(row: pd.Series, key: str):
        value = row.get(key)
        if value is None:
            return None
        if isinstance(value, (float, np.floating)) and np.isnan(value):
            return None
        return value

    @staticmethod
    def _saved_outcome_category(value: object) -> str | None:
        """Map the audited ArabiCCR outcome to the UI's broad categories."""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        text = str(value)
        if not text or text == "غير محدد":
            return None
        if "صلح" in text:
            return "settlement"
        if "عدم الاختصاص" in text:
            return "no_jurisdiction"
        if "عدم قبول" in text or "عدم جواز نظر" in text:
            return "inadmissible"
        if "إلزام" in text or "ثبوت حق" in text:
            return "accepted"
        if "رفض" in text:
            return "rejected"
        return "other"

    def _build_hit(self, row: pd.Series, doc_id: int, score: float) -> dict:
        judgment_number = self._value(row, "judgment_number")
        details_url = self._value(row, "details_url")
        verdict = self._value(row, "RULING")
        saved_outcome = self._value(row, "outcome_v3")
        outcome_category = self._saved_outcome_category(saved_outcome)
        if outcome_category is None:
            outcome_category = classify_outcome(verdict)

        title = "حكم تجاري"
        if judgment_number is not None:
            title = f"حكم تجاري رقم {judgment_number}"

        return {
            "source": "ARABICCR",
            "case_id": details_url or f"arabiccr-{doc_id}",
            "judgment_number": judgment_number,
            "case_number": self._value(row, "case_number"),
            "judgment_date": self._value(row, "judgment_date"),
            "city": self._value(row, "city"),
            "court": self._value(row, "court_name"),
            "title": title,
            "facts": self._value(row, "EVENTS"),
            "reasoning": self._value(row, "REASONING"),
            "verdict": verdict,
            "full_text": self._value(row, "case_text"),
            "applicable_laws": None,
            "summary": None,
            "source_url": details_url,
            "outcome_category": outcome_category,
            "outcome_raw": saved_outcome,
            "dispute_types": self.dispute_types[doc_id],
            "similarity_score": float(score),
        }

    def search(
        self, query: str, top_k: int = 5, dispute_type: str | None = None
    ) -> dict:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Enter a nonempty search query.")
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")
        if dispute_type is not None and dispute_type not in DISPUTE_LABELS:
            raise ValueError("Unknown dispute type.")

        query = query.strip()
        vector = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")

        # One judgment can have multiple chunks. Search broadly, then keep the
        # strongest chunk only once for each judgment.
        candidate_count = (
            self.index.ntotal
            if dispute_type is not None
            else min(self.index.ntotal, max(200, top_k * 40))
        )
        scores, chunk_positions = self.index.search(vector, candidate_count)

        results = []
        seen_doc_ids: set[int] = set()
        for score, chunk_position in zip(scores[0], chunk_positions[0]):
            if chunk_position < 0:
                continue
            doc_id = int(self.chunk_to_doc[int(chunk_position)])
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)
            if dispute_type is not None and dispute_type not in self.dispute_types[doc_id]:
                continue
            results.append(
                self._build_hit(self.metadata.iloc[doc_id], doc_id, float(score))
            )
            if len(results) == top_k:
                break

        for rank, hit in enumerate(results, 1):
            hit["rank"] = rank

        return {"query": query, "result_count": len(results), "results": results}


if __name__ == "__main__":
    engine = LegalSearchEngine()
    response = engine.search(
        "شركة وردت بضاعة والمشتري لم يسدد الثمن", top_k=5
    )
    for item in response["results"]:
        print(
            item["rank"], item["judgment_number"],
            item["similarity_score"], item["outcome_category"]
        )
