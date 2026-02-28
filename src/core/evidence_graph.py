from collections import defaultdict
from typing import Dict, Set

class EvidenceGraph:
    """Lightweight deterministic adjacency mapping for audit observability."""
    
    def __init__(self):
        # Maps a parent ID (e.g., a PDF Claim) to a set of child IDs (e.g., Repo Artifacts)
        self.edges: Dict[str, Set[str]] = defaultdict(set)

    def link(self, parent_id: str, child_id: str) -> None:
        """Create a directional relationship between two pieces of evidence or citations."""
        self.edges[parent_id].add(child_id)

    def get_links(self, evidence_id: str) -> Set[str]:
        """Retrieve all downstream relationships extending from a specific ID."""
        return self.edges.get(evidence_id, set())

    def clear(self) -> None:
        """Reset the graph."""
        self.edges.clear()
