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
            JudicialOpinion(judge="Prosecutor", criterion_id="test_criterion", score=1, argument="No evidence", cited_evidence=[]),
            JudicialOpinion(judge="TechLead", criterion_id="test_criterion", score=1, argument="No evidence", cited_evidence=[]),
            JudicialOpinion(judge="Defense", criterion_id="test_criterion", score=5, argument="I hallucinated", cited_evidence=[]) # Extreme high outlier
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
            JudicialOpinion(judge="Defense", criterion_id="test_criterion", score=5, argument="Good", cited_evidence=[]),
            JudicialOpinion(judge="TechLead", criterion_id="test_criterion", score=5, argument="Good", cited_evidence=[]),
            JudicialOpinion(judge="Prosecutor", criterion_id="test_criterion", score=1, argument="I disagree forever", cited_evidence=[]) # Extreme low outlier
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
