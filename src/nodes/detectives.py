"""Detective nodes for evidence collection - Interim Submission."""

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
            print("❌ RepoInvestigator: No repo URL provided")
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
                rationale=f"Failed to analyze repository: {type(e).__name__}",
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
            print("❌ DocAnalyst: No PDF path provided")
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
                rationale=f"Failed to analyze PDF: {type(e).__name__}",
                confidence=0.0
            )]
        
        # Return with reducer key 'doc'
        return {"evidences": {"doc": evidences}}


class VisionInspectorNode:
    """Diagram detective - analyzes images in PDF (optional for interim)."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute diagram analysis - minimal version for interim.
        
        FIXED: Returns EMPTY list instead of fake negative evidence.
        This prevents penalizing ourselves with false negatives.
        """
        print("👁️ VisionInspector: Skipped (not implemented for interim)")
        
        # ✅ FIXED: Return EMPTY list - no fake evidence
        # This is cleaner and doesn't create false negatives
        return {"evidences": {"vision": []}}


class EvidenceAggregatorNode:
    """Collects and organizes evidence from all detectives."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Aggregate and validate evidence.
        
        This node runs after all detectives complete.
        It doesn't change state - just logs what was collected.
        """
        evidences = state.get("evidences", {})
        
        print("\n" + "="*60)
        print("📊 EVIDENCE AGGREGATOR".center(60))
        print("="*60)
        
        total = 0
        successful = 0
        
        for detector, ev_list in evidences.items():
            count = len(ev_list)
            total += count
            
            # Count successful evidence (found=True)
            successful += sum(1 for ev in ev_list if ev.found)
            
            # Format detector name for display
            det_name = detector.upper()
            print(f"\n  {det_name}: {count} evidence items")
            
            # Print sample evidence (first 2 items max)
            for i, ev in enumerate(ev_list[:2]):
                status = "✅" if ev.found else "❌"
                print(f"    {i+1}. {status} {ev.goal}")
                print(f"       {ev.rationale[:60]}..." if len(ev.rationale) > 60 else f"       {ev.rationale}")
        
        # Summary statistics
        print("\n" + "-"*60)
        print(f"  📈 SUMMARY:")
        print(f"     Total evidence items: {total}")
        print(f"     Successful findings: {successful}")
        print(f"     Success rate: {successful/total*100:.1f}%" if total > 0 else "     No evidence collected")
        print("="*60 + "\n")
        
        # Return empty - state already updated via reducers
        return {}


if __name__ == "__main__":
    print("\n🧪 Testing detective nodes...")
    print("="*40)
    
    # Create test state
    test_state = {
        "repo_url": "https://github.com/langchain-ai/langgraph",
        "pdf_path": "test_report.pdf",  
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    
    print("\n🔍 Testing RepoInvestigator...")
    repo_node = RepoInvestigatorNode()
    repo_result = repo_node(test_state)
    repo_ev_count = len(repo_result.get("evidences", {}).get("repo", []))
    print(f"   → Found {repo_ev_count} evidence items")
    
    print("\n📄 Testing DocAnalyst...")
    doc_node = DocAnalystNode()
    doc_result = doc_node(test_state)
    doc_ev_count = len(doc_result.get("evidences", {}).get("doc", []))
    print(f"   → Found {doc_ev_count} evidence items")
    
    print("\n👁️ Testing VisionInspector...")
    vision_node = VisionInspectorNode()
    vision_result = vision_node(test_state)
    vision_ev_count = len(vision_result.get("evidences", {}).get("vision", []))
    print(f"   → Found {vision_ev_count} evidence items (empty = correct!)")
    
    print("\n✅ All detective nodes ready!")
    
    # Test aggregator with combined results
    print("\n📊 Testing EvidenceAggregator...")
    
    # Combine results into one state
    combined_state = {
        "repo_url": test_state["repo_url"],
        "pdf_path": test_state["pdf_path"],
        "rubric_dimensions": [],
        "evidences": {
            **repo_result.get("evidences", {}),
            **doc_result.get("evidences", {}),
            **vision_result.get("evidences", {})
        },
        "opinions": [],
        "final_report": None
    }
    
    agg_node = EvidenceAggregatorNode()
    agg_node(combined_state)