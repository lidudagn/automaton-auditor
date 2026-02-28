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

    def _apply_calibrated_override(self, max_confidence: float, criterion_id: str, remediation: str, dissent_summary: str, reasoning_trace: List[str]) -> tuple[int, str, str, str, List[str]]:
        """
        Step 1: Calibrated Override (Phase 3).
        Graduated penalty based on evidence confidence.
        Returns: (score_override, status, remediation, dissent, trace)
        """
        if max_confidence < 0.3:
            logger.info(f"  🚨 CALIBRATED OVERRIDE: Heavy penalty for {criterion_id} (Confidence: {max_confidence:.2f})")
            remediation = f"CRITICAL MISSING COMPONENT: No tangible artifacts found matching {criterion_id}."
            dissent_summary = "Overruled judges; confidence threshold not met for architectural claims."
            reasoning_trace.append(f"Calibrated Override Triggered: Heavy penalty (Score 1) due to low evidence confidence ({max_confidence:.2f}).")
            return 1, "OVERRIDE_HEAVY", remediation, dissent_summary, reasoning_trace
        
        if max_confidence < 0.7:
            logger.info(f"  ⚠️ CALIBRATED OVERRIDE: Moderate penalty for {criterion_id} (Confidence: {max_confidence:.2f})")
            remediation = f"GENERIC IMPLEMENTATION: Only basic signals found for {criterion_id}. Lacks advanced architectural patterns."
            reasoning_trace.append(f"Calibrated Override Triggered: Moderate penalty (Cap 2) due to mid-range evidence confidence ({max_confidence:.2f}).")
            return 2, "OVERRIDE_MODERATE", remediation, dissent_summary, reasoning_trace
            
        reasoning_trace.append(f"Calibrated Override Passed: Sufficient evidence confidence ({max_confidence:.2f}).")
        return None, "PASSED", remediation, dissent_summary, reasoning_trace

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

    def _perform_variance_arbitration(self, scores: Dict[str, int], arguments: Dict[str, str], max_confidence: float, dissent_summary: str, reasoning_trace: List[str]) -> tuple[List[str], str, List[str]]:
        """Step 3: Variance Arbitration - Prune factual outliers with sensitivity delta."""
        valid_judges = ["Prosecutor", "Defense", "TechLead"]
        max_score = max(scores.values())
        min_score = min(scores.values())
        variance = max_score - min_score
        
        if variance > 1.5:
            logger.warning(f"  ⚠️ HIGH VARIANCE DETECTED (Δ{variance}): Resolving judge disagreement.")
            dissent_summary = (
                f"Judicial disagreement observed (Δ{variance}).\n"
                f"Explanation: Chief Justice arbitrating based on architectural evidence context."
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
            
            if outlier_judge and max_dev > 1:
                outlier_score = scores[outlier_judge]
                # Cross-reference with confidence
                if outlier_score > 3 and max_confidence < 0.4:
                    logger.info(f"  ❌ PRUNING HIGH OUTLIER ({outlier_judge}): Score {outlier_score} lacks confidence {max_confidence}.")
                    valid_judges.remove(outlier_judge)
                    reasoning_trace.append(f"Variance Arbitration: Pruned high outlier '{outlier_judge}' ({outlier_score}) due to low evidence confidence ({max_confidence:.2f}).")
                elif outlier_score < 2 and max_confidence > 0.7:
                    logger.info(f"  ❌ PRUNING LOW OUTLIER ({outlier_judge}): Score {outlier_score} ignores high confidence {max_confidence}.")
                    valid_judges.remove(outlier_judge)
                    reasoning_trace.append(f"Variance Arbitration: Pruned low outlier '{outlier_judge}' ({outlier_score}) despite high evidence confidence ({max_confidence:.2f}).")
                else:
                    reasoning_trace.append(f"Variance Arbitration: Outlier '{outlier_judge}' ({outlier_score}) kept within calibrated bounds.")
        else:
            reasoning_trace.append(f"Variance Arbitration Passed: Variance (Δ{variance}) within stable limits.")

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
                cited_evidences[op.judge] = getattr(op, "cited_evidence_ids", [])
                logger.info(f"  [{op.judge}] {op.score}/5 - {op.argument[:70]}...")
            
            # Gather evidence facts and max confidence for this criterion
            evidence_found_count = 0
            evidence_missing_count = 0
            max_confidence = 0.0
            for det, ev_list in state.evidences.items():
                for ev in ev_list:
                    if (criterion_id.lower() in ev.goal.lower() or 
                        any(word in ev.goal.lower() for word in criterion_id.lower().split('_'))):
                        if ev.found:
                            evidence_found_count += 1
                            max_confidence = max(max_confidence, ev.confidence)
                        else:
                            evidence_missing_count += 1

            valid_judges = ["Prosecutor", "Defense", "TechLead"]
            dissent_summary = None
            remediation = "Continue tracking."
            reasoning_trace = []
            
            # Step 0: Citation Validation (Hallucination Guard)
            for judge in list(valid_judges):
                citations = cited_evidences.get(judge, [])
                for cit in citations:
                    if not state.registry.exists(cit):
                        logger.info(f"  ❌ PRUNING JUDGE ({judge}): Hallucinated citation ID '{cit}'.")
                        valid_judges.remove(judge)
                        reasoning_trace.append(f"Citation Validation: Judge {judge} pruned due to invalid citation: {cit}.")
                        break
            
            # Step 1: Calibrated Override (Architectural Governance)
            override_score, status, remediation, dissent_summary, reasoning_trace = self._apply_calibrated_override(
                max_confidence, criterion_id, remediation, dissent_summary, reasoning_trace
            )
            
            # Step 2: Security Override
            sec_score, sec_remediation, reasoning_trace = self._apply_security_override(
                criterion_id, scores, remediation, reasoning_trace
            )
            
            if status == "OVERRIDE_HEAVY":
                final_score = override_score
            elif sec_score is not None:
                final_score = sec_score
                remediation = sec_remediation
            else:
                # Step 3: Variance Arbitration
                valid_judges, dissent_summary, reasoning_trace = self._perform_variance_arbitration(
                    scores, arguments, max_confidence, dissent_summary, reasoning_trace
                )
                
                # Step 4 & 5: Functionality Weight or Median Stabilization
                final_score, reasoning_trace = self._apply_functionality_weight_and_median(
                    criterion_id, scores, valid_judges, reasoning_trace
                )
                
                # If moderate override, cap the score
                if status == "OVERRIDE_MODERATE":
                    final_score = min(final_score, override_score)
            
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
            
        # --- Step 7: Cross-Criterion Coherence Guards (Phase 3 Systemic Intelligence) ---
        # Map criteria by ID for quick lookup
        crit_map = {c.dimension_id.lower(): c for c in final_criteria_results}
        
        # 1. Architecture high but state management low
        arch_crit = next((c for c in final_criteria_results if "architecture" in c.dimension_id.lower()), None)
        state_crit = next((c for c in final_criteria_results if "state" in c.dimension_id.lower()), None)
        if arch_crit and state_crit and arch_crit.final_score >= 4 and state_crit.final_score <= 2:
            logger.info("  🧠 SYSTEMIC COHERENCE: Penalizing Architecture due to poor state management.")
            arch_crit.final_score -= 1
            arch_crit.reasoning_trace.append("Systemic Coherence Penalty: Architecture score reduced by 1 because State Management validation failed downstream.")
            global_contradictions.append("Systemic Incoherence: High abstraction (Architecture) built on failing foundation (State Management).")

        # 2. Testing missing but overall > 4 context (simplified to: if testing is 1, no other score can be 5)
        test_crit = next((c for c in final_criteria_results if "test" in c.dimension_id.lower()), None)
        if test_crit and test_crit.final_score == 1:
            for c in final_criteria_results:
                if c.final_score == 5 and c.dimension_id != test_crit.dimension_id:
                    logger.info(f"  🧠 SYSTEMIC COHERENCE: Capping {c.dimension_id} at 4 because testing is entirely missing.")
                    c.final_score = 4
                    c.reasoning_trace.append("Systemic Coherence Cap: Score capped at 4. Perfection (5) cannot be claimed without verifiable tests.")
                    
        # Generate Final Audit Report
        overall_score_sum = sum(c.final_score for c in final_criteria_results)
        overall_avg = overall_score_sum / len(final_criteria_results) if final_criteria_results else 0.0
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

    def meta_override(self, meta_scores: Dict[str, float], meta_registry: Dict[str, Any], reasoning_trace: List[str]) -> tuple[Dict[str, float], List[str]]:
        """
        Step 8: Meta-Audit Override (Phase 5).
        Adjusts scores based on multi-run evidence stability.
        """
        logger.info("  🧠 PHASE 5 MASTER AUDITOR: Applying Meta-Audit Overrides.")
        adjusted_scores = meta_scores.copy()
        
        for crit_id, score in adjusted_scores.items():
            # Check for low stability evidence that might have inflated the score
            relevant_evidence = [
                ev for ev in meta_registry.values()
                if ev.claim_reference and crit_id.lower() in ev.claim_reference.lower()
            ]
            
            if relevant_evidence:
                avg_stability = sum(ev.stability_score for ev in relevant_evidence) / len(relevant_evidence)
                if avg_stability < 0.7:
                    logger.warning(f"  ⚠️ SYSTEMIC UNCERTAINTY: Penalizing {crit_id} due to unstable evidence (Stability: {avg_stability:.2f})")
                    penalty = 0.5 if avg_stability < 0.5 else 0.2
                    adjusted_scores[crit_id] = max(1.0, score - penalty)
                    reasoning_trace.append(f"Meta-Override Applied: Penalized {crit_id} by {penalty} due to low evidence stability ({avg_stability:.2f}).")
                elif avg_stability == 1.0 and score >= 4.0:
                    logger.info(f"  💎 SYSTEMIC CONFIDENCE: Boosting {crit_id} to 5.0 due to perfect evidence stability.")
                    adjusted_scores[crit_id] = 5.0
                    reasoning_trace.append(f"Meta-Override Applied: Boosted {crit_id} to 5.0 due to 100% evidence stability across all runs.")

        return adjusted_scores, reasoning_trace
