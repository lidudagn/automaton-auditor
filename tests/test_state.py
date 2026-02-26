"""Test state management and reducers."""

import pytest
from src.state import Evidence, JudicialOpinion, AgentState
import operator

def test_evidence_model():
    """Test Evidence model creation and validation."""
    evidence = Evidence(
        goal="Test Goal",
        found=True,
        content="test content",
        location="test.py",
        rationale="test rationale",
        confidence=0.95
    )
    
    assert evidence.goal == "Test Goal"
    assert evidence.found == True
    assert 0.0 <= evidence.confidence <= 1.0
    print("✅ Evidence model works")

def test_reducer_merge_dicts():
    """Test that dict reducer merges correctly."""
    from src.state import merge_dicts
    
    dict1 = {"repo": ["evidence1"]}
    dict2 = {"doc": ["evidence2"]}
    dict3 = {"repo": ["evidence3"]}
    
    # Merge should combine without overwriting
    result = merge_dicts(dict1, dict2)
    result = merge_dicts(result, dict3)
    
    assert "repo" in result
    assert "doc" in result
    assert len(result["repo"]) == 2  # Both evidence1 and evidence3
    assert len(result["doc"]) == 1
    print("✅ Reducer correctly merges dictionaries")

def test_reducer_add_lists():
    """Test that list reducer concatenates."""
    list1 = [JudicialOpinion(judge="Prosecutor", criterion_id="test", score=5, argument="good", cited_evidence=[])]
    list2 = [JudicialOpinion(judge="Defense", criterion_id="test", score=3, argument="ok", cited_evidence=[])]
    
    # operator.add should concatenate
    result = operator.add(list1, list2)
    
    assert len(result) == 2
    assert result[0].judge == "Prosecutor"
    assert result[1].judge == "Defense"
    print("✅ List reducer correctly concatenates")

if __name__ == "__main__":
    test_evidence_model()
    test_reducer_merge_dicts()
    test_reducer_add_lists()