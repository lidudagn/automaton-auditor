import pytest
from src.state import AgentState, JudicialOpinion, Evidence
from src.nodes.justice import ChiefJusticeNode

def test_extreme_high_outlier_removed():
    """
    Test scores `[1,1,5]` with missing evidence where the 5 is removed 
    resulting in a final score of `1`.
    """
    node = ChiefJusticeNode()
    
    # Setup mock state with missing evidence and a 5/5 outlier
    state = AgentState(
        repo_url="https://github.com/test",
        pdf_path="",
        evidences={}, # No evidence found
        opinions=[
            JudicialOpinion(judge="Prosecutor", criterion_id="test_criterion", score=1, argument="No evidence", cited_evidence_ids=[]),
            JudicialOpinion(judge="TechLead", criterion_id="test_criterion", score=1, argument="No evidence", cited_evidence_ids=[]),
            JudicialOpinion(judge="Defense", criterion_id="test_criterion", score=5, argument="I hallucinated", cited_evidence_ids=[]) # Extreme high outlier
        ]
    )
    
    result = node(state)
    report = result.get("final_report")
    
    assert report is not None
    assert len(report.criteria) == 1
    # Without evidence fact supremacy should trigger and force it to 1,
    # and the outlier Defense judge should also be pruned if we hit Step 3 directly.
    assert report.criteria[0].final_score == 1
    # Check that defense was actually overridden/fact supremacy took over
    assert "CRITICAL MISSING COMPONENT" in report.criteria[0].remediation

def test_extreme_low_outlier_removed():
    """
    Test scores `[5,5,1]` with strong evidence where the 1 is removed 
    resulting in a final score of `5`.
    """
    node = ChiefJusticeNode()
    
    # Setup mock state with strong evidence and a 1/5 outlier
    state = AgentState(
        repo_url="https://github.com/test",
        pdf_path="",
        evidences={
            "repo": [
                Evidence(goal="Verify test_criterion exists", found=True, location="test.py", rationale="test", confidence=0.9, content="test")
            ]
        },
        opinions=[
            JudicialOpinion(judge="Defense", criterion_id="test_criterion", score=5, argument="Good", cited_evidence_ids=[]),
            JudicialOpinion(judge="TechLead", criterion_id="test_criterion", score=5, argument="Good", cited_evidence_ids=[]),
            JudicialOpinion(judge="Prosecutor", criterion_id="test_criterion", score=1, argument="I disagree forever", cited_evidence_ids=[]) # Extreme low outlier
        ]
    )
    
    result = node(state)
    report = result.get("final_report")
    
    assert report is not None
    assert len(report.criteria) == 1
    # Variance is 4 (5-1), median is 5. Outlier is Prosecutor (1), deviation is 4.
    # Evidence is found, so low outlier (<=2) should be removed.
    # Remaining valid judges: Defense (5), TechLead (5). Rounded mean = 5.
    assert report.criteria[0].final_score == 5
    assert report.criteria[0].dissent_summary is not None
    assert "Variance > 2" in report.criteria[0].dissent_summary


def test_hallucination_citation_pruning():
    """
    Test simulating `[5, 5, 5]` but one judge cites an invalid registry ID.
    The judge must be pruned, final score recalculates, and reasoning trace logs the pruning.
    """
    node = ChiefJusticeNode()
    
    state = AgentState(
        repo_url="https://github.com/test",
        pdf_path="",
        evidences={
            "repo": [
                Evidence(goal="Verify architecture exists", found=True, location="", rationale="", confidence=1.0)
            ]
        },
        opinions=[
            JudicialOpinion(judge="Defense", criterion_id="architecture", score=5, argument="Solid", cited_evidence_ids=["valid_id_1"]),
            JudicialOpinion(judge="TechLead", criterion_id="architecture", score=5, argument="Great", cited_evidence_ids=["valid_id_1"]),
            JudicialOpinion(judge="Prosecutor", criterion_id="architecture", score=5, argument="Fake code exists", cited_evidence_ids=["made_up_id_99"])
        ]
    )
    
    # Pre-load registry with the valid evidence so fact supremacy passes
    from src.core.evidence_registry import EvidenceRecord
    state.registry.add(EvidenceRecord(
        id="valid_id_1", source="repo", exists=True, claim_reference="architecture"
    ))
    
    result = node(state)
    report = result.get("final_report")
    
    assert report is not None
    assert len(report.criteria) == 1
    
    crit = report.criteria[0]
    # Check reasoning trace logged the specific Prosecutor pruning
    trace_text = " ".join(crit.reasoning_trace)
    assert "Prosecutor pruned due to invalid citation" in trace_text or "hallucination" in trace_text.lower() or "invalid citation" in trace_text.lower()
    
    # Ensure they were pruned and remaining scores dictated the final average (which is still 5 here)
    assert crit.final_score == 5
