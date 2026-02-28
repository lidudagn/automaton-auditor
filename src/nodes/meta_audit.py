"""Meta-Audit Node for Automaton Auditor - Phase 5."""

import logging
from typing import List, Dict, Any
from collections import defaultdict
from src.state import MetaAuditState, AuditRun, EvidenceRecord, JudicialOpinion
from src.nodes.justice import ChiefJusticeNode

logger = logging.getLogger(__name__)

class MetaAuditNode:
    """Consolidates multiple deterministic runs into a master audit report."""
    
    def __init__(self):
        self.chief_justice = ChiefJusticeNode()
    
    def __call__(self, state: MetaAuditState) -> Dict[str, Any]:
        logger.info("⚖️  MetaAudit: Aggregating multi-run evidence and scores...")
        
        if not state.runs:
            logger.warning("⚠️ No runs found to aggregate.")
            return {}

        # 1. Consolidate Evidence & Calculate Stability
        self._consolidate_evidence(state)
        
        # 2. Analyze Score Variance & Detect Contradictions
        self._detect_cross_run_contradictions(state)
        
        # 3. Apply Multi-Run Consensus Normalization
        self._normalize_consensus_scores(state)

        # 3.5 Apply Chief Justice Meta-Overrides (Phase 5 Super-Guardrails)
        state.meta_scores, state.reasoning_trace = self.chief_justice.meta_override(
            state.meta_scores, 
            state.meta_registry, 
            state.reasoning_trace
        )
        
        # 4. Final Metatrace
        state.reasoning_trace.append(f"Meta-Audit complete across {len(state.runs)} runs.")
        
        return {
            "meta_registry": state.meta_registry,
            "meta_scores": state.meta_scores,
            "reasoning_trace": state.reasoning_trace
        }

    def _consolidate_evidence(self, state: MetaAuditState):
        """Build MetaEvidenceRegistry and calculate stability scores."""
        evidence_counts = defaultdict(int)
        all_evidence: Dict[str, EvidenceRecord] = {}
        
        num_runs = len(state.runs)
        
        for run in state.runs:
            for ev_id, record in run.registry_state.items():
                # We identify "same" evidence by artifact_path and claim_reference
                # since IDs might change across runs if uuid is used.
                # However, for now we assume consistent IDs if seeded correctly.
                key = f"{record.artifact_path}:{record.claim_reference}"
                evidence_counts[key] += 1
                
                if key not in all_evidence:
                    all_evidence[key] = record.model_copy()
                    all_evidence[key].seen_in_runs = []
                
                all_evidence[key].seen_in_runs.append(run.run_id)

        # Calculate stability scores
        for key, record in all_evidence.items():
            record.stability_score = evidence_counts[key] / num_runs
            state.meta_registry[key] = record
            
            if record.stability_score < 0.6:
                logger.warning(f"  ⚠️ Transient Evidence Detected: {record.claim_reference} (Stability: {record.stability_score})")
                state.reasoning_trace.append(f"Flagged transient evidence: {record.claim_reference} ({record.stability_score})")

    def _detect_cross_run_contradictions(self, state: MetaAuditState):
        """Detect jump in scores or disappearing evidence across runs."""
        judge_scores = defaultdict(lambda: defaultdict(list)) # judge -> criterion -> scores
        
        for run in state.runs:
            for opinion in run.opinions:
                judge_scores[opinion.judge][opinion.criterion_id].append(opinion.score)

        for judge, criteria in judge_scores.items():
            for criterion_id, scores in criteria.items():
                if not scores: continue
                
                max_score = max(scores)
                min_score = min(scores)
                variance = max_score - min_score
                
                if variance > 1.5:
                    msg = f"CRITICAL: {judge} score jump (Δ{variance}) for {criterion_id} across runs."
                    logger.error(f"  ❌ {msg}")
                    state.reasoning_trace.append(msg)

    def _normalize_consensus_scores(self, state: MetaAuditState):
        """Compute weighted meta-scores based on evidence stability."""
        criterion_scores = defaultdict(list)
        
        for run in state.runs:
            # Group scores by criterion
            run_criterion_scores = defaultdict(list)
            for op in run.opinions:
                run_criterion_scores[op.criterion_id].append(op.score)
            
            # Simple average for this run's criterion (could use Chief Justice logic here)
            for crit_id, scores in run_criterion_scores.items():
                run_avg = sum(scores) / len(scores)
                criterion_scores[crit_id].append(run_avg)

        # Final meta-normalization
        for crit_id, meta_scores in criterion_scores.items():
            # Apply stability weighting
            # If evidence for this criterion is unstable, we penalize the meta-score
            stability_buffer = self._get_criterion_stability(state, crit_id)
            
            raw_meta_score = sum(meta_scores) / len(meta_scores)
            final_normalized = raw_meta_score * stability_buffer
            
            state.meta_scores[crit_id] = round(final_normalized, 2)
            state.reasoning_trace.append(f"Meta-score for {crit_id}: {state.meta_scores[crit_id]} (Stability: {stability_buffer})")

    def _get_criterion_stability(self, state: MetaAuditState, criterion_id: str) -> float:
        """Calculate aggregate stability for all evidence linked to a criterion."""
        relevant_stability = [
            ev.stability_score for ev in state.meta_registry.values()
            if ev.claim_reference and criterion_id.lower() in ev.claim_reference.lower()
        ]
        
        if not relevant_stability:
            return 1.0 # default to stable if no evidence found (Fact Supremacy will catch 0s)
            
        return sum(relevant_stability) / len(relevant_stability)
