"""LangGraph state graph for Automaton Auditor - Phase 2 with Judges."""
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from langgraph.graph import StateGraph, START, END

from src.state import AgentState
from src.nodes.detectives import (
    RepoInvestigatorNode,
    DocAnalystNode,
    VisionInspectorNode,
    EvidenceAggregatorNode
)
from src.nodes.judges import (
    ProsecutorNode,
    DefenseNode,
    TechLeadNode,
    OpinionAggregatorNode
)


def create_full_graph() -> StateGraph:
    """
    Create complete graph with detectives + judges.
    
    Graph structure:
    START
      ├── RepoInvestigator
      ├── DocAnalyst
      └── VisionInspector  (ALL PARALLEL)
           ↓
    EvidenceAggregator
           ↓
      ├── Prosecutor
      ├── Defense
      └── TechLead        (ALL PARALLEL)
           ↓
    OpinionAggregator
           ↓
    END
    """
    builder = StateGraph(AgentState)
    
    # Add detective nodes
    builder.add_node("repo_investigator", RepoInvestigatorNode())
    builder.add_node("doc_analyst", DocAnalystNode())
    builder.add_node("vision_inspector", VisionInspectorNode())
    builder.add_node("evidence_aggregator", EvidenceAggregatorNode())
    
    # Add judge nodes
    builder.add_node("prosecutor", ProsecutorNode())
    builder.add_node("defense", DefenseNode())
    builder.add_node("tech_lead", TechLeadNode())
    builder.add_node("opinion_aggregator", OpinionAggregatorNode())
    
    # Detective parallel fan-out
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")
    
    # Fan-in to aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")
    
    # Evidence to judges (parallel fan-out)
    builder.add_edge("evidence_aggregator", "prosecutor")
    builder.add_edge("evidence_aggregator", "defense")
    builder.add_edge("evidence_aggregator", "tech_lead")
    
    # Judges to opinion aggregator (fan-in)
    builder.add_edge("prosecutor", "opinion_aggregator")
    builder.add_edge("defense", "opinion_aggregator")
    builder.add_edge("tech_lead", "opinion_aggregator")
    
    # Aggregator to END
    builder.add_edge("opinion_aggregator", END)
    
    graph = builder.compile()
    return graph


def create_detective_graph() -> StateGraph:
    """
    Create detective-only graph (for testing).
    
    Graph structure:
    START
      ├── RepoInvestigator  (parallel)
      ├── DocAnalyst        (parallel)
      └── VisionInspector   (parallel)
           ↓
    EvidenceAggregator
           ↓
    END
    """
    builder = StateGraph(AgentState)
    
    builder.add_node("repo_investigator", RepoInvestigatorNode())
    builder.add_node("doc_analyst", DocAnalystNode())
    builder.add_node("vision_inspector", VisionInspectorNode())
    builder.add_node("evidence_aggregator", EvidenceAggregatorNode())
    
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")
    
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")
    
    builder.add_edge("evidence_aggregator", END)
    
    graph = builder.compile()
    return graph


# For testing this file directly
if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING GRAPH.PHASE 2".center(60))
    print("="*60)
    
    # Test detective graph
    print("\n📊 Testing detective graph...")
    det_graph = create_detective_graph()
    print(f"✅ Detective graph compiled!")
    print(f"   Nodes: {list(det_graph.nodes.keys())}")
    
    # Test full graph
    print("\n⚖️  Testing full graph with judges...")
    full_graph = create_full_graph()
    print(f"✅ Full graph compiled!")
    print(f"   Nodes: {list(full_graph.nodes.keys())}")
    
    # Test with minimal state (Pydantic model)
    print("\n🚀 Testing execution with Pydantic state...")
    
    from src.state import AgentState
    
    test_state = AgentState(
        repo_url="https://github.com/langchain-ai/langgraph",
        pdf_path="test_report.pdf"
    )
    
    try:
        # Try detective graph first
        result = det_graph.invoke(test_state)
        print(f"\n✅ Detective graph executed successfully!")
        print(f"   Evidence collected: {list(result.evidences.keys())}")
        
        total_evidence = result.get_evidence_count()
        print(f"   Total evidence items: {total_evidence}")
        
        # Test full graph with judges
        print(f"\n⚖️  Testing full graph with judges...")
        
        # Create fresh state for judges test
        judge_state = AgentState(
            repo_url="https://github.com/langchain-ai/langgraph",
            pdf_path="test_report.pdf"
        )
        
        judge_result = full_graph.invoke(judge_state)
        print(f"\n✅ Full graph executed successfully!")
        print(f"   Evidence: {judge_result.get_evidence_count()} items")
        print(f"   Opinions: {len(judge_result.opinions)}")
        
    except Exception as e:
        print(f"\n❌ Execution error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
    
    print("\n" + "="*60)