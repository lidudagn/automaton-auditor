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
    TechLeadNode
)
from src.nodes.justice import ChiefJusticeNode
import logging
logger = logging.getLogger(__name__)


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
    ChiefJustice
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
    builder.add_node("chief_justice", ChiefJusticeNode())
    
    # Detective parallel fan-out
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")
    
    # Fan-in to aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")
    
    def should_judge(state: AgentState):
        """Route to judges only if evidence was collected."""
        if state.get_evidence_count() > 0:
            return ["prosecutor", "defense", "tech_lead"]
        return [END]

    builder.add_conditional_edges("evidence_aggregator", should_judge)
    
    # Judges to chief justice (fan-in)
    builder.add_edge("prosecutor", "chief_justice")
    builder.add_edge("defense", "chief_justice")
    builder.add_edge("tech_lead", "chief_justice")
    
    # Chief Justice to END
    builder.add_edge("chief_justice", END)
    
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
    logger.info("="*60)
    logger.info("🧪 TESTING GRAPH.PHASE 2".center(60))
    logger.info("="*60)
    
    # Test detective graph
    logger.info("\n📊 Testing detective graph...")
    det_graph = create_detective_graph()
    logger.info(f"✅ Detective graph compiled!")
    logger.info(f"   Nodes: {list(det_graph.nodes.keys())}")
    
    # Test full graph
    logger.info("\n⚖️  Testing full graph with judges...")
    full_graph = create_full_graph()
    logger.info(f"✅ Full graph compiled!")
    logger.info(f"   Nodes: {list(full_graph.nodes.keys())}")
    
    # Test with minimal state (Pydantic model)
    logger.info("\n🚀 Testing execution with Pydantic state...")
    
    from src.state import AgentState
    
    test_state = AgentState(
        repo_url="https://github.com/langchain-ai/langgraph",
        pdf_path="test_report.pdf"
    )
    
    try:
        # Try detective graph first
        result = det_graph.invoke(test_state)
        logger.info(f"\n✅ Detective graph executed successfully!")
        evidences = result.get("evidences", {})
        logger.info(f"   Evidence collected: {list(evidences.keys())}")
        
        total_evidence = sum(len(ev_list) for ev_list in evidences.values())
        logger.info(f"   Total evidence items: {total_evidence}")
        
        # Test full graph with judges
        logger.info(f"\n⚖️  Testing full graph with judges...")
        
        # Create fresh state for judges test
        judge_state = AgentState(
            repo_url="https://github.com/langchain-ai/langgraph",
            pdf_path="test_report.pdf"
        )
        
        judge_result = full_graph.invoke(judge_state)
        logger.info(f"\n✅ Full graph executed successfully!")
        judge_evidences = judge_result.get("evidences", {})
        logger.info(f"   Evidence: {sum(len(ev_list) for ev_list in judge_evidences.values())} items")
        logger.info(f"   Opinions: {len(judge_result.get('opinions', []))}")
        
    except Exception as e:
        logger.error(f"\n❌ Execution error: {str(e)}")
        logger.info(f"   Type: {type(e).__name__}")
    
    logger.info("\n" + "="*60)