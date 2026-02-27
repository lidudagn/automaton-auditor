"""Main entry point for Automaton Auditor - Interim Submission."""

import argparse
import json
import os
from dotenv import load_dotenv

from src.graph import create_full_graph
from src.state import AgentState
import logging
logger = logging.getLogger(__name__)

# Load environment variables (API keys if needed)
load_dotenv()


def main():
    """Run the detective graph."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    parser = argparse.ArgumentParser(description="Automaton Auditor - Final Audit")
    parser.add_argument("--repo", required=True, help="GitHub repository URL")
    parser.add_argument("--pdf", required=True, help="Path to PDF report")
    parser.add_argument("--md-output", default="final_audit_report.md", help="Output Markdown report path")
    parser.add_argument("--json-output", default="evidence_output.json", help="Output JSON evidence path")
    parser.add_argument("--full-history", action="store_true", help="Clone full git history (slower but deeper)")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("🔍 AUTOMATON AUDITOR - FULL PIPELINE")
    logger.info("="*60)
    logger.info(f"Repository: {args.repo}")
    logger.info(f"PDF Report: {args.pdf}")
    logger.info(f"JSON Output: {args.json_output}")
    logger.info(f"MD Output:   {args.md_output}")
    logger.info("="*60)
    
    # Check if PDF exists
    if not os.path.exists(args.pdf):
        logger.error(f"❌ ERROR: PDF file not found: {args.pdf}")
        return
    
    # Create the graph
    logger.info("\n🚀 Initializing full graph...")
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
        rubric_dimensions=rubric,
        metadata={"full_history": args.full_history}
    )
    
    # Run the graph
    logger.info("\n🔍 Starting parallel detectives and judges...")
    logger.info("   (Executing full phase 2 pipeline)")
    logger.info("-" * 40)
    
    result = graph.invoke(initial_state)
    
    logger.info("-" * 40)
    logger.info("\n✅ Audit complete!")
    
    # Display results summary
    logger.info("\n📊 EVIDENCE COLLECTED SUMMARY:")
    logger.info("="*40)
    
    evidences_dict = result.get("evidences", {})
    
    total_evidence = 0
    for detector, evidences in evidences_dict.items():
        count = len(evidences)
        total_evidence += count
        logger.info(f"\n{detector.upper()}: {count} items")
        
        # Show first few items as sample
        for i, ev in enumerate(evidences[:2]):  # Show first 2 only
            status = "✅" if ev.found else "❌"
            logger.info(f"  {status} {ev.goal}")
    
    logger.info("\n" + "="*40)
    logger.info(f"TOTAL EVIDENCE ITEMS: {total_evidence}")
    logger.info("="*40)
    
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
    
    logger.info(f"\n💾 Evidence saved to JSON: {args.json_output}")
    
    # Generate and Save Markdown Report
    final_report = result.get("final_report")
    if final_report:
        from src.tools.report_tools import generate_markdown_report
        md_content = generate_markdown_report(final_report)
        with open(args.md_output, "w") as f:
            f.write(md_content)
        logger.info(f"📝 Final Markdown Report saved to: {args.md_output}")
    else:
        logger.warning("⚠️ No final report was generated. Graphs may have ended early due to lack of evidence.")

    logger.info("\n✨ Phase 2 Completion Submission Ready! ✨")


if __name__ == "__main__":
    main()