"""Schema definitions for Data Foundry output.

Defines the Ragas-compatible output format for generated Q/A samples.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SampleMetadata:
    """Metadata for a generated sample."""

    source_file: str = ""
    quality_score: float = 0.0
    topic_summary: str = ""
    # Extensible for additional metadata
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding empty extra."""
        result = {
            "source_file": self.source_file,
            "quality_score": self.quality_score,
            "topic_summary": self.topic_summary,
        }
        if self.extra:
            result.update(self.extra)
        return result


@dataclass
class GeneratedSample:
    """A generated Q/A sample in Ragas-compatible format.

    Attributes:
        user_input: The question in French
        retrieved_contexts: List of context passages
        reference: The ground truth answer in French
        relevant_chunk_ids: Ground-truth chunk IDs that should be retrieved
        retrieved_chunk_ids: Chunk IDs that were actually retrieved
        metadata: Additional metadata about the sample
    """

    user_input: str
    retrieved_contexts: list[str]
    reference: str
    relevant_chunk_ids: list[str] = field(default_factory=list)
    retrieved_chunk_ids: list[str] = field(default_factory=list)
    metadata: SampleMetadata = field(default_factory=SampleMetadata)

    def to_dict(self) -> dict[str, Any]:
        """Convert to Ragas-compatible dictionary format."""
        result: dict[str, Any] = {
            "user_input": self.user_input,
            "retrieved_contexts": self.retrieved_contexts,
            "reference": self.reference,
            "_metadata": self.metadata.to_dict(),
        }
        if self.relevant_chunk_ids:
            result["relevant_chunk_ids"] = self.relevant_chunk_ids
        if self.retrieved_chunk_ids:
            result["retrieved_chunk_ids"] = self.retrieved_chunk_ids
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedSample":
        """Create from dictionary (e.g., parsed JSON)."""
        metadata_dict = data.get("_metadata", {})
        metadata = SampleMetadata(
            source_file=metadata_dict.get("source_file", ""),
            quality_score=metadata_dict.get("quality_score", 0.0),
            topic_summary=metadata_dict.get("topic_summary", ""),
        )
        return cls(
            user_input=data.get("user_input", ""),
            retrieved_contexts=data.get("retrieved_contexts", []),
            reference=data.get("reference", ""),
            relevant_chunk_ids=data.get("relevant_chunk_ids", []),
            retrieved_chunk_ids=data.get("retrieved_chunk_ids", []),
            metadata=metadata,
        )
