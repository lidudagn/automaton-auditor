"""Tests for the multi-run benchmark orchestrator suite."""

import pytest
from src.state import AgentState, AuditReport, CriterionResult

# We will test the metrics calculation portion of the benchmark script.
from src.benchmark import generate_calibration_curves

class MockCriterion:
    def __init__(self):
        self.reasoning_trace = []

class MockReport:
    def __init__(self, overall_score):
        self.overall_score = overall_score
        self.criteria = [MockCriterion()]

def test_generate_calibration_curves_logic(caplog):
    """Test the calculation and formatting output logic implicitly by reading logs."""
    import logging
    
    with caplog.at_level(logging.INFO):
        tier_stats = {
            "High": [MockReport(4.5), MockReport(5.0)]
        }
        
        all_results = [
            {"target_id": "t1", "expected_tier": "High", "dimension_id": "test1", "base_score": 5, "penalty_applied": 0, "final_score": 5, "contradiction_flag": False},
            {"target_id": "t1", "expected_tier": "High", "dimension_id": "test2", "base_score": 5, "penalty_applied": 2, "final_score": 3, "contradiction_flag": True},
            {"target_id": "t2", "expected_tier": "High", "dimension_id": "test1", "base_score": 4, "penalty_applied": 0, "final_score": 4, "contradiction_flag": False},
        ]
        
        generate_calibration_curves(tier_stats, all_results)
        
        output = caplog.text
        
        assert "CALIBRATION SCORING CURVES" in output
        assert "Tier: High (2 targets)" in output
        assert "Overall Average Final Score: 4.8/5.0" in output
        assert "Total Criteria Evaluated:     3" in output
        assert "Total Contradictions Caught:    1" in output
        assert "Cumulative Base Score:        14" in output
        assert "Cumulative Penalty Applied:  -2" in output
        assert "Cumulative Final Score:       12" in output
        # Total Base: 14. Penalty: 2. 2/14 = 14.28% ~ 14.3%
        assert "14.3% reduction" in output
    assert "Tier: High (2 targets)" in output
    assert "Overall Average Final Score: 4.8/5.0" in output
    assert "Total Criteria Evaluated:     3" in output
    assert "Total Contradictions Caught:    1" in output
    assert "Cumulative Base Score:        14" in output
    assert "Cumulative Penalty Applied:  -2" in output
    assert "Cumulative Final Score:       12" in output
    # Total Base: 14. Penalty: 2. 2/14 = 14.28% ~ 14.3%
    assert "14.3% reduction" in output
