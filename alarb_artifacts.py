"""Load one complete ALARB artifact set, selected by its saved case count."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import pandas as pd


REQUIRED_METADATA_COLUMNS = {
    "case_id", "case_facts", "court_reasoning", "applicable_laws", "verdict",
}


def load_alarb_artifacts(artifact_dir: str | Path):
    """Read the configured release; never silently fall back to an older index."""
    artifact_dir = Path(artifact_dir)
    config_path = artifact_dir / "alarb_search_config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing ALARB configuration: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    case_count = config.get("number_of_cases")
    if type(case_count) is not int or case_count < 1:
        raise ValueError("ALARB number_of_cases must be a positive integer.")

    index_path = artifact_dir / f"alarb_judgments_{case_count}.index"
    metadata_path = artifact_dir / f"alarb_judgments_metadata_{case_count}.parquet"
    missing = [path.name for path in (index_path, metadata_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing ALARB artifact files: " + ", ".join(missing))

    index = faiss.read_index(str(index_path))
    metadata = pd.read_parquet(metadata_path)
    missing_columns = REQUIRED_METADATA_COLUMNS - set(metadata.columns)
    if missing_columns:
        raise ValueError(
            "ALARB metadata is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if index.ntotal != case_count or len(metadata) != case_count:
        raise ValueError(
            "ALARB case counts do not match: "
            f"configuration={case_count}, index={index.ntotal}, metadata={len(metadata)}."
        )
    if metadata["case_id"].isna().any() or not metadata["case_id"].is_unique:
        raise ValueError("ALARB case IDs must be nonempty and unique.")
    if index.d != config["embedding_dimension"]:
        raise ValueError("ALARB index dimension does not match its configuration.")
    if index.metric_type != faiss.METRIC_INNER_PRODUCT:
        raise ValueError("ALARB requires an inner-product index.")
    if config.get("normalize_embeddings") is not True:
        raise ValueError("ALARB requires normalized embeddings.")

    return index, metadata, config
