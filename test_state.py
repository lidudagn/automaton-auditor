# test_state.py

from src.state import Evidence, AgentState, JudicialOpinion
from typing import List, Dict, Any

# Test 1: Evidence Creation
print("🧪 Testing Evidence class...")
print("-" * 40)
try:
    # Create sample evidence with all required fields
    ev = Evidence(
        goal="Test Evidence", 
        found=True, 
        content="abc", 
        location="loc", 
        rationale="rationale", 
        confidence=0.9
    )
    print(f"✓ Evidence created successfully")
    print(f"  - Type check: {isinstance(ev, Evidence)} ✅")
    print(f"  - Goal: {ev.goal}")
    print(f"  - Found: {ev.found}")
    print(f"  - Confidence: {ev.confidence}")
    
    # Test evidence with default values (content is optional)
    ev_minimal = Evidence(
        goal="Minimal Test",
        found=False,
        content=None,  # Use None for optional field
        location="",
        rationale="",
        confidence=0.0
    )
    print(f"✓ Minimal evidence created successfully")
    print(f"  - Content: {ev_minimal.content}")
    
except Exception as e:
    print(f"❌ Error creating Evidence: {e}")
    print(f"  Exception type: {type(e).__name__}")
    print(f"  Details: {e}")

print("\n")

# Test 2: AgentState Creation
print("🧪 Testing AgentState dictionary...")
print("-" * 40)
try:
    # Create sample AgentState with proper typing
    state: AgentState = {
        "repo_url": "https://github.com/example/repo",
        "pdf_path": "test_report.pdf",
        "rubric_dimensions": [
            {
                "name": "Code Quality",
                "description": "Quality of code structure and organization",
                "max_score": 10
            }
        ],
        "evidences": {},  # Empty dict for evidences
        "opinions": [],   # Empty list for opinions
        "final_report": None
    }
    
    print(f"✓ AgentState created successfully")
    print(f"  - Repo URL: {state['repo_url']}")
    print(f"  - PDF Path: {state['pdf_path']}")
    print(f"  - Rubric dimensions: {len(state['rubric_dimensions'])}")
    print(f"  - Evidences type: {type(state['evidences']).__name__}")
    
except Exception as e:
    print(f"❌ Error creating AgentState: {e}")

print("\n")

# Test 3: Integration Test with Evidences Dict
print("🧪 Testing integration with evidences dictionary...")
print("-" * 40)
try:
    # Create evidence from different detectives
    ev1 = Evidence(
        goal="Find main function",
        found=True,
        content="def main(): pass",
        location="src/main.py",
        rationale="Found in main.py file",
        confidence=1.0
    )
    
    ev2 = Evidence(
        goal="Check error handling",
        found=False,
        content=None,
        location="",
        rationale="No error handling found",
        confidence=0.0
    )
    
    ev3 = Evidence(
        goal="Check documentation",
        found=True,
        content="# Module documentation",
        location="README.md",
        rationale="Found in README",
        confidence=0.8
    )
    
    # Add to state with the new evidences dictionary structure
    state_with_evidence: AgentState = {
        "repo_url": "https://github.com/example/repo",
        "pdf_path": "test_report.pdf",
        "rubric_dimensions": [],
        "evidences": {
            "repo_detective": [ev1, ev2],
            "doc_detective": [ev3]
        },
        "opinions": [],
        "final_report": None
    }
    
    print(f"✓ Evidence successfully added to state")
    print(f"  - Total detectives with evidence: {len(state_with_evidence['evidences'])}")
    print(f"  - Repo detective evidence: {len(state_with_evidence['evidences']['repo_detective'])} items")
    print(f"  - Doc detective evidence: {len(state_with_evidence['evidences']['doc_detective'])} items")
    
    # Display all evidence
    print(f"\n  Collected Evidence by detective:")
    for detective, evidence_list in state_with_evidence['evidences'].items():
        print(f"    {detective}: {len(evidence_list)} evidence items")
        for i, evidence in enumerate(evidence_list, 1):
            print(f"      {i}. {evidence.goal} - Found: {evidence.found}")
    
except Exception as e:
    print(f"❌ Error in integration test: {e}")

print("\n" + "="*40)
print("✅ All Phase 1 tests completed!")