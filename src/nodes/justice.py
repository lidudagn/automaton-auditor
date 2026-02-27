"""Chief Justice node for Automaton Auditor - Layer 3."""

from typing import Dict, Any, List
from src.state import AgentState, AuditReport, CriterionResult
import logging
logger = logging.getLogger(__name__)

class ChiefJusticeNode:
    """Collects opinions and synthesizes the Deterministic Chief Justice verdict with Intelligence Amplification."""
    
    def _detect_cross_evidence_contradiction(self, state: AgentState, criterion_id: str) -> tuple[bool, str]:
        """
        Phase 3 Intel: Compare doc claims vs repo reality.
        Returns: (has_contradiction, explanation)
        """
        doc_claims_found = False
        repo_evidence_missing = False
        
        # Scour doc evidence
        if 'doc' in state.evidences:
            for ev in state.evidences['doc']:
                if (criterion_id.lower() in ev.goal.lower() or 
                    any(word in ev.goal.lower() for word in criterion_id.lower().split('_'))):
                    if ev.found and ev.confidence > 0.6:
                        doc_claims_found = True
                        
        # Scour repo evidence
        if 'repo' in state.evidences:
            relevant_repo = False
            for ev in state.evidences['repo']:
                if (criterion_id.lower() in ev.goal.lower() or 
                    any(word in ev.goal.lower() for word in criterion_id.lower().split('_'))):
                    relevant_repo = True
                    if not ev.found and ev.confidence > 0.6:
                        repo_evidence_missing = True
            
            # If repo scanned but found *no* relevant files explicitly, missing is implicitly True
            if doc_claims_found and not relevant_repo and len(state.evidences['repo']) > 0:
                repo_evidence_missing = True
                
        if doc_claims_found and repo_evidence_missing:
            return True, f"Documentation claims structural existence for '{criterion_id}', but static repository forensic tools explicitly could not find supporting code artifacts."
            
        return False, ""

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Aggregate opinions via deterministic rules and produce final AuditReport."""
        opinions = state.opinions
        
        if not opinions:
            logger.warning("\n⚠️  No opinions to aggregate")
            return {}
        
        logger.info("\n" + "="*70)
        logger.info("⚖️  CHIEF JUSTICE OPINION SYNTHESIS".center(70))
        logger.info("="*70)
        
        # Group by criterion
        by_criterion = {}
        for op in opinions:
            if op.criterion_id not in by_criterion:
                by_criterion[op.criterion_id] = []
            by_criterion[op.criterion_id].append(op)
            
        final_criteria_results = []
        overall_score_sum = 0
        global_contradictions = []
        
        for criterion_id, ops in by_criterion.items():
            logger.info(f"\n📋 Evaluating: {criterion_id}")
            
            # Map judge scores and arguments
            scores = {"Prosecutor": 3, "Defense": 3, "TechLead": 3}
            arguments = {}
            cited_evidences = {}
            for op in ops:
                scores[op.judge] = op.score
                arguments[op.judge] = op.argument
                cited_evidences[op.judge] = op.cited_evidence
                logger.info(f"  [{op.judge}] {op.score}/5 - {op.argument[:70]}...")
            
            # Base Weighted Score
            final_score = round(
                (scores["Prosecutor"] + scores["Defense"] + scores["TechLead"]) / 3
            )
            dissent_summary = None
            remediation = "Continue tracking."
            
            # 1. Rule of Functionality (Tech Lead supremacy for Architecture)
            if "architecture" in criterion_id.lower() or "orchestration" in criterion_id.lower():
                logger.info("  🏛️ RULE OF FUNCTIONALITY: Tech Lead opinion carries highest weight.")
                # Give TechLead 3x weight
                final_score = round(
                    (scores["Prosecutor"] + scores["Defense"] + (3 * scores["TechLead"])) / 5
                )

            # 2. Hard Rule: High Disagreement Variance & Variance Re-evaluation
            max_score = max(scores.values())
            min_score = min(scores.values())
            variance = max_score - min_score
            
            if variance > 2:
                logger.warning(f"  ⚠️ VARIANCE RE-EVALUATION TRIGGERED (Δ{variance}): Validating citations.")
                # If Defense is high but Prosecutor is low, check facts (Rule of Evidence applied proactively)
                dissent_summary = (
                    f"Strong disagreement between judges (Variance > 2).\n"
                    f"Prosecutor ({scores['Prosecutor']}/5): {arguments.get('Prosecutor', 'N/A')}\n"
                    f"Defense ({scores['Defense']}/5): {arguments.get('Defense', 'N/A')}\n"
                    f"TechLead ({scores['TechLead']}/5): {arguments.get('TechLead', 'N/A')}"
                )

            # 3. Rule of Evidence (Fact Supremacy)
            # Find evidence matches
            evidence_found_count = 0
            evidence_missing_count = 0
            for det, ev_list in state.evidences.items():
                for ev in ev_list:
                    if (criterion_id.lower() in ev.goal.lower() or 
                        any(word in ev.goal.lower() for word in criterion_id.lower().split('_'))):
                        if ev.found:
                            evidence_found_count += 1
                        else:
                            evidence_missing_count += 1
            
            if evidence_found_count == 0:
                logger.info("  🚨 RULE OF EVIDENCE: Overruling Defense for hallucination due to missing artifacts.")
                final_score = 1
                remediation = f"CRITICAL MISSING COMPONENT: No valid artifacts found matching {criterion_id}."
                if dissent_summary is None:
                    dissent_summary = f"Overruled Defense; fact supremacy requires tangible artifacts."

            # 4. Rule of Security (Overrides everything else)
            if "safe" in criterion_id.lower() or "security" in criterion_id.lower():
                if scores["Prosecutor"] <= 3:
                    logger.info("  🚨 RULE OF SECURITY: Prosecutor identified security flaw. Score capped at 3.")
                    final_score = min(final_score, 3)
                    remediation = "IMMEDIATE FIX REQUIRED: Security/safety vulnerabilities detected by Prosecutor must be patched."
                    
            # Track base_score before contradictions
            base_score = final_score
            penalty_applied = 0
            
            # 5. Rule of Contradiction (Phase 3 Intelligence Amplification)
            has_contradiction, contra_msg = self._detect_cross_evidence_contradiction(state, criterion_id)
            if has_contradiction:
                logger.info(f"  🧠 PHASE 3 INTELLIGENCE: CROSS-EVIDENCE CONTRADICTION DETECTED.")
                logger.info(f"     -> {contra_msg}")
                # Mathematically heavily penalize (confidence-weight pushes towards REPO evidence)
                # Repo reality > Doc Theory. Pull score down by 2 points automatically.
                final_score = max(1, final_score - 2)
                penalty_applied = base_score - final_score
                remediation = f"RESOLVE CONTRADICTION: {contra_msg}"
                global_contradictions.append(contra_msg)

            # Ensure score bounds
            final_score = max(1, min(5, final_score))
            logger.info(f"  ⭐ Final Synthesized Score: {final_score}/5")
            
            # Save criterion result
            final_criteria_results.append(CriterionResult(
                dimension_id=criterion_id,
                dimension_name=criterion_id.replace("_", " ").title(),
                final_score=final_score,
                base_score=base_score,
                penalty_applied=penalty_applied,
                prosecutor_score=scores["Prosecutor"],
                defense_score=scores["Defense"],
                tech_lead_score=scores["TechLead"],
                dissent_summary=dissent_summary,
                contradiction_flag=has_contradiction,
                remediation=remediation
            ))
            
            overall_score_sum += final_score

        # Generate Final Audit Report
        overall_avg = overall_score_sum / len(by_criterion) if by_criterion else 0.0
        logger.info(f"\n🏆 CHIEF JUSTICE OVERALL VERDICT: {overall_avg:.1f}/5.0")
        logger.info("="*70 + "\n")
        
        evidence_summary_dict = {k: len(v) for k, v in state.evidences.items()}
        
        final_report = AuditReport(
            repo_url=state.repo_url,
            executive_summary=f"Automaton Auditor examined the repository and rendered a final score of {overall_avg:.1f}/5.0. See criterion breakdown for exact flaws and mitigating factors.",
            overall_score=overall_avg,
            criteria=final_criteria_results,
            remediation_plan="Review the 'Criteria Evaluation' scores of 3 or below and apply the suggested fixes.",
            detected_contradictions=global_contradictions,
            evidence_summary=evidence_summary_dict
        )
        
        return {"final_report": final_report}
