"""LangGraph state graph for Automaton Auditor - Interim Submission."""

from langgraph.graph import StateGraph, START, END

from src.state import AgentState
from src.nodes.detectives import (
    RepoInvestigatorNode,
    DocAnalystNode,
    VisionInspectorNode,
    EvidenceAggregatorNode
)


def create_detective_graph() -> StateGraph:
    """
    Create the detective graph with parallel execution.
    
    Graph structure:
    START
      ├── RepoInvestigator  (parallel)
      ├── DocAnalyst        (parallel)
      └── VisionInspector   (parallel)
           ↓
    EvidenceAggregator (waits for ALL detectives)
           ↓
    END
    """
    # Create graph builder with our state type
    builder = StateGraph(AgentState)
    
    # Add detective nodes
    builder.add_node("repo_investigator", RepoInvestigatorNode())
    builder.add_node("doc_analyst", DocAnalystNode())
    builder.add_node("vision_inspector", VisionInspectorNode())
    builder.add_node("evidence_aggregator", EvidenceAggregatorNode())
    
    # PARALLEL FAN-OUT: START to all detectives
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")
    
    # FAN-IN: All detectives feed into aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")
    
    # Connect aggregator to END
    builder.add_edge("evidence_aggregator", END)
    
    # Compile the graph WITHOUT checkpointer to avoid thread_id error
    graph = builder.compile()
    
    return graph


# For testing this file directly
if __name__ == "__main__":
    print("Testing graph compilation...")
    
    # Create graph
    graph = create_detective_graph()
    
    # Print graph structure
    print("\n✅ Graph compiled successfully!")
    print("\nGraph nodes:", list(graph.nodes.keys()))
    
    # Test with minimal state
    test_state = {
        "repo_url": "https://github.com/langchain-ai/langgraph",
        "pdf_path": "test_report.pdf",
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    
    print("\n🚀 Testing graph execution...")
    
    # Run graph (no config needed since we removed checkpointer)
    result = graph.invoke(test_state)
    
    print("\n✅ Graph executed successfully!")
    print(f"Evidence collected: {list(result['evidences'].keys())}")
    
    # Count total evidence
    total = sum(len(v) for v in result['evidences'].values())
    print(f"Total evidence items: {total}")