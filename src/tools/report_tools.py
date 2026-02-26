import re
from src.state import AuditReport

def generate_markdown_report(report: AuditReport) -> str:
    """Generate a cleanly formatted markdown report from the AuditReport object."""
    md = [
        f"# Automaton Auditor Final Report",
        f"**Repository Under Audit:** [{report.repo_url}]({report.repo_url})",
        f"**Audit Date:** {report.audit_date.strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n## Executive Summary",
        f"**Overall Score:** {report.overall_score:.1f}/5.0",
        f"\n**Evidence Collected Summary:**"
    ]
    
    for detector, count in report.evidence_summary.items():
        md.append(f"- **{detector.upper()}**: {count} items")
        
    md.append(f"\n{report.executive_summary}\n")
    md.append(f"## Criteria Evaluation\n")
    
    for crit in report.criteria:
        md.append(f"### {crit.dimension_name}")
        md.append(f"**Final Score:** {crit.final_score}/5")
        md.append(f"- **Prosecutor Score:** {crit.prosecutor_score}/5")
        md.append(f"- **Defense Score:** {crit.defense_score}/5")
        md.append(f"- **TechLead Score:** {crit.tech_lead_score}/5")
        
        if crit.dissent_summary:
            md.append(f"\n> [!WARNING] High Judge Disagreement")
            md.append(f"> {crit.dissent_summary}")
            
        if crit.remediation:
            md.append(f"\n**Remediation Action:**")
            md.append(f"{crit.remediation}\n")
            
        md.append("---")
        
    md.append(f"\n## Final Remediation Plan\n")
    md.append(f"{report.remediation_plan}")
    
    return "\n".join(md)
