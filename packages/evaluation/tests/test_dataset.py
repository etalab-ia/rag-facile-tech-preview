"""Tests for the rag-facile JSONL → Inspect AI dataset adapter."""

from __future__ import annotations

import json
from pathlib import Path

from rag_facile.evaluation._dataset import load_rag_dataset


def _write_jsonl(tmp_path: Path, samples: list[dict]) -> Path:
    """Write samples to a JSONL file and return the path."""
    path = tmp_path / "test.jsonl"
    lines = [json.dumps(s, ensure_ascii=False) for s in samples]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_load_basic_dataset(tmp_path: Path) -> None:
    """Load a minimal dataset with required fields."""
    path = _write_jsonl(
        tmp_path,
        [
            {
                "user_input": "What is RAG?",
                "reference": "Retrieval-Augmented Generation",
                "retrieved_contexts": ["RAG combines retrieval with generation."],
            }
        ],
    )
    ds = load_rag_dataset(path)
    assert len(ds) == 1
    assert ds[0].input == "What is RAG?"
    assert ds[0].target == "Retrieval-Augmented Generation"
    # retrieved_contexts from JSONL → both metadata keys
    assert ds[0].metadata["retrieved_contexts"] == [
        "RAG combines retrieval with generation."
    ]
    assert ds[0].metadata["relevant_contexts"] == [
        "RAG combines retrieval with generation."
    ]


def test_load_dataset_with_chunk_ids(tmp_path: Path) -> None:
    """Chunk IDs are loaded into metadata."""
    path = _write_jsonl(
        tmp_path,
        [
            {
                "user_input": "Q1",
                "reference": "A1",
                "retrieved_contexts": ["ctx"],
                "relevant_chunk_ids": ["c1", "c2"],
                "retrieved_chunk_ids": ["c1", "c3"],
            }
        ],
    )
    ds = load_rag_dataset(path)
    assert ds[0].metadata["relevant_chunk_ids"] == ["c1", "c2"]
    assert ds[0].metadata["retrieved_chunk_ids"] == ["c1", "c3"]


def test_load_dataset_with_metadata(tmp_path: Path) -> None:
    """Extra _metadata fields are extracted."""
    path = _write_jsonl(
        tmp_path,
        [
            {
                "user_input": "Q",
                "reference": "A",
                "retrieved_contexts": [],
                "_metadata": {
                    "source_file": "doc.pdf",
                    "retrieval_scores": [0.9, 0.8],
                    "collection_ids": [785],
                },
            }
        ],
    )
    ds = load_rag_dataset(path)
    assert ds[0].metadata["source_file"] == "doc.pdf"
    assert ds[0].metadata["retrieval_scores"] == [0.9, 0.8]
    assert ds[0].metadata["collection_ids"] == [785]


def test_load_empty_lines_skipped(tmp_path: Path) -> None:
    """Blank lines in the JSONL are ignored."""
    path = tmp_path / "test.jsonl"
    path.write_text(
        json.dumps({"user_input": "Q", "reference": "A", "retrieved_contexts": []})
        + "\n\n\n",
        encoding="utf-8",
    )
    ds = load_rag_dataset(path)
    assert len(ds) == 1


def test_dataset_name_from_filename(tmp_path: Path) -> None:
    """Dataset name is derived from the file stem."""
    path = _write_jsonl(
        tmp_path,
        [{"user_input": "Q", "reference": "A", "retrieved_contexts": []}],
    )
    ds = load_rag_dataset(path)
    assert ds.name == "test"
