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


class OpinionAggregatorNode:
    """Collects and displays opinions from all judges."""
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Aggregate and display judicial opinions."""
        opinions = state.opinions
        
        if not opinions:
            print("\n⚠️  No opinions to aggregate")
            return {}
        
        print("\n" + "="*70)
        print("⚖️  JUDICIAL OPINIONS AGGREGATOR".center(70))
        print("="*70)
        
        # Group by criterion
        by_criterion = {}
        for op in opinions:
            if op.criterion_id not in by_criterion:
                by_criterion[op.criterion_id] = []
            by_criterion[op.criterion_id].append(op)
        
        # Display opinions by criterion
        for criterion, ops in by_criterion.items():
            print(f"\n📋 {criterion}:")
            
            # Calculate average score
            avg_score = sum(op.score for op in ops) / len(ops)
            
            for op in ops:
                score_color = "🟢" if op.score >= 4 else "🟡" if op.score >= 3 else "🔴"
                print(f"  {score_color} {op.judge}: {op.score}/5")
                print(f"     {op.argument[:100]}...")
            
            print(f"  📊 Average Score: {avg_score:.1f}/5")
        
        # Summary statistics
        print("\n" + "-"*70)
        print("  📈 SUMMARY:")
        print(f"     Total opinions: {len(opinions)}")
        print(f"     Unique criteria: {len(by_criterion)}")
        print(f"     Overall average: {sum(op.score for op in opinions)/len(opinions):.1f}/5")
        print("="*70 + "\n")
        
        return {}