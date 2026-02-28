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

    def _apply_fact_supremacy(self, evidence_found_count: int, criterion_id: str, remediation: str, dissent_summary: str, reasoning_trace: List[str]) -> tuple[int, str, str, bool, List[str]]:
        """Step 1: Fact Supremacy - Absolute reality layer."""
        if evidence_found_count == 0:
            logger.info("  🚨 RULE OF EVIDENCE: Overruling Defense for hallucination due to missing artifacts.")
            remediation = f"CRITICAL MISSING COMPONENT: No valid artifacts found matching {criterion_id}."
            if dissent_summary is None:
                dissent_summary = f"Overruled Defense; fact supremacy requires tangible artifacts."
            reasoning_trace.append("Fact Supremacy Triggered: No evidence found. Score set to 1. Ignored all judges.")
            return 1, remediation, dissent_summary, True, reasoning_trace
        reasoning_trace.append("Fact Supremacy Passed: Evidence found.")
        return 0, remediation, dissent_summary, False, reasoning_trace

    def _apply_security_override(self, criterion_id: str, scores: Dict[str, int], remediation: str, reasoning_trace: List[str]) -> tuple[int, str, List[str]] | tuple[None, str, List[str]]:
        """Step 2: Security Override."""
        if "safe" in criterion_id.lower() or "security" in criterion_id.lower():
            if scores["Prosecutor"] <= 3:
                logger.info("  🚨 RULE OF SECURITY: Prosecutor identified security flaw. Score capped at 3.")
                remediation = "IMMEDIATE FIX REQUIRED: Security/safety vulnerabilities detected by Prosecutor must be patched."
                reasoning_trace.append(f"Security Override Triggered: Prosecutor score ({scores['Prosecutor']}) capped final score at 3.")
                return min(scores["TechLead"], 3), remediation, reasoning_trace # Use techlead as base but cap
            reasoning_trace.append("Security Override Passed: Prosecutor did not identify safety flaws.")
        return None, remediation, reasoning_trace

    def _perform_variance_arbitration(self, scores: Dict[str, int], arguments: Dict[str, str], evidence_found_count: int, dissent_summary: str, reasoning_trace: List[str]) -> tuple[List[str], str, List[str]]:
        """Step 3: Variance Arbitration - Prune factual outliers."""
        valid_judges = ["Prosecutor", "Defense", "TechLead"]
        max_score = max(scores.values())
        min_score = min(scores.values())
        variance = max_score - min_score
        
        if variance > 2:
            logger.warning(f"  ⚠️ VARIANCE RE-EVALUATION TRIGGERED (Δ{variance}): Validating citations.")
            dissent_summary = (
                f"Strong disagreement between judges (Variance > 2).\n"
                f"Prosecutor ({scores['Prosecutor']}/5): {arguments.get('Prosecutor', 'N/A')}\n"
                f"Defense ({scores['Defense']}/5): {arguments.get('Defense', 'N/A')}\n"
                f"TechLead ({scores['TechLead']}/5): {arguments.get('TechLead', 'N/A')}"
            )
            
            # Find median
            sorted_scores = sorted(scores.values())
            median = sorted_scores[1]
            
            # Find extreme outlier (largest absolute deviation)
            outlier_judge = None
            max_dev = -1
            for judge, score in scores.items():
                dev = abs(score - median)
                if dev > max_dev:
                    max_dev = dev
                    outlier_judge = judge
            
            if outlier_judge and max_dev > 1: # Only prune if clearly an outlier
                outlier_score = scores[outlier_judge]
                # Fact check extreme outlier
                if outlier_score > 2 and evidence_found_count == 0:
                    logger.info(f"  ❌ INVALIDATING OUTLIER ({outlier_judge}): Ignored missing factual evidence.")
                    valid_judges.remove(outlier_judge)
                    reasoning_trace.append(f"Variance Arbitration Triggered: Invalidated extreme high outlier '{outlier_judge}' ({outlier_score}) conflicting with lack of factual evidence.")
                elif outlier_score <= 2 and evidence_found_count >= 1: # simple threshold for now
                    logger.info(f"  ❌ INVALIDATING OUTLIER ({outlier_judge}): Harshly scored despite solid factual evidence.")
                    valid_judges.remove(outlier_judge)
                    reasoning_trace.append(f"Variance Arbitration Triggered: Invalidated extreme low outlier '{outlier_judge}' ({outlier_score}) conflicting with confirmed factual evidence.")
                else:
                    reasoning_trace.append(f"Variance Arbitration Passed: Extreme outlier '{outlier_judge}' ({outlier_score}) not overtly contradicted by factual evidence.")
        else:
            reasoning_trace.append(f"Variance Arbitration Passed: Variance (Δ{variance}) within acceptable limits.")

        return valid_judges, dissent_summary, reasoning_trace

    def _apply_functionality_weight_and_median(self, criterion_id: str, scores: Dict[str, int], valid_judges: List[str], reasoning_trace: List[str]) -> tuple[int, List[str]]:
        """Step 4 & 5: Functionality Weighting or Median Stabilization."""
        if not valid_judges:
            reasoning_trace.append("Fallback: All judges pruned. Base score set to 1.")
            return 1, reasoning_trace # Fallback if all pruned
            
        if ("architecture" in criterion_id.lower() or "orchestration" in criterion_id.lower()) and "TechLead" in valid_judges:
            logger.info("  🏛️ RULE OF FUNCTIONALITY: Tech Lead opinion carries highest weight.")
            # Gather valid scores
            valid_scores = [scores[j] for j in valid_judges]
            
            # Apply 2x multiplier only for TechLead's *weight* in the average
            weighted_sum = 0
            total_weight = 0
            for j in valid_judges:
                if j == "TechLead":
                    weighted_sum += (2 * scores[j])
                    total_weight += 2
                else:
                    weighted_sum += scores[j]
                    total_weight += 1
                    
            final_score = round(weighted_sum / total_weight)
            reasoning_trace.append(f"Functionality Weighting Applied: 2x multiplier for TechLead. Final valid judges: {valid_judges}. Score: {final_score}")
            return final_score, reasoning_trace
            
        # Step 5: Median Stabilization
        valid_scores = [scores[j] for j in valid_judges]
        final_score = round(sum(valid_scores) / len(valid_scores))
        reasoning_trace.append(f"Median Stabilization Applied: Computed rounded mean of valid judges: {valid_judges}. Score: {final_score}")
        return final_score, reasoning_trace

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
            
            # Gather evidence facts for this criterion
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

            valid_judges = ["Prosecutor", "Defense", "TechLead"]
            dissent_summary = None
            remediation = "Continue tracking."
            reasoning_trace = []
            
            # Step 1: Fact Supremacy (Absolute Reality Layer)
            final_score, remediation, dissent_summary, stop_eval, reasoning_trace = self._apply_fact_supremacy(
                evidence_found_count, criterion_id, remediation, dissent_summary, reasoning_trace
            )
            
            if not stop_eval:
                # Step 2: Security Override
                sec_score, sec_remediation, reasoning_trace = self._apply_security_override(
                    criterion_id, scores, remediation, reasoning_trace
                )
                if sec_score is not None:
                    final_score = sec_score
                    remediation = sec_remediation
                
                # Step 3: Variance Arbitration
                valid_judges, dissent_summary, reasoning_trace = self._perform_variance_arbitration(
                    scores, arguments, evidence_found_count, dissent_summary, reasoning_trace
                )
                
                if sec_score is None:
                    # Step 4 & 5: Functionality Weight or Median Stabilization
                    final_score, reasoning_trace = self._apply_functionality_weight_and_median(
                        criterion_id, scores, valid_judges, reasoning_trace
                    )
            
            base_score = final_score
            penalty_applied = 0
            
            # Step 6: Global Rule of Contradiction (Phase 3 Intelligence Amplification)
            has_contradiction, contra_msg = self._detect_cross_evidence_contradiction(state, criterion_id)
            if has_contradiction:
                logger.info(f"  🧠 PHASE 3 INTELLIGENCE: CROSS-EVIDENCE CONTRADICTION DETECTED.")
                logger.info(f"     -> {contra_msg}")
                final_score = max(1, final_score - 2)
                reasoning_trace.append(f"Contradiction Penalty Applied: Deducted {base_score - final_score} points. -> {contra_msg}")
                penalty_applied = base_score - final_score
                remediation = f"RESOLVE CONTRADICTION: {contra_msg}"
                global_contradictions.append(contra_msg)
            
            final_score = max(1, min(5, final_score))
            reasoning_trace.append(f"Final Score Locked: {final_score}/5.")
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
                reasoning_trace=reasoning_trace,
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
