# """Detective nodes for evidence collection - Interim Submission."""

# import os
# from typing import Dict, List, Any

# from src.state import AgentState, Evidence
# from src.tools import repo_tools, doc_tools


# class RepoInvestigatorNode:
#     """Code detective - analyzes GitHub repository."""
    
#     def __call__(self, state: AgentState) -> Dict[str, Any]:
#         """
#         Execute repo investigation.
        
#         Args: state - Current agent state
#         Returns: Dict with updated evidences
#         """
#         repo_url = state.get("repo_url")
#         if not repo_url:
#             print("❌ RepoInvestigator: No repo URL provided")
#             error_evidence = Evidence(
#                 goal="Repository Access",
#                 found=False,
#                 content="No repo URL provided",
#                 location="N/A",
#                 rationale="Missing repository URL in state",
#                 confidence=0.0
#             )
#             return {"evidences": {"repo": [error_evidence]}}
        
#         print("🔍 RepoInvestigator: Starting analysis...")
        
#         try:
#             # Run all repo detective tools
#             evidences = repo_tools.main_detective_work(repo_url)
#             print(f"✅ RepoInvestigator: Found {len(evidences)} evidence items")
            
#         except Exception as e:
#             print(f"❌ RepoInvestigator error: {str(e)}")
#             evidences = [Evidence(
#                 goal="Repository Analysis",
#                 found=False,
#                 content=str(e),
#                 location=repo_url,
#                 rationale=f"Failed to analyze repository: {type(e).__name__}",
#                 confidence=0.0
#             )]
        
#         # Return with reducer key 'repo'
#         return {"evidences": {"repo": evidences}}


# class DocAnalystNode:
#     """Document detective - analyzes PDF report."""
    
#     def __call__(self, state: AgentState) -> Dict[str, Any]:
#         """
#         Execute document analysis.
        
#         Args: state - Current agent state
#         Returns: Dict with updated evidences
#         """
#         pdf_path = state.get("pdf_path")
#         if not pdf_path:
#             print("❌ DocAnalyst: No PDF path provided")
#             error_evidence = Evidence(
#                 goal="Document Access",
#                 found=False,
#                 content="No PDF path provided",
#                 location="N/A",
#                 rationale="Missing PDF path in state",
#                 confidence=0.0
#             )
#             return {"evidences": {"doc": [error_evidence]}}
        
#         print("📄 DocAnalyst: Starting PDF analysis...")
        
#         try:
#             # Run PDF analysis tools
#             evidences = doc_tools.analyze_pdf_report(pdf_path)
#             print(f"✅ DocAnalyst: Found {len(evidences)} evidence items")
            
#         except Exception as e:
#             print(f"❌ DocAnalyst error: {str(e)}")
#             evidences = [Evidence(
#                 goal="Document Analysis",
#                 found=False,
#                 content=str(e),
#                 location=pdf_path,
#                 rationale=f"Failed to analyze PDF: {type(e).__name__}",
#                 confidence=0.0
#             )]
        
#         # Return with reducer key 'doc'
#         return {"evidences": {"doc": evidences}}

# class VisionInspectorNode:
#     """Diagram detective - analyzes images in PDF."""
    
#     def __call__(self, state: AgentState) -> Dict[str, Any]:
#         print("👁️ VisionInspector: Analyzing PDF for diagrams...")
#         pdf_path = state.get("pdf_path")
        
#         if not pdf_path or not os.path.exists(pdf_path):
#             print("❌ VisionInspector: PDF not found")
#             evidence = Evidence(
#                 goal="Diagram Analysis",
#                 found=False,
#                 content="PDF not available",
#                 location=pdf_path or "N/A",
#                 rationale="Cannot analyze without valid PDF",
#                 confidence=0.0
#             )
#             return {"evidences": {"vision": [evidence]}}
        
#         try:
#             from src.tools.vision_tools import detect_diagrams_in_pdf
#             evidences = detect_diagrams_in_pdf(pdf_path)
            
#             # If no images found, make it neutral (found=True with explanation)
#             if evidences and not evidences[0].found:
#                 # CHANGE: Set found=True for expected absence
#                 evidences[0].found = True
#                 evidences[0].goal = "Diagram Analysis (No diagrams found - expected)"
#                 evidences[0].confidence = 0.8  # High confidence in correct detection
#                 evidences[0].rationale = "PDF contains no embedded diagrams - this is normal"
#                 print(f"ℹ️ VisionInspector: No diagrams detected (this is correct)")
#             else:
#                 print(f"✅ VisionInspector: Found diagrams!")
            
#             return {"evidences": {"vision": evidences}}
            
#         except Exception as e:
#             print(f"❌ VisionInspector error: {str(e)}")
#             evidence = Evidence(
#                 goal="Diagram Analysis",
#                 found=False,
#                 content=str(e),
#                 location=pdf_path,
#                 rationale=f"Analysis failed: {type(e).__name__}",
#                 confidence=0.0
#             )
#             return {"evidences": {"vision": [evidence]}}
# class EvidenceAggregatorNode:
#     """Collects and organizes evidence from all detectives."""
    
#     def __call__(self, state: AgentState) -> Dict[str, Any]:
#         """
#         Aggregate and validate evidence.
        
#         This node runs after all detectives complete.
#         It doesn't change state - just logs what was collected.
#         """
#         evidences = state.get("evidences", {})
        
#         print("\n" + "="*60)
#         print("📊 EVIDENCE AGGREGATOR".center(60))
#         print("="*60)
        
#         total = 0
#         successful = 0
        
#         for detector, ev_list in evidences.items():
#             count = len(ev_list)
#             total += count
            
#             # Count successful evidence (found=True)
#             successful += sum(1 for ev in ev_list if ev.found)
            
#             # Format detector name for display
#             det_name = detector.upper()
#             print(f"\n  {det_name}: {count} evidence items")
            
#             # Print sample evidence (first 2 items max)
#             for i, ev in enumerate(ev_list[:2]):
#                 status = "✅" if ev.found else "❌"
#                 print(f"    {i+1}. {status} {ev.goal}")
#                 print(f"       {ev.rationale[:60]}..." if len(ev.rationale) > 60 else f"       {ev.rationale}")
        
#         # Summary statistics
#         print("\n" + "-"*60)
#         print(f"  📈 SUMMARY:")
#         print(f"     Total evidence items: {total}")
#         print(f"     Successful findings: {successful}")
#         print(f"     Success rate: {successful/total*100:.1f}%" if total > 0 else "     No evidence collected")
#         print("="*60 + "\n")
        
#         # Return empty - state already updated via reducers
#         return {}


# if __name__ == "__main__":
#     print("\n🧪 Testing detective nodes...")
#     print("="*40)
    
#     # Create test state
#     test_state = {
#         "repo_url": "https://github.com/langchain-ai/langgraph",
#         "pdf_path": "test_report.pdf",  
#         "rubric_dimensions": [],
#         "evidences": {},
#         "opinions": [],
#         "final_report": None
#     }
    
#     print("\n🔍 Testing RepoInvestigator...")
#     repo_node = RepoInvestigatorNode()
#     repo_result = repo_node(test_state)
#     repo_ev_count = len(repo_result.get("evidences", {}).get("repo", []))
#     print(f"   → Found {repo_ev_count} evidence items")
    
#     print("\n📄 Testing DocAnalyst...")
#     doc_node = DocAnalystNode()
#     doc_result = doc_node(test_state)
#     doc_ev_count = len(doc_result.get("evidences", {}).get("doc", []))
#     print(f"   → Found {doc_ev_count} evidence items")
    
#     print("\n👁️ Testing VisionInspector...")
#     vision_node = VisionInspectorNode()
#     vision_result = vision_node(test_state)
#     vision_ev_count = len(vision_result.get("evidences", {}).get("vision", []))
#     print(f"   → Found {vision_ev_count} evidence items (empty = correct!)")
    
#     print("\n✅ All detective nodes ready!")
    
#     # Test aggregator with combined results
#     print("\n📊 Testing EvidenceAggregator...")
    
#     # Combine results into one state
#     combined_state = {
#         "repo_url": test_state["repo_url"],
#         "pdf_path": test_state["pdf_path"],
#         "rubric_dimensions": [],
#         "evidences": {
#             **repo_result.get("evidences", {}),
#             **doc_result.get("evidences", {}),
#             **vision_result.get("evidences", {})
#         },
#         "opinions": [],
#         "final_report": None
#     }
    
#     agg_node = EvidenceAggregatorNode()
#     agg_node(combined_state)


"""Detective nodes for evidence collection - Phase 2 with Pydantic state."""

import os
from typing import Dict, Any

from src.state import AgentState, Evidence
from src.tools import repo_tools, doc_tools, vision_tools


class RepoInvestigatorNode:
    """Code detective - analyzes GitHub repository."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute repo investigation.
        
        Args: state - Current agent state (Pydantic model)
        Returns: Dict with evidences to merge via reducer
        """
        repo_url = state.repo_url
        evidences_list = []  # ← Collect evidence here
        
        if not repo_url:
            print("❌ RepoInvestigator: No repo URL provided")
            evidences_list.append(Evidence(
                goal="Repository Access",
                found=False,
                content="No repo URL provided",
                location="N/A",
                rationale="Missing repository URL in state",
                confidence=0.0
            ))
            # Return the evidence to be merged
            return {"evidences": {"repo": evidences_list}}
        
        print("🔍 RepoInvestigator: Starting analysis...")
        
        try:
            # Run all repo detective tools
            evidences = repo_tools.main_detective_work(repo_url)
            evidences_list.extend(evidences)
            print(f"✅ RepoInvestigator: Collected {len(evidences_list)} evidence items")
            
        except Exception as e:
            print(f"❌ RepoInvestigator error: {str(e)}")
            evidences_list.append(Evidence(
                goal="Repository Analysis",
                found=False,
                content=str(e),
                location=repo_url,
                rationale=f"Failed to analyze repository: {type(e).__name__}",
                confidence=0.0
            ))
        
        # ✅ RETURN THE EVIDENCE - this is what gets merged by the reducer
        return {"evidences": {"repo": evidences_list}}
class DocAnalystNode:
    """Document detective - analyzes PDF report."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute document analysis.
        
        Args: state - Current agent state (Pydantic model)
        Returns: Empty dict (state updated in-place via add_evidence)
        """
        pdf_path = state.pdf_path
        
        if not pdf_path:
            print("❌ DocAnalyst: No PDF path provided")
            state.add_evidence("doc", Evidence(
                goal="Document Access",
                found=False,
                content="No PDF path provided",
                location="N/A",
                rationale="Missing PDF path in state",
                confidence=0.0
            ))
            return {}
        
        print("📄 DocAnalyst: Starting PDF analysis...")
        
        try:
            # Run PDF analysis tools
            evidences = doc_tools.analyze_pdf_report(pdf_path)
            for evidence in evidences:
                state.add_evidence("doc", evidence)
            print(f"✅ DocAnalyst: Added {len(evidences)} evidence items")
            
        except Exception as e:
            print(f"❌ DocAnalyst error: {str(e)}")
            state.add_evidence("doc", Evidence(
                goal="Document Analysis",
                found=False,
                content=str(e),
                location=pdf_path,
                rationale=f"Failed to analyze PDF: {type(e).__name__}",
                confidence=0.0
            ))
        
        return {}


class VisionInspectorNode:
    """Diagram detective - analyzes images in PDF."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute diagram analysis.
        
        Args: state - Current agent state (Pydantic model)
        Returns: Empty dict (state updated in-place via add_evidence)
        """
        pdf_path = state.pdf_path
        
        if not pdf_path or not os.path.exists(pdf_path):
            print("❌ VisionInspector: PDF not found")
            state.add_evidence("vision", Evidence(
                goal="Diagram Analysis",
                found=False,
                content="PDF not available",
                location=pdf_path or "N/A",
                rationale="Cannot analyze without valid PDF",
                confidence=0.0
            ))
            return {}
        
        print("👁️ VisionInspector: Analyzing PDF for diagrams...")
        
        try:
            evidences = vision_tools.detect_diagrams_in_pdf(pdf_path)
            
            # If no images found, make it neutral (found=True with explanation)
            if evidences and not evidences[0].found:
                evidences[0].found = True
                evidences[0].goal = "Diagram Analysis (No diagrams found - expected)"
                evidences[0].confidence = 0.8
                evidences[0].rationale = "PDF contains no embedded diagrams - this is normal"
                print(f"ℹ️ VisionInspector: No diagrams detected (this is correct)")
            else:
                print(f"✅ VisionInspector: Found diagrams!")
            
            for evidence in evidences:
                state.add_evidence("vision", evidence)
            
        except Exception as e:
            print(f"❌ VisionInspector error: {str(e)}")
            state.add_evidence("vision", Evidence(
                goal="Diagram Analysis",
                found=False,
                content=str(e),
                location=pdf_path,
                rationale=f"Analysis failed: {type(e).__name__}",
                confidence=0.0
            ))
        
        return {}


class EvidenceAggregatorNode:
    """Collects and organizes evidence from all detectives."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Aggregate and display evidence summary.
        
        Args: state - Current agent state with all evidence
        Returns: Empty dict
        """
        print("\n" + "="*60)
        print("📊 EVIDENCE AGGREGATOR".center(60))
        print("="*60)
        
        if not state.evidences:
            print("\n  No evidence collected")
            print("\n" + "="*60)
            return {}
        
        total = 0
        successful = 0
        
        for detector, ev_list in state.evidences.items():
            count = len(ev_list)
            total += count
            successful += sum(1 for ev in ev_list if ev.found)
            
            det_name = detector.upper()
            print(f"\n  {det_name}: {count} evidence items")
            
            # Print sample evidence (first 2 items)
            for i, ev in enumerate(ev_list[:2]):
                status = "✅" if ev.found else "❌"
                print(f"    {i+1}. {status} {ev.goal}")
                rationale_short = ev.rationale[:60] + "..." if len(ev.rationale) > 60 else ev.rationale
                print(f"       {rationale_short}")
        
        # Summary statistics using state helper methods
        print("\n" + "-"*60)
        print(f"  📈 SUMMARY:")
        print(f"     Total evidence items: {state.get_evidence_count()}")
        print(f"     Successful findings: {state.get_successful_evidence()}")
        print(f"     Success rate: {state.get_success_rate():.1f}%")
        print("="*60 + "\n")
        
        return {}
    

    
if __name__ == "__main__":
    print("\n🧪 Testing detective nodes with Pydantic state...")
    print("="*60)
    
    # Create test state using Pydantic model
    from src.state import AgentState
    
    test_state = AgentState(
        repo_url="https://github.com/langchain-ai/langgraph",
        pdf_path="test_report.pdf"
    )
    
    print(f"\n🔍 Testing RepoInvestigator...")
    print(f"   State type: {type(test_state).__name__}")  # Should show "AgentState"
    repo_node = RepoInvestigatorNode()
    repo_node(test_state)
    repo_count = len(test_state.evidences.get("repo", []))
    print(f"   → Added {repo_count} repo evidence items")
    
    print(f"\n📄 Testing DocAnalyst...")
    doc_node = DocAnalystNode()
    doc_node(test_state)
    doc_count = len(test_state.evidences.get("doc", []))
    print(f"   → Added {doc_count} doc evidence items")
    
    print(f"\n👁️ Testing VisionInspector...")
    vision_node = VisionInspectorNode()
    vision_node(test_state)
    vision_count = len(test_state.evidences.get("vision", []))
    print(f"   → Added {vision_count} vision evidence items")
    
    print(f"\n📊 Testing EvidenceAggregator...")
    agg_node = EvidenceAggregatorNode()
    agg_node(test_state)
    
    print(f"\n✅ Final Results:")
    print(f"   Total evidence: {test_state.get_evidence_count()}")
    print(f"   Success rate: {test_state.get_success_rate():.1f}%")
    print("="*60)