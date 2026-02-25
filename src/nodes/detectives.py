
import os
from typing import Dict, List, Any

from src.state import AgentState, Evidence
from src.tools import repo_tools, doc_tools


class RepoInvestigatorNode:
    """Code detective - analyzes GitHub repository."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute repo investigation.
        
        Args: state - Current agent state
        Returns: Dict with updated evidences
        """
        repo_url = state.get("repo_url")
        if not repo_url:
            error_evidence = Evidence(
                goal="Repository Access",
                found=False,
                content="No repo URL provided",
                location="N/A",
                rationale="Missing repository URL in state",
                confidence=0.0
            )
            return {"evidences": {"repo": [error_evidence]}}
        
        print("🔍 RepoInvestigator: Starting analysis...")
        
        try:
            # Run all repo detective tools
            evidences = repo_tools.main_detective_work(repo_url)
            print(f"✅ RepoInvestigator: Found {len(evidences)} evidence items")
            
        except Exception as e:
            print(f"❌ RepoInvestigator error: {str(e)}")
            evidences = [Evidence(
                goal="Repository Analysis",
                found=False,
                content=str(e),
                location=repo_url,
                rationale="Failed to analyze repository",
                confidence=0.0
            )]
        
        # Return with reducer key 'repo'
        return {"evidences": {"repo": evidences}}


class DocAnalystNode:
    """Document detective - analyzes PDF report."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute document analysis.
        
        Args: state - Current agent state
        Returns: Dict with updated evidences
        """
        pdf_path = state.get("pdf_path")
        if not pdf_path:
            error_evidence = Evidence(
                goal="Document Access",
                found=False,
                content="No PDF path provided",
                location="N/A",
                rationale="Missing PDF path in state",
                confidence=0.0
            )
            return {"evidences": {"doc": [error_evidence]}}
        
        print("📄 DocAnalyst: Starting PDF analysis...")
        
        try:
            # Run PDF analysis tools
            evidences = doc_tools.analyze_pdf_report(pdf_path)
            print(f"✅ DocAnalyst: Found {len(evidences)} evidence items")
            
        except Exception as e:
            print(f"❌ DocAnalyst error: {str(e)}")
            evidences = [Evidence(
                goal="Document Analysis",
                found=False,
                content=str(e),
                location=pdf_path,
                rationale="Failed to analyze PDF",
                confidence=0.0
            )]
        
        # Return with reducer key 'doc'
        return {"evidences": {"doc": evidences}}


class VisionInspectorNode:
    """Diagram detective - analyzes images in PDF (optional for interim)."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute diagram analysis - minimal version for interim.
        """
        print("👁️ VisionInspector: Skipping (optional for interim)")
        
        # Return empty evidence list with 'vision' key
        evidence = Evidence(
            goal="Diagram Analysis",
            found=False,
            content="Vision inspector not implemented for interim",
            location=state.get("pdf_path", "N/A"),
            rationale="Optional component - skipped for Wednesday submission",
            confidence=0.0
        )
        
        return {"evidences": {"vision": [evidence]}}


class EvidenceAggregatorNode:
    """Collects and organizes evidence from all detectives."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Aggregate and validate evidence.
        
        This node runs after all detectives complete.
        It doesn't change state - just logs what was collected.
        """
        evidences = state.get("evidences", {})
        
        print("\n" + "="*50)
        print("📊 EVIDENCE AGGREGATOR")
        print("="*50)
        
        total = 0
        for detector, ev_list in evidences.items():
            count = len(ev_list)
            total += count
            print(f"  {detector}: {count} evidence items")
            
            # Print first evidence from each detector as sample
            if ev_list:
                sample = ev_list[0]
                print(f"    Sample: {sample.goal} - {'✅' if sample.found else '❌'}")
        
        print(f"\n  TOTAL: {total} evidence items collected")
        print("="*50 + "\n")
        
        # Return empty - state already updated via reducers
        return {}


if __name__ == "__main__":
    print("Testing detective nodes...")
    
    # Create test state
    test_state = {
        "repo_url": "https://github.com/langchain-ai/langgraph",
        "pdf_path": "test_report.pdf",  # ← CHANGE THIS LINE
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    # Test RepoInvestigator
    repo_node = RepoInvestigatorNode()
    result = repo_node(test_state)
    print(f"\nRepoInvestigator output: {list(result.keys())}")
    
    # Test DocAnalyst
    doc_node = DocAnalystNode()
    result = doc_node(test_state)
    print(f"DocAnalyst output: {list(result.keys())}")
    
    print("\n✅ Detective nodes ready")