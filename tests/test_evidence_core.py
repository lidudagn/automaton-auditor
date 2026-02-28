import pytest
from src.core.evidence_registry import EvidenceRecord, EvidenceRegistry
from src.core.evidence_graph import EvidenceGraph

def test_evidence_registry():
    registry = EvidenceRegistry()
    record = EvidenceRecord(
        id="test_ev_1",
        source="repo",
        artifact_path="src/main.py",
        claim_reference="Verify routing exists",
        exists=True
    )
    
    registry.add(record)
    assert registry.exists("test_ev_1") is True
    assert registry.exists("non_existent") is False
    
    retrieved = registry.get("test_ev_1")
    assert retrieved.id == "test_ev_1"
    assert retrieved.source == "repo"
    
    all_records = registry.all()
    assert len(all_records) == 1
    
    filtered = registry.filter_by_claim("routing")
    assert len(filtered) == 1
    assert len(registry.filter_by_claim("database")) == 0

def test_evidence_graph():
    graph = EvidenceGraph()
    
    graph.link("goal_1", "ev_1")
    graph.link("goal_1", "ev_2")
    graph.link("goal_2", "ev_3")
    
    assert "ev_1" in graph.get_links("goal_1")
    assert "ev_2" in graph.get_links("goal_1")
    assert len(graph.get_links("goal_1")) == 2
    
    assert len(graph.get_links("goal_2")) == 1
    assert len(graph.get_links("non_existent")) == 0
    
    graph.clear()
    assert len(graph.get_links("goal_1")) == 0
