"""Main entry point for Automaton Auditor - Interim Submission."""

import argparse
import json
import os
from dotenv import load_dotenv

from src.graph import create_full_graph
from src.state import AgentState

# Load environment variables (API keys if needed)
load_dotenv()


def main():
    """Run the detective graph."""
    parser = argparse.ArgumentParser(description="Automaton Auditor - Final Audit")
    parser.add_argument("--repo", required=True, help="GitHub repository URL")
    parser.add_argument("--pdf", required=True, help="Path to PDF report")
    parser.add_argument("--md-output", default="final_audit_report.md", help="Output Markdown report path")
    parser.add_argument("--json-output", default="evidence_output.json", help="Output JSON evidence path")
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔍 AUTOMATON AUDITOR - FULL PIPELINE")
    print("="*60)
    print(f"Repository: {args.repo}")
    print(f"PDF Report: {args.pdf}")
    print(f"JSON Output: {args.json_output}")
    print(f"MD Output:   {args.md_output}")
    print("="*60)
    
    # Check if PDF exists
    if not os.path.exists(args.pdf):
        print(f"❌ ERROR: PDF file not found: {args.pdf}")
        return
    
    # Create the graph
    print("\n🚀 Initializing full graph...")
    graph = create_full_graph()
    
    # Generate generic rubric for the full audit
    rubric = [
        {"id": "git_forensic_analysis", "name": "Git Forensic Analysis"},
        {"id": "state_management_rigor", "name": "State Management Rigor"},
        {"id": "graph_orchestration", "name": "Graph Orchestration Architecture"},
        {"id": "safe_tool_engineering", "name": "Safe Tool Engineering"},
        {"id": "structured_output", "name": "Structured Output Enforcement"},
        {"id": "judicial_nuance", "name": "Judicial Nuance"},
        {"id": "theoretical_depth", "name": "Theoretical Depth"}
    ]
    
    # Initial state
    initial_state = AgentState(
        repo_url=args.repo,
        pdf_path=args.pdf,
        rubric_dimensions=rubric
    )
    
    # Run the graph
    print("\n🔍 Starting parallel detectives and judges...")
    print("   (Executing full phase 2 pipeline)")
    print("-" * 40)
    
    result = graph.invoke(initial_state)
    
    print("-" * 40)
    print("\n✅ Audit complete!")
    
    # Display results summary
    print("\n📊 EVIDENCE COLLECTED SUMMARY:")
    print("="*40)
    
    evidences_dict = result.get("evidences", {})
    
    total_evidence = 0
    for detector, evidences in evidences_dict.items():
        count = len(evidences)
        total_evidence += count
        print(f"\n{detector.upper()}: {count} items")
        
        # Show first few items as sample
        for i, ev in enumerate(evidences[:2]):  # Show first 2 only
            status = "✅" if ev.found else "❌"
            print(f"  {status} {ev.goal}")
    
    print("\n" + "="*40)
    print(f"TOTAL EVIDENCE ITEMS: {total_evidence}")
    print("="*40)
    
    # Save JSON Evidence
    with open(args.json_output, 'w') as f:
        output_data = {
            "repo_url": result.get("repo_url", args.repo),
            "pdf_path": result.get("pdf_path", args.pdf),
            "summary": {
                "total_evidence": total_evidence,
                "detectors": list(evidences_dict.keys())
            },
            "evidences": {
                k: [json.loads(ev.model_dump_json()) if hasattr(ev, "model_dump_json") else json.loads(ev.json()) for ev in v]
                for k, v in evidences_dict.items()
            }
        }
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Evidence saved to JSON: {args.json_output}")
    
    # Generate and Save Markdown Report
    final_report = result.get("final_report")
    if final_report:
        from src.tools.report_tools import generate_markdown_report
        md_content = generate_markdown_report(final_report)
        with open(args.md_output, "w") as f:
            f.write(md_content)
        print(f"📝 Final Markdown Report saved to: {args.md_output}")
    else:
        print("⚠️ No final report was generated. Graphs may have ended early due to lack of evidence.")

    print("\n✨ Phase 2 Completion Submission Ready! ✨")


if __name__ == "__main__":
    main()