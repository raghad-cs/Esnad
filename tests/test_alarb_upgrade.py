"""Exercise release switching without downloading an embedding model."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd


class FakeModel:
    def __init__(self, *args, **kwargs):
        self.max_seq_length = None

    def get_embedding_dimension(self):
        return 1024

    def encode(self, texts, **kwargs):
        return np.ones((len(texts), 1024), dtype="float32") / 32


faiss_stub = types.ModuleType("faiss")
faiss_stub.METRIC_INNER_PRODUCT = 0
faiss_stub.read_index = Mock()
torch_stub = types.ModuleType("torch")
torch_stub.cuda = types.SimpleNamespace(is_available=lambda: False)
model_stub = types.ModuleType("sentence_transformers")
model_stub.SentenceTransformer = FakeModel
sys.modules.update({
    "faiss": faiss_stub,
    "torch": torch_stub,
    "sentence_transformers": model_stub,
})

from alarb_artifacts import load_alarb_artifacts
from alarb_search_engine import AlarbSearchEngine
from search_engine import LegalSearchEngine


def metadata(count):
    return pd.DataFrame({
        "case_id": range(1, count + 1),
        "case_facts": ["وقائع"] * count,
        "court_reasoning": ["تسبيب"] * count,
        "applicable_laws": [""] * count,
        "verdict": ["إثبات الصلح"] * count,
    })


def fake_index(count):
    return types.SimpleNamespace(
        ntotal=count, d=1024, metric_type=0,
        search=lambda vector, k: (
            np.array([[0.9] * k], dtype="float32"),
            np.array([list(range(count - 1, count - k - 1, -1))]),
        ),
    )


def write_release(directory, count):
    directory.mkdir(parents=True, exist_ok=True)
    config = {
        "number_of_cases": count, "embedding_dimension": 1024,
        "model_name": "BAAI/bge-m3", "max_sequence_length": 1024,
        "normalize_embeddings": True,
    }
    (directory / "alarb_search_config.json").write_text(json.dumps(config))
    (directory / f"alarb_judgments_{count}.index").write_bytes(b"index fixture")
    (directory / f"alarb_judgments_metadata_{count}.parquet").write_bytes(b"metadata fixture")
    return config


class AlarbUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def load(self, directory, count, index=None, rows=None):
        with patch.object(faiss_stub, "read_index", return_value=index or fake_index(count)), \
             patch.object(pd, "read_parquet", return_value=rows if rows is not None else metadata(count)):
            return load_alarb_artifacts(directory)

    def test_selects_200_and_6000_from_configuration(self):
        for count in (200, 6000):
            with self.subTest(count=count):
                directory = self.root / str(count)
                write_release(directory, count)
                with patch.object(faiss_stub, "read_index", return_value=fake_index(count)) as read_index, \
                     patch.object(pd, "read_parquet", return_value=metadata(count)) as read_parquet:
                    index, rows, config = load_alarb_artifacts(directory)
                self.assertEqual(index.ntotal, count)
                self.assertEqual(len(rows), count)
                self.assertEqual(config["number_of_cases"], count)
                self.assertTrue(read_index.call_args.args[0].endswith(f"_{count}.index"))
                self.assertTrue(str(read_parquet.call_args.args[0]).endswith(f"_{count}.parquet"))

    def test_missing_new_release_never_falls_back_to_old_files(self):
        write_release(self.root, 200)
        config_path = self.root / "alarb_search_config.json"
        config = json.loads(config_path.read_text())
        config["number_of_cases"] = 6000
        config_path.write_text(json.dumps(config))
        with self.assertRaisesRegex(FileNotFoundError, "6000"):
            self.load(self.root, 6000)

    def test_rejects_invalid_configured_count(self):
        config = write_release(self.root, 200)
        for value in (0, -1, True, "6000", None):
            with self.subTest(value=value):
                config["number_of_cases"] = value
                (self.root / "alarb_search_config.json").write_text(json.dumps(config))
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    self.load(self.root, 200)

    def test_rejects_mixed_index_metadata_and_config_counts(self):
        write_release(self.root, 6000)
        for index_count, row_count in ((200, 6000), (6000, 200), (200, 200)):
            with self.subTest(index_count=index_count, row_count=row_count):
                with self.assertRaisesRegex(ValueError, "counts do not match"):
                    self.load(self.root, 6000, fake_index(index_count), metadata(row_count))

    def test_rejects_duplicate_ids_missing_columns_and_wrong_dimension(self):
        write_release(self.root, 200)
        rows = metadata(200)
        rows.loc[1, "case_id"] = 1
        with self.assertRaisesRegex(ValueError, "unique"):
            self.load(self.root, 200, rows=rows)
        with self.assertRaisesRegex(ValueError, "required columns"):
            self.load(self.root, 200, rows=metadata(200).drop(columns="verdict"))
        index = fake_index(200)
        index.d = 768
        with self.assertRaisesRegex(ValueError, "dimension"):
            self.load(self.root, 200, index=index)

    def test_both_engines_search_new_cases_and_keep_moj_paths(self):
        alarb_dir = self.root / "artifacts" / "alarb"
        write_release(alarb_dir, 6000)
        moj_dir = self.root / "artifacts"
        (moj_dir / "precedents.index").touch()
        (moj_dir / "precedents_metadata.parquet").touch()
        moj_config = {
            "model_name": "BAAI/bge-m3", "embedding_dimension": 1024,
            "normalize_embeddings": True,
        }
        (moj_dir / "moj_search_config.json").write_text(json.dumps(moj_config))
        with patch.object(faiss_stub, "read_index", side_effect=lambda path: fake_index(1 if Path(path).name == "precedents.index" else 6000)) as read_index, \
             patch.object(pd, "read_parquet", side_effect=lambda path: metadata(1 if Path(path).name == "precedents_metadata.parquet" else 6000)):
            standalone = AlarbSearchEngine(alarb_dir)
            unified = LegalSearchEngine(self.root)
            self.assertEqual(standalone.search("اختبار", top_k=1)["results"][0]["case_id"], 6000)
            hits = unified.search("اختبار", top_k=2)["results"]
            self.assertIn(6000, [hit["case_id"] for hit in hits])
            self.assertEqual(unified.sources["MOJ"][0].ntotal, 1)
            self.assertIn(str(moj_dir / "precedents.index"), [call.args[0] for call in read_index.call_args_list])

    def test_colab_uploader_commits_only_three_files_and_pushes_without_force(self):
        source = self.root / "drive"
        write_release(source, 6000)
        remote = self.root / "remote.git"
        seed = self.root / "seed"

        def run(*args, cwd=None):
            return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

        run("init", "--bare", str(remote))
        seed.mkdir()
        run("init", "-b", "upscaling", cwd=seed)
        run("config", "user.name", "Test", cwd=seed)
        run("config", "user.email", "test@example.invalid", cwd=seed)
        write_release(seed / "artifacts" / "alarb", 200)
        moj_path = seed / "artifacts" / "precedents.index"
        moj_path.write_bytes(b"MOJ must remain unchanged")
        run("add", ".", cwd=seed)
        run("commit", "-m", "Fixture release", cwd=seed)
        run("remote", "add", "origin", str(remote), cwd=seed)
        run("push", "origin", "upscaling", cwd=seed)
        before = run("rev-parse", "HEAD", cwd=seed)

        notebook = json.loads((Path(__file__).resolve().parents[1] / "notebooks" / "upload_alarb_6000.ipynb").read_text())
        code = "".join(notebook["cells"][-1]["source"])
        namespace = {}
        exec(code.rsplit("publish_alarb()", 1)[0], namespace)
        namespace.update({"SOURCE_DIR": source, "REPOSITORY_URL": str(remote)})
        namespace["getpass"] = lambda prompt: "dummy-test-credential"
        with patch("builtins.input", side_effect=["test", "test@example.invalid"]), \
             patch.object(faiss_stub, "read_index", return_value=fake_index(6000)), \
             patch.object(pd, "read_parquet", return_value=metadata(6000)), \
             contextlib.redirect_stdout(io.StringIO()):
            namespace["publish_alarb"]()

        changed = run("--git-dir", str(remote), "diff", "--name-only", before, "upscaling").splitlines()
        self.assertEqual(set(changed), {
            "artifacts/alarb/alarb_judgments_6000.index",
            "artifacts/alarb/alarb_judgments_metadata_6000.parquet",
            "artifacts/alarb/alarb_search_config.json",
        })
        self.assertEqual(run("--git-dir", str(remote), "show", "upscaling:artifacts/precedents.index"), "MOJ must remain unchanged")
        self.assertEqual(json.loads(run("--git-dir", str(remote), "show", "upscaling:artifacts/alarb/alarb_search_config.json"))["number_of_cases"], 6000)
        self.assertNotIn("--force", code)
        self.assertIn('"credential.helper="', code)


if __name__ == "__main__":
    unittest.main()
