"""Load and validate Esnad's ArabiCCR search artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
import pandas as pd


REQUIRED_METADATA_COLUMNS = {
    "judgment_number", "judgment_date", "city", "details_url",
    "EVENTS", "REASONING", "RULING",
}


def load_arabiccr_artifacts(artifact_dir: str | Path):
    """Read and validate the ArabiCCR index and its supporting files."""
    artifact_dir = Path(artifact_dir)
    index_path = artifact_dir / "arabiccr_chunks.index"
    mapping_path = artifact_dir / "chunk_to_doc.npy"
    config_path = artifact_dir / "arabiccr_search_config.json"
    parquet_path = artifact_dir / "arabiccr_metadata.parquet"
    pickle_path = artifact_dir / "arabiccr_metadata.pkl"

    for path in (index_path, mapping_path, config_path):
        if not path.is_file():
            raise FileNotFoundError(f"Missing ArabiCCR artifact: {path}")

    if parquet_path.is_file():
        metadata = pd.read_parquet(parquet_path)
    elif pickle_path.is_file():
        # Compatibility with the first export. Parquet is preferred for deployment.
        metadata = pd.read_pickle(pickle_path)
    else:
        raise FileNotFoundError(
            "Missing ArabiCCR metadata: expected arabiccr_metadata.parquet "
            "or arabiccr_metadata.pkl"
        )

    index = faiss.read_index(str(index_path))
    chunk_to_doc = np.load(mapping_path, allow_pickle=False)
    config = json.loads(config_path.read_text(encoding="utf-8"))

    missing_columns = REQUIRED_METADATA_COLUMNS - set(metadata.columns)
    if missing_columns:
        raise ValueError(
            "ArabiCCR metadata is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    if chunk_to_doc.ndim != 1:
        raise ValueError("ArabiCCR chunk mapping must be one-dimensional.")
    if index.ntotal != len(chunk_to_doc):
        raise ValueError(
            "ArabiCCR index and mapping do not match: "
            f"index={index.ntotal}, mapping={len(chunk_to_doc)}."
        )
    if len(metadata) < 1:
        raise ValueError("ArabiCCR metadata is empty.")
    if chunk_to_doc.min() < 0 or chunk_to_doc.max() >= len(metadata):
        raise ValueError("ArabiCCR mapping points outside the metadata.")
    if len(np.unique(chunk_to_doc)) != len(metadata):
        raise ValueError("Every ArabiCCR judgment must have at least one chunk.")
    if index.d != config["embedding_dimension"]:
        raise ValueError("ArabiCCR index dimension does not match configuration.")
    if index.metric_type != faiss.METRIC_INNER_PRODUCT:
        raise ValueError("ArabiCCR requires an inner-product FAISS index.")
    if config.get("normalize_embeddings") is not True:
        raise ValueError("ArabiCCR requires normalized embeddings.")
    if config.get("number_of_chunks") != index.ntotal:
        raise ValueError("Configured chunk count does not match the index.")
    if config.get("number_of_judgments") != len(metadata):
        raise ValueError("Configured judgment count does not match metadata.")

    return index, metadata, chunk_to_doc, config


def load_dispute_types(artifact_dir: str | Path, expected_count: int) -> list[list[str]]:
    """Load the precomputed multi-label dispute classification."""
    path = Path(artifact_dir) / "dispute_types.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing ArabiCCR dispute labels: {path}")
    labels = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(labels, list) or len(labels) != expected_count:
        raise ValueError("ArabiCCR dispute labels do not match the metadata.")
    if any(not isinstance(row, list) for row in labels):
        raise ValueError("Every ArabiCCR dispute label entry must be a list.")
    return labels
