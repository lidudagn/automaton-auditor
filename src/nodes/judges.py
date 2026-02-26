"""Judge nodes for Automaton Auditor - Phase 2."""

from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.state import AgentState, JudicialOpinion, Evidence
from src.prompts.judge_prompts import (
    PROSECUTOR_PROMPT,
    DEFENSE_PROMPT,
    TECH_LEAD_PROMPT
)


class BaseJudgeNode:
    """Base class for all judge personas."""
    
    def __init__(self, judge_name: str, system_prompt: str):
        self.judge_name = judge_name
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Use structured output to enforce JudicialOpinion schema
        self.structured_llm = self.llm.with_structured_output(JudicialOpinion)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
Review the evidence for this rubric criterion:

CRITERION: {criterion_name}
CRITERION ID: {criterion_id}

EVIDENCE SUMMARY:
{evidence_summary}

You are the {judge_name}. Based on the evidence above, provide your JudicialOpinion.

Your opinion must include:
- judge: "{judge_name}"
- criterion_id: "{criterion_id}"
- score: 1-5 integer following your persona's guidelines
- argument: Detailed reasoning (2-3 sentences)
- cited_evidence: List of evidence goals you referenced

Return ONLY the JudicialOpinion object.
""")
        ])
        
        self.chain = self.prompt | self.structured_llm
    
    def _summarize_evidence(self, state: AgentState, criterion_id: str) -> str:
        """Create a summary of relevant evidence for the criterion."""
        summary = []
        
        for detector, ev_list in state.evidences.items():
            for ev in ev_list:
                # Check if evidence matches criterion
                if (criterion_id.lower() in ev.goal.lower() or 
                    any(word in ev.goal.lower() for word in criterion_id.lower().split('_'))):
                    
                    status = "✅ FOUND" if ev.found else "❌ MISSING"
                    summary.append(
                        f"[{detector.upper()}] {ev.goal}: {status}\n"
                        f"  Location: {ev.location}\n"
                        f"  Rationale: {ev.rationale}\n"
                        f"  Confidence: {ev.confidence*100:.0f}%\n"
                    )
        
        if not summary:
            # If no direct matches, show recent evidence
            for detector, ev_list in list(state.evidences.items())[:2]:
                for ev in ev_list[:2]:
                    summary.append(
                        f"[{detector.upper()}] {ev.goal}: {'✅' if ev.found else '❌'}\n"
                        f"  {ev.rationale[:100]}...\n"
                    )
        
        return "\n".join(summary) if summary else "No relevant evidence found."


class ProsecutorNode(BaseJudgeNode):
    """Prosecutor judge - harsh, critical."""
    
    def __init__(self):
        super().__init__("Prosecutor", PROSECUTOR_PROMPT)
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate evidence as Prosecutor."""
        print("⚖️  Prosecutor: Analyzing evidence...")
        
        # Get rubric dimensions from state or use defaults
        rubric_dims = state.rubric_dimensions
        if not rubric_dims:
            rubric_dims = [
                {"id": "git_forensic_analysis", "name": "Git Forensic Analysis"},
                {"id": "state_management_rigor", "name": "State Management Rigor"},
                {"id": "graph_orchestration", "name": "Graph Orchestration Architecture"},
                {"id": "safe_tool_engineering", "name": "Safe Tool Engineering"},
                {"id": "structured_output", "name": "Structured Output Enforcement"},
                {"id": "judicial_nuance", "name": "Judicial Nuance"},
                {"id": "theoretical_depth", "name": "Theoretical Depth"},
            ]
        
        opinions = []
        for dim in rubric_dims:
            criterion_id = dim.get("id", dim.get("name", "unknown"))
            criterion_name = dim.get("name", criterion_id)
            
            evidence_summary = self._summarize_evidence(state, criterion_id)
            
            try:
                opinion = self.chain.invoke({
                    "judge_name": self.judge_name,
                    "criterion_name": criterion_name,
                    "criterion_id": criterion_id,
                    "evidence_summary": evidence_summary
                })
                
                # Ensure timestamp is set
                opinion.timestamp = datetime.now()
                opinions.append(opinion)
                
                print(f"  → {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                print(f"  ❌ Error for {criterion_id}: {str(e)}")
                # Create fallback opinion
                fallback = JudicialOpinion(
                    judge="Prosecutor",
                    criterion_id=criterion_id,
                    score=1,
                    argument=f"Error evaluating: {str(e)}",
                    cited_evidence=[]
                )
                opinions.append(fallback)
        
        return {"opinions": opinions}


class DefenseNode(BaseJudgeNode):
    """Defense judge - forgiving, rewards effort."""
    
    def __init__(self):
        super().__init__("Defense", DEFENSE_PROMPT)
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate evidence as Defense."""
        print("🛡️  Defense: Analyzing evidence...")
        
        rubric_dims = state.rubric_dimensions
        if not rubric_dims:
            rubric_dims = [
                {"id": "git_forensic_analysis", "name": "Git Forensic Analysis"},
                {"id": "state_management_rigor", "name": "State Management Rigor"},
                {"id": "graph_orchestration", "name": "Graph Orchestration Architecture"},
                {"id": "safe_tool_engineering", "name": "Safe Tool Engineering"},
                {"id": "structured_output", "name": "Structured Output Enforcement"},
                {"id": "judicial_nuance", "name": "Judicial Nuance"},
                {"id": "theoretical_depth", "name": "Theoretical Depth"},
            ]
        
        opinions = []
        for dim in rubric_dims:
            criterion_id = dim.get("id", dim.get("name", "unknown"))
            criterion_name = dim.get("name", criterion_id)
            
            evidence_summary = self._summarize_evidence(state, criterion_id)
            
            try:
                opinion = self.chain.invoke({
                    "judge_name": self.judge_name,
                    "criterion_name": criterion_name,
                    "criterion_id": criterion_id,
                    "evidence_summary": evidence_summary
                })
                
                opinion.timestamp = datetime.now()
                opinions.append(opinion)
                
                print(f"  → {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                print(f"  ❌ Error for {criterion_id}: {str(e)}")
                fallback = JudicialOpinion(
                    judge="Defense",
                    criterion_id=criterion_id,
                    score=3,
                    argument=f"Error evaluating, defaulting to average: {str(e)}",
                    cited_evidence=[]
                )
                opinions.append(fallback)
        
        return {"opinions": opinions}


class TechLeadNode(BaseJudgeNode):
    """Tech Lead judge - pragmatic, production focus."""
    
    def __init__(self):
        super().__init__("TechLead", TECH_LEAD_PROMPT)
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate evidence as Tech Lead."""
        print("🔧  TechLead: Analyzing evidence...")
        
        rubric_dims = state.rubric_dimensions
        if not rubric_dims:
            rubric_dims = [
                {"id": "git_forensic_analysis", "name": "Git Forensic Analysis"},
                {"id": "state_management_rigor", "name": "State Management Rigor"},
                {"id": "graph_orchestration", "name": "Graph Orchestration Architecture"},
                {"id": "safe_tool_engineering", "name": "Safe Tool Engineering"},
                {"id": "structured_output", "name": "Structured Output Enforcement"},
                {"id": "judicial_nuance", "name": "Judicial Nuance"},
                {"id": "theoretical_depth", "name": "Theoretical Depth"},
            ]
        
        opinions = []
        for dim in rubric_dims:
            criterion_id = dim.get("id", dim.get("name", "unknown"))
            criterion_name = dim.get("name", criterion_id)
            
            evidence_summary = self._summarize_evidence(state, criterion_id)
            
            try:
                opinion = self.chain.invoke({
                    "judge_name": self.judge_name,
                    "criterion_name": criterion_name,
                    "criterion_id": criterion_id,
                    "evidence_summary": evidence_summary
                })
                
                opinion.timestamp = datetime.now()
                opinions.append(opinion)
                
                print(f"  → {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                print(f"  ❌ Error for {criterion_id}: {str(e)}")
                fallback = JudicialOpinion(
                    judge="TechLead",
                    criterion_id=criterion_id,
                    score=3,
                    argument=f"Error evaluating, assuming average: {str(e)}",
                    cited_evidence=[]
                )
                opinions.append(fallback)
        
        return {"opinions": opinions}


from src.state import AgentState, JudicialOpinion, Evidence, AuditReport, CriterionResult

class OpinionAggregatorNode:
    """Collects opinions and synthesizes the Deterministic Chief Justice verdict."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Aggregate opinions via deterministic rules and produce final AuditReport."""
        opinions = state.opinions
        
        if not opinions:
            print("\n⚠️  No opinions to aggregate")
            return {}
        
        
        print("\n" + "="*70)
        print("⚖️  CHIEF JUSTICE OPINION SYNTHESIS".center(70))
        print("="*70)
        
        # Group by criterion
        by_criterion = {}
        for op in opinions:
            if op.criterion_id not in by_criterion:
                by_criterion[op.criterion_id] = []
            by_criterion[op.criterion_id].append(op)
            
        final_criteria_results = []
        overall_score_sum = 0
        
        for criterion_id, ops in by_criterion.items():
            print(f"\n📋 Evaluating: {criterion_id}")
            
            # Map judge scores
            scores = {"Prosecutor": 3, "Defense": 3, "TechLead": 3}
            arguments = {}
            for op in ops:
                scores[op.judge] = op.score
                arguments[op.judge] = op.argument
                print(f"  [{op.judge}] {op.score}/5 - {op.argument[:70]}...")
            
            # 1. Base Weighted Score (TechLead has 2x weight)
            base_score = round(
                (scores["Prosecutor"] + scores["Defense"] + (2 * scores["TechLead"])) / 4
            )
            final_score = base_score
            dissent_summary = None
            remediation = "Continue tracking."
            
            # 2. Hard Rule: Security Flaw Cap
            if "safe" in criterion_id.lower() or "security" in criterion_id.lower():
                if any(s < 3 for s in scores.values()):
                    print("  🚨 SECURITY FLAW TRIGGER: Score capped at 3.")
                    final_score = min(final_score, 3)
                    remediation = "IMMEDIATE FIX REQUIRED: Security/safety vulnerabilities detected by judges."
            
            # 3. Hard Rule: No Evidence Auto-Fail
            evidence_count = 0
            for det, ev_list in state.evidences.items():
                for ev in ev_list:
                    if (criterion_id.lower() in ev.goal.lower() or 
                        any(word in ev.goal.lower() for word in criterion_id.lower().split('_'))):
                        if ev.found:
                            evidence_count += 1
            
            if evidence_count == 0:
                print("  🚨 MISSING EVIDENCE TRIGGER: Auto-failed to 1.")
                final_score = 1
                remediation = f"CRITICAL MISSING COMPONENT: No artifacts found matching {criterion_id}."
            
            # 4. Hard Rule: High Disagreement Variance
            max_score = max(scores.values())
            min_score = min(scores.values())
            if max_score - min_score >= 2:
                print(f"  ⚠️ HIGH VARIANCE TRIGGER (Δ{max_score-min_score}): Attaching dissent log.")
                dissent_summary = (
                    f"Strong disagreement between judges.\n"
                    f"Prosecutor ({scores['Prosecutor']}/5): {arguments.get('Prosecutor', 'N/A')}\n"
                    f"Defense ({scores['Defense']}/5): {arguments.get('Defense', 'N/A')}"
                )
            
            print(f"  ⭐ Final Synthesized Score: {final_score}/5")
            
            # Save criterion result
            final_criteria_results.append(CriterionResult(
                dimension_id=criterion_id,
                dimension_name=criterion_id.replace("_", " ").title(),
                final_score=final_score,
                prosecutor_score=scores["Prosecutor"],
                defense_score=scores["Defense"],
                tech_lead_score=scores["TechLead"],
                dissent_summary=dissent_summary,
                remediation=remediation
            ))
            
            overall_score_sum += final_score

        # Generate Final Audit Report
        overall_avg = overall_score_sum / len(by_criterion) if by_criterion else 0.0
        print(f"\n🏆 CHIEF JUSTICE OVERALL VERDICT: {overall_avg:.1f}/5.0")
        print("="*70 + "\n")
        
        evidence_summary_dict = {k: len(v) for k, v in state.evidences.items()}
        
        final_report = AuditReport(
            repo_url=state.repo_url,
            executive_summary=f"Automaton Auditor examined the repository and rendered a final score of {overall_avg:.1f}/5.0. See criterion breakdown for exact flaws and mitigating factors.",
            overall_score=overall_avg,
            criteria=final_criteria_results,
            remediation_plan="Review the 'Criteria Evaluation' scores of 3 or below and apply the suggested fixes.",
            evidence_summary=evidence_summary_dict
        )
        
        # Return the report as an update dict to the state
        return {"final_report": final_report}