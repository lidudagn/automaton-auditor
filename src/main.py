"""Main entry point for Automaton Auditor - Interim Submission."""

import argparse
import json
import os
from dotenv import load_dotenv

from src.graph import create_detective_graph
from src.state import AgentState

# Load environment variables (API keys if needed)
load_dotenv()


def main():
    """Run the detective graph."""
    parser = argparse.ArgumentParser(description="Automaton Auditor - Interim Submission")
    parser.add_argument("--repo", required=True, help="GitHub repository URL")
    parser.add_argument("--pdf", required=True, help="Path to PDF report")
    parser.add_argument("--output", default="evidence_output.json", help="Output file path")
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔍 AUTOMATON AUDITOR - DETECTIVE LAYER")
    print("="*60)
    print(f"Repository: {args.repo}")
    print(f"PDF Report: {args.pdf}")
    print(f"Output: {args.output}")
    print("="*60)
    
    # Check if PDF exists
    if not os.path.exists(args.pdf):
        print(f"❌ ERROR: PDF file not found: {args.pdf}")
        return
    
    # Create the graph
    print("\n🚀 Initializing detective graph...")
    graph = create_detective_graph()
    
    # Initial state
    initial_state = {
        "repo_url": args.repo,
        "pdf_path": args.pdf,
        "rubric_dimensions": [],  # Empty for interim
        "evidences": {},           # Will be filled by detectives
        "opinions": [],            # Not used yet
        "final_report": None
    }
    
    # Run the graph
    print("\n🔍 Starting parallel detectives...")
    print("   (RepoInvestigator, DocAnalyst, VisionInspector running simultaneously)")
    print("-" * 40)
    
    result = graph.invoke(initial_state)
    
    print("-" * 40)
    print("\n✅ Audit complete!")
    
    # Display results summary
    print("\n📊 EVIDENCE COLLECTED SUMMARY:")
    print("="*40)
    
    total_evidence = 0
    for detector, evidences in result["evidences"].items():
        count = len(evidences)
        total_evidence += count
        print(f"\n{detector.upper()}: {count} items")
        
        # Show first few items as sample
        for i, ev in enumerate(evidences[:2]):  # Show first 2 only
            status = "✅" if ev.found else "❌"
            print(f"  {status} {ev.goal}")
            print(f"     Location: {ev.location}")
            print(f"     Confidence: {ev.confidence*100:.0f}%")
    
    print("\n" + "="*40)
    print(f"TOTAL EVIDENCE ITEMS: {total_evidence}")
    print("="*40)
    
    # Save to file
    with open(args.output, 'w') as f:
        output_data = {
            "repo_url": result["repo_url"],
            "pdf_path": result["pdf_path"],
            "summary": {
                "total_evidence": total_evidence,
                "detectors": list(result["evidences"].keys())
            },
            "evidences": {
                k: [ev.model_dump() for ev in v]
                for k, v in result["evidences"].items()
            }
        }
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Evidence saved to: {args.output}")
    print("\n✨ Interim submission ready! ✨")


if __name__ == "__main__":
    main()