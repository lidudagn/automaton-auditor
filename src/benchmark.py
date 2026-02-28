"""Benchmarking Engine for Automaton Auditor Multi-Run Calibration."""

import json
import csv
import sys
import os
import asyncio
from typing import List, Dict, Any
from collections import defaultdict
import logging

from src.graph import create_full_graph
from src.state import AgentState

# Setup basic logging to monitor progress
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

TARGETS_FILE = "config/benchmark_targets.json"
RESULTS_FILE = "benchmark_results.csv"

# Generic Pre-defined dimensions mapped strictly to Detective Node Evidence Goals
DEFAULT_DIMENSIONS = [
    {"id": "graph_orchestration_architecture", "name": "Core Architecture & Modularity"},
    {"id": "state_management_rigor", "name": "State Management & Resilience"},
    {"id": "test_infrastructure", "name": "Testing Rigor & Coverage"},
    {"id": "repository_structure", "name": "Repository Format & Onboarding"}
]

async def run_benchmark():
    """Execute the benchmarking suite across all defined targets."""
    
    if not os.path.exists(TARGETS_FILE):
        logger.error(f"❌ Targets file not found: {TARGETS_FILE}")
        sys.exit(1)
        
    with open(TARGETS_FILE, 'r') as f:
        targets = json.load(f)
        
    logger.info(f"🚀 Starting Benchmarking Suite across {len(targets)} targets...\n")
    
    graph = create_full_graph()
    all_results = []
    tier_stats = defaultdict(list)
    diagnostic_mode = "--diagnostic" in sys.argv
    
    for target in targets:
        target_id = target["id"]
        repo_url = target["repo_url"]
        pdf_path = target["pdf_path"]
        expected_tier = target["expected_tier"]
        
        logger.info(f"Targeting: {target_id} ({expected_tier} Tier)")
        logger.info(f"Repository: {repo_url}")
        
        # Initialize state
        initial_state = AgentState(
            repo_url=repo_url,
            pdf_path=pdf_path,
            rubric_dimensions=DEFAULT_DIMENSIONS
        )
        
        try:
            # Run the graph
            logger.info("  Executing audit pipeline...")
            final_state = await graph.ainvoke(initial_state)
            
            report = final_state.get("final_report")
            
            if not report:
                logger.error(f"  ❌ No report generated for {target_id}")
                continue
                
            logger.info(f"  ✅ Complete! Final Score: {report.overall_score:.1f}/5.0")
            
            # Extract criteria metrics
            if diagnostic_mode:
                logger.info(f"\n  🔍 [DIAGNOSTIC MODE] criterion analysis for {target_id}")
                for op in final_state.get("opinions", []):
                    logger.info(f"    - OPINION [{op.criterion_id}] {op.judge}: {op.score}/5 - {op.argument}")

            for criterion in report.criteria:
                result_row = {
                    "target_id": target_id,
                    "expected_tier": expected_tier,
                    "dimension_id": criterion.dimension_id,
                    "base_score": criterion.base_score,
                    "penalty_applied": criterion.penalty_applied,
                    "final_score": criterion.final_score,
                    "contradiction_flag": criterion.contradiction_flag
                }
                if diagnostic_mode:
                    logger.info(f"    [Criterion] {criterion.dimension_id}")
                    logger.info(f"      - Base Score: {criterion.base_score}")
                    logger.info(f"      - Penalty: {criterion.penalty_applied}")
                    logger.info(f"      - Contradiction: {criterion.contradiction_flag}")
                
                all_results.append(result_row)
                
            # Store overall stats for the curve generation
            tier_stats[expected_tier].append(report)
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {target_id}: {str(e)}")
            
    # Write to CSV
    logger.info(f"\n💾 Writing results to {RESULTS_FILE}...")
    with open(RESULTS_FILE, 'w', newline='') as csvfile:
        fieldnames = ["target_id", "expected_tier", "dimension_id", "base_score", "penalty_applied", "final_score", "contradiction_flag"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
            
    logger.info("CSV generation complete.")
    
    # Generate Statistical Summaries & Calibration Curves
    generate_calibration_curves(tier_stats, all_results)


def generate_calibration_curves(tier_stats: Dict[str, List[Any]], all_results: List[Dict]):
    """Print ASCII statistical summaries, calibration impact curves, and write to markdown."""
    
    logger.info("\n" + "="*60)
    logger.info("📊 CALIBRATION SCORING CURVES & METRICS")
    logger.info("="*60)
    
    tiers = ["High", "Medium", "Broken"]
    md_content = "# Automaton Auditor: Multi-Run Calibration Report\n\n"
    
    for tier in tiers:
        if tier not in tier_stats or not tier_stats[tier]:
            continue
            
        reports = tier_stats[tier]
        avg_final = sum(r.overall_score for r in reports) / len(reports)
        
        # Calculate base vs final impact specifically from criteria
        tier_rows = [row for row in all_results if row["expected_tier"] == tier]
        total_base = sum(row["base_score"] for row in tier_rows)
        total_final = sum(row["final_score"] for row in tier_rows)
        total_penalties = sum(row["penalty_applied"] for row in tier_rows)
        contradictions_found = sum(1 for row in tier_rows if row["contradiction_flag"])
        
        # Parse reasoning trace events
        hallucination_prunes = 0
        variance_prunes = 0
        security_overrides = 0
        coherence_penalties = 0
        
        for report in reports:
            for c in report.criteria:
                trace_text = " ".join(c.reasoning_trace).lower()
                hallucination_prunes += trace_text.count("pruned due to invalid citation")
                variance_prunes += trace_text.count("variance arbitration triggered")
                security_overrides += trace_text.count("capped by security protocol")
                coherence_penalties += trace_text.count("systemic coherence")
        
        # Simple ASCII Bar representation for Net Impact
        impact_percent = (total_penalties / total_base) * 100 if total_base > 0 else 0
        bar = "█" * int(impact_percent / 2)
        
        # Display to logger
        logger.info(f"\n🏷️  Tier: {tier} ({len(reports)} targets)")
        logger.info(f"   Overall Average Final Score: {avg_final:.1f}/5.0")
        logger.info(f"   Total Criteria Evaluated:     {len(tier_rows)}")
        logger.info(f"   --- Phase 3 Tracking ---")
        logger.info(f"   Citation Hallucinations Pruned: {hallucination_prunes}")
        logger.info(f"   Variance Re-evaluations:        {variance_prunes}")
        logger.info(f"   Security Overrides Fired:       {security_overrides}")
        logger.info(f"   Systemic Coherence Caps:        {coherence_penalties}")
        logger.info(f"   Total Contradictions Caught:    {contradictions_found}")
        logger.info(f"   ------------------------")
        logger.info(f"   Cumulative Base Score:        {total_base}")
        logger.info(f"   Cumulative Penalty Applied:  -{total_penalties}")
        logger.info(f"   Cumulative Final Score:       {total_final}")
        logger.info(f"   Penalty Impact: [{bar:<25}] {impact_percent:.1f}% reduction")
        
        # Append to markdown
        md_content += f"## Tier: {tier} ({len(reports)} targets)\n"
        md_content += f"- **Overall Average Final Score**: {avg_final:.1f}/5.0\n"
        md_content += f"- **Total Criteria Evaluated**: {len(tier_rows)}\n"
        md_content += f"- **Total Contradictions Caught**: {contradictions_found}\n"
        md_content += f"- **Citation Hallucinations Pruned**: {hallucination_prunes}\n"
        md_content += f"- **Variance Re-evaluations**: {variance_prunes}\n"
        md_content += f"- **Systemic Coherence Caps**: {coherence_penalties}\n"
        md_content += f"- **Cumulative Base Score**: {total_base}\n"
        md_content += f"- **Cumulative Penalty Applied**: -{total_penalties}\n"
        md_content += f"- **Cumulative Final Score**: {total_final}\n"
        md_content += f"```text\nPenalty Impact: [{bar:<25}] {impact_percent:.1f}% reduction\n```\n\n"
        
    logger.info("\nDone. If Medium/High tiers show >15% reduction, consider softening the Rule of Contradiction.")
    logger.info("="*60 + "\n")
    
    with open("benchmark_report.md", "w") as f:
        f.write(md_content)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
