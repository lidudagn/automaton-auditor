import pytest
from datetime import datetime
from src.state import AgentState, Evidence, JudicialOpinion
from src.nodes.justice import ChiefJusticeNode

def test_cross_evidence_contradiction():
    # Setup mock state with contradictory evidence
    state = AgentState(
        repo_url="https://mockrepo.com",
        pdf_path="mock.pdf",
        rubric_dimensions=[
            {"id": "architecture_pattern", "name": "Architecture Pattern"}
        ]
    )
    
    # Add DOC evidence claiming architecture exists (CONFIDENCE > 0.6)
    state.add_evidence("doc", Evidence(
        goal="architecture_pattern",
        found=True,
        location="mock.pdf",
        rationale="PDF claims graph architecture exists",
        confidence=0.9
    ))
    
    # Add REPO evidence proving architecture does NOT exist (CONFIDENCE > 0.6)
    state.add_evidence("repo", Evidence(
        goal="architecture_pattern",
        found=False,
        location="repository",
        rationale="Could not find graph architecture files",
        confidence=0.8
    ))
    
    # Add Judge opinions (giving a high score of 5)
    opinions = [
        JudicialOpinion(judge="Prosecutor", criterion_id="architecture_pattern", score=5, argument="Looks good"),
        JudicialOpinion(judge="Defense", criterion_id="architecture_pattern", score=5, argument="Perfect"),
        JudicialOpinion(judge="TechLead", criterion_id="architecture_pattern", score=5, argument="LGTM")
    ]
    state.opinions.extend(opinions)
    
    # Execute Chief Justice
    node = ChiefJusticeNode()
    result = node(state)
    
    final_report = result["final_report"]
    
    # Verify contradiction detected
    assert len(final_report.detected_contradictions) == 1
    assert "Documentation claims structural existence" in final_report.detected_contradictions[0]
    
    # Verify score was mathematically penalized (Base 5 - 2 = 3)
    criterion_result = final_report.criteria[0]
    assert criterion_result.contradiction_flag is True
    assert criterion_result.final_score == 3
    assert criterion_result.remediation.startswith("RESOLVE CONTRADICTION")

def test_no_contradiction_happy_path():
    # Setup mock state with corresponding evidence
    state = AgentState(
        repo_url="https://mockrepo.com",
        pdf_path="mock.pdf",
        rubric_dimensions=[
            {"id": "architecture_pattern", "name": "Architecture Pattern"}
        ]
    )
    
    # Add DOC evidence
    state.add_evidence("doc", Evidence(
        goal="architecture_pattern",
        found=True,
        location="mock.pdf",
        rationale="PDF claims graph architecture exists",
        confidence=0.9
    ))
    
    # Add REPO evidence confirming it
    state.add_evidence("repo", Evidence(
        goal="architecture_pattern",
        found=True,
        location="repository",
        rationale="Found graph architecture files",
        confidence=0.8
    ))
    
    # Add Judge opinions
    opinions = [
        JudicialOpinion(judge="Prosecutor", criterion_id="architecture_pattern", score=5, argument="Looks good"),
        JudicialOpinion(judge="Defense", criterion_id="architecture_pattern", score=5, argument="Perfect"),
        JudicialOpinion(judge="TechLead", criterion_id="architecture_pattern", score=5, argument="LGTM")
    ]
    state.opinions.extend(opinions)
    
    # Execute
    node = ChiefJusticeNode()
    result = node(state)
    
    final_report = result["final_report"]
    
    assert len(final_report.detected_contradictions) == 0
    assert final_report.criteria[0].contradiction_flag is False
    assert final_report.criteria[0].final_score == 5
