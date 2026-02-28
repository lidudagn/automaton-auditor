"""Meta-Audit Orchestrator for Automaton Auditor - Phase 5."""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import List
from dotenv import load_dotenv

from src.graph import create_full_graph
from src.state import AgentState, AuditRun, MetaAuditState
from src.nodes.meta_audit import MetaAuditNode

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_meta_audit(repo_url: str, pdf_path: str, n_runs: int = 5):
    """Execute N deterministic runs and consolidate via MetaAuditNode."""
    logger.info(f"🚀 STARTING META-AUDIT SUITE: {repo_url} (N={n_runs} runs)")
    
    graph = create_full_graph()
    runs = []
    
    # Calibrated rubric
    rubric = [
        {"id": "graph_orchestration_architecture", "name": "Core Architecture & Modularity"},
        {"id": "state_management_rigor", "name": "State Management & Resilience"},
        {"id": "test_infrastructure", "name": "Testing Rigor & Coverage"},
        {"id": "repository_structure", "name": "Repository Format & Onboarding"}
    ]

    for i in range(1, n_runs + 1):
        logger.info(f"\n▶️ RUN {i}/{n_runs}...")
        
        # We can introduce jitter or seed variations here if our nodes were seedable
        # For now, deterministic nodes will behave similarly, but LLM non-determinism 
        # (even at temp 0) will provide the variance we need to test stability.
        
        initial_state = AgentState(
            repo_url=repo_url,
            pdf_path=pdf_path,
            rubric_dimensions=rubric
        )
        
        # Run the single audit
        result = graph.invoke(initial_state)
        report = result.get("final_report")
        
        if report:
            audit_run = AuditRun(
                run_id=i,
                overall_score=report.overall_score,
                opinions=result.get("opinions", []),
                registry_state=result.get("registry", {}).all(),
                contradictions_found=report.detected_contradictions
            )
            runs.append(audit_run)
            logger.info(f"  ✅ Run {i} Complete. Score: {report.overall_score:.2f}")
        else:
            logger.error(f"  ❌ Run {i} FAILED to generate report.")

    if not runs:
        logger.error("❌ All runs failed. Aborting Meta-Audit.")
        return

    # Consolidate via MetaAuditNode
    meta_state = MetaAuditState(
        repo_url=repo_url,
        runs=runs
    )
    
    meta_node = MetaAuditNode()
    meta_result = meta_node(meta_state)
    
    # Generate Meta Report
    _generate_meta_report(meta_state)
    
    logger.info("\n🏆 META-AUDIT COMPLETE.")
    logger.info(f"📝 Master Report generated: meta_audit_report.md")

def _generate_meta_report(state: MetaAuditState):
    """Generate Markdown report for Meta-Audit results."""
    lines = [
        "# Meta-Audit Master Report",
        f"**Repository:** {state.repo_url}",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Aggregation Size:** {len(state.runs)} runs",
        "",
        "## Overall Meta-Scores",
        "| Criterion | Meta-Score | Multi-Run Stability |",
        "|---|---|---|",
    ]
    
    # Group evidence for stability lookup
    for crit_id, score in state.meta_scores.items():
        stability = _get_avg_stability(state, crit_id)
        lines.append(f"| {crit_id} | {score} | {stability:.2f} |")
        
    lines.append("\n## Meta-Reasoning Trace")
    for log in state.reasoning_trace:
        lines.append(f"- {log}")
        
    lines.append("\n## Run History Summary")
    lines.append("| Run ID | Overall Score | Evidence Count |")
    lines.append("|---|---|---|")
    for run in state.runs:
        lines.append(f"| {run.run_id} | {run.overall_score:.2f} | {len(run.registry_state)} |")

    with open("meta_audit_report.md", "w") as f:
        f.write("\n".join(lines))

def _get_avg_stability(state: MetaAuditState, criterion_id: str) -> float:
    relevant = [
        ev.stability_score for ev in state.meta_registry.values()
        if ev.claim_reference and criterion_id.lower() in ev.claim_reference.lower()
    ]
    return sum(relevant) / len(relevant) if relevant else 0.0

if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/langchain-ai/langgraph"
    asyncio.run(run_meta_audit(repo, "test_report.pdf", n_runs=3)) # Using 3 for test speed
