"""Test detective graph."""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph import create_detective_graph


def test_detectives():
    """Test that detective graph runs."""
    print("🔍 Testing detective graph...")
    
    # Create graph
    graph = create_detective_graph()
    print(f"✅ Graph created with nodes: {list(graph.nodes.keys())}")
    
    # Create a dummy PDF file if it doesn't exist
    pdf_path = Path(__file__).parent.parent / "test.pdf"
    if not pdf_path.exists():
        with open(pdf_path, 'w') as f:
            f.write("Test PDF content for Automaton Auditor\n")
            f.write("Keywords: Dialectical Synthesis, Fan-Out, parallel detectives\n")
    
    # Test state
    test_state = {
        "repo_url": "https://github.com/langchain-ai/langgraph",
        "pdf_path": str(pdf_path),
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    
    # Run graph
    try:
        result = graph.invoke(test_state)
        print("✅ Graph ran successfully!")
        
        # Show evidence collected
        evidences = result.get("evidences", {})
        print(f"\n📊 Evidence collected from: {list(evidences.keys())}")
        
        for detector, ev_list in evidences.items():
            print(f"\n  {detector.upper()}: {len(ev_list)} items")
            for ev in ev_list:
                status = "✅" if ev.found else "❌"
                print(f"    {status} {ev.goal}")
                
    except Exception as e:
        print(f"❌ Error running graph: {e}")
    
    return result


if __name__ == "__main__":
    test_detectives()