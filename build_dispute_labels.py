"""Build the lightweight dispute-label artifact from ArabiCCR metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dispute_classifier import classify_dispute


ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts" / "arabiccr"


def main() -> None:
    parquet_path = ARTIFACT_DIR / "arabiccr_metadata.parquet"
    pickle_path = ARTIFACT_DIR / "arabiccr_metadata.pkl"
    metadata = (
        pd.read_parquet(parquet_path)
        if parquet_path.is_file()
        else pd.read_pickle(pickle_path)
    )
    labels = [
        classify_dispute(row.EVENTS, row.REASONING)
        for row in metadata.itertuples(index=False)
    ]
    output_path = ARTIFACT_DIR / "dispute_types.json"
    output_path.write_text(
        json.dumps(labels, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Saved {len(labels)} judgments to {output_path}")


if __name__ == "__main__":
    main()
