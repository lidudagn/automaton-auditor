import unittest
from datetime import datetime
from src.state import MetaAuditState, AuditRun, EvidenceRecord, JudicialOpinion
from src.nodes.meta_audit import MetaAuditNode

class TestMetaAuditLogic(unittest.TestCase):
    def setUp(self):
        self.meta_node = MetaAuditNode()
        
        # Mock Evidence Records
        self.stable_ev = EvidenceRecord(
            id="ev_stable",
            source="repo",
            artifact_path="src/core.py",
            claim_reference="graph_orchestration",
            exists=True
        )
        
        self.transient_ev = EvidenceRecord(
            id="ev_transient",
            source="repo",
            artifact_path="random_file.py",
            claim_reference="state_management",
            exists=True
        )

    def test_meta_aggregation_and_stability(self):
        """Verify that MetaAuditNode correctly identifies stable vs transient evidence."""
        # Run 1: Both exist
        run1 = AuditRun(
            run_id=1,
            overall_score=4.0,
            opinions=[
                JudicialOpinion(judge="TechLead", criterion_id="graph_orchestration", score=5, argument="Solid")
            ],
            registry_state={"ev_stable": self.stable_ev, "ev_transient": self.transient_ev}
        )
        
        # Run 2: Only stable exists
        run2 = AuditRun(
            run_id=2,
            overall_score=3.5,
            opinions=[
                JudicialOpinion(judge="TechLead", criterion_id="graph_orchestration", score=4, argument="Good")
            ],
            registry_state={"ev_stable": self.stable_ev}
        )
        
        state = MetaAuditState(repo_url="test_repo", runs=[run1, run2])
        result = self.meta_node(state)
        
        meta_reg = result["meta_registry"]
        
        # Verify stability scores
        # Key in meta_registry is "path:goal"
        stable_key = "src/core.py:graph_orchestration"
        transient_key = "random_file.py:state_management"
        
        self.assertEqual(meta_reg[stable_key].stability_score, 1.0)
        self.assertEqual(meta_reg[transient_key].stability_score, 0.5)
        
        # Verify meta-scores (graph_orchestration average of 5 and 4 = 4.5)
        # However, Phase 5 Meta-Override boosts 4.5 to 5.0 because stability is 1.0
        self.assertEqual(result["meta_scores"]["graph_orchestration"], 5.0)

    def test_cross_run_contradiction_detection(self):
        """Verify that large score jumps across runs are detected."""
        run1 = AuditRun(
            run_id=1,
            overall_score=5.0,
            opinions=[
                JudicialOpinion(judge="Prosecutor", criterion_id="security", score=5, argument="Perfect")
            ],
            registry_state={}
        )
        
        run2 = AuditRun(
            run_id=2,
            overall_score=1.0,
            opinions=[
                JudicialOpinion(judge="Prosecutor", criterion_id="security", score=1, argument="Critical Flaw")
            ],
            registry_state={}
        )
        
        state = MetaAuditState(repo_url="test_repo", runs=[run1, run2])
        result = self.meta_node(state)
        
        # Check if the jump (5-1=4) was flagged in reasoning trace
        trace_text = " ".join(result["reasoning_trace"])
        self.assertIn("CRITICAL", trace_text)
        self.assertIn("score jump (Δ4)", trace_text)

    def test_meta_override_justice(self):
        """Verify that Chief Justice correctly boosts or penalizes based on stability."""
        # Setup state with a meta-score and specific evidence stability
        state = MetaAuditState(
            repo_url="test_repo",
            meta_scores={"architecture": 4.5, "unstable_feat": 4.0},
            meta_registry={
                "stable": EvidenceRecord(id="1", source="repo", artifact_path="p", claim_reference="architecture", exists=True, stability_score=1.0),
                "unstable": EvidenceRecord(id="2", source="repo", artifact_path="p2", claim_reference="unstable_feat", exists=True, stability_score=0.4)
            }
        )
        
        # Call meta_override via the node's internal chief_justice or directly
        scores, trace = self.meta_node.chief_justice.meta_override(
            state.meta_scores,
            state.meta_registry,
            []
        )
        
        # Architecture should be boosted to 5.0 (stability 1.0 + score >= 4)
        self.assertEqual(scores["architecture"], 5.0)
        
        # Unstable_feat should be penalized (stability 0.4 < 0.5)
        self.assertLess(scores["unstable_feat"], 4.0)

if __name__ == "__main__":
    unittest.main()
