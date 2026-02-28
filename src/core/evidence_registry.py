from typing import Dict, Any, Literal, Optional, List
from pydantic import BaseModel, Field

class EvidenceRecord(BaseModel):
    """A canonical, immutable record of fact in the deterministic auditing system."""
    id: str = Field(description="Unique identifier for the evidence")
    source: Literal["repo", "pdf", "vision"] = Field(description="Where the factual claim originated")
    artifact_path: Optional[str] = Field(default=None, description="The file path or commit hash")
    claim_reference: Optional[str] = Field(default=None, description="The specific goal/claim this addresses")
    exists: bool = Field(description="Whether the claim is factually true/exists")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or snippets")


class EvidenceRegistry:
    """The unified, deterministic source of truth for all gathered facts."""
    
    def __init__(self):
        self._store: Dict[str, EvidenceRecord] = {}

    def add(self, record: EvidenceRecord) -> None:
        """Register a new immutable fact."""
        self._store[record.id] = record

    def get(self, evidence_id: str) -> EvidenceRecord:
        """Retrieve a specific factual record."""
        return self._store[evidence_id]
        
    def exists(self, evidence_id: str) -> bool:
        """Check if an evidence ID exists in the canonical registry."""
        return evidence_id in self._store

    def all(self) -> Dict[str, EvidenceRecord]:
        """Return the entire evidentiary store."""
        return self._store
        
    def filter_by_claim(self, claim_keyword: str) -> List[EvidenceRecord]:
        """Retrieve all records related to a specific claim keyword."""
        return [
            record for record in self._store.values() 
            if record.claim_reference and claim_keyword.lower() in record.claim_reference.lower()
        ]
