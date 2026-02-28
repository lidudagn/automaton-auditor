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
import logging
logger = logging.getLogger(__name__)


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

EVIDENCE_REGISTRY:
{evidence_registry}

You are the {judge_name}. Based on the evidence above, provide your JudicialOpinion.

Your opinion must include:
- judge: "{judge_name}"
- criterion_id: "{criterion_id}"
- score: 1-5 integer following your persona's guidelines
- argument: Detailed reasoning (2-3 sentences)
- cited_evidence_ids: List of valid Evidence IDs from the registry above that you referenced

Return ONLY the JudicialOpinion object.
""")
        ])
        
        self.chain = self.prompt | self.structured_llm
    
    def _format_evidence_registry(self, state: AgentState, criterion_id: str) -> str:
        """Create a summary of canonical registry records relevant to the criterion."""
        summary = []
        
        # Pull from the deterministic EvidenceRegistry
        for record_id, record in state.registry.all().items():
            if record.claim_reference and (
                criterion_id.lower() in record.claim_reference.lower() or 
                any(word in record.claim_reference.lower() for word in criterion_id.lower().split('_'))
            ):
                summary.append(
                    f"- ID: {record.id}\n"
                    f"  source: {record.source}\n"
                    f"  artifact_path: {record.artifact_path or 'N/A'}\n"
                    f"  claim_reference: {record.claim_reference}\n"
                    f"  exists: {record.exists}\n"
                    f"  rationale: {record.metadata.get('rationale', 'N/A')}\n"
                )
        
        if not summary:
            # If no direct matches, show all recent registry items contextually
            for record_id, record in list(state.registry.all().items())[:5]:
                summary.append(
                    f"- ID: {record.id}\n"
                    f"  exists: {record.exists}\n"
                    f"  claim_reference: {record.claim_reference}\n"
                )
                
        return "\n".join(summary) if summary else "No factual registry records found."


class ProsecutorNode(BaseJudgeNode):
    """Prosecutor judge - harsh, critical."""
    
    def __init__(self):
        super().__init__("Prosecutor", PROSECUTOR_PROMPT)
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate evidence as Prosecutor."""
        logger.info("⚖️  Prosecutor: Analyzing evidence...")
        
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
            
            evidence_registry = self._format_evidence_registry(state, criterion_id)
            
            import time
            import random
            time.sleep(random.uniform(1.0, 3.0)) # Stable jitter
            
            try:
                opinion = self.chain.invoke({
                    "judge_name": self.judge_name,
                    "criterion_name": criterion_name,
                    "criterion_id": criterion_id,
                    "evidence_registry": evidence_registry
                })
                
                # Ensure timestamp is set
                opinion.timestamp = datetime.now()
                opinions.append(opinion)
                
                logger.info(f"  → {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                logger.error(f"  ❌ Error for {criterion_id}: {str(e)}")
                # Create fallback opinion
                fallback = JudicialOpinion(
                    judge="Prosecutor",
                    criterion_id=criterion_id,
                    score=1,
                    argument=f"Error evaluating: {str(e)}",
                    cited_evidence_ids=[]
                )
                opinions.append(fallback)
        
        return {"opinions": opinions}


class DefenseNode(BaseJudgeNode):
    """Defense judge - forgiving, rewards effort."""
    
    def __init__(self):
        super().__init__("Defense", DEFENSE_PROMPT)
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate evidence as Defense."""
        logger.info("🛡️  Defense: Analyzing evidence...")
        
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
            
            evidence_registry = self._format_evidence_registry(state, criterion_id)
            
            import time
            import random
            time.sleep(random.uniform(1.0, 3.0)) # Stable jitter
            
            try:
                opinion = self.chain.invoke({
                    "judge_name": self.judge_name,
                    "criterion_name": criterion_name,
                    "criterion_id": criterion_id,
                    "evidence_registry": evidence_registry
                })
                
                opinion.timestamp = datetime.now()
                opinions.append(opinion)
                
                logger.info(f"  → {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                logger.error(f"  ❌ Error for {criterion_id}: {str(e)}")
                fallback = JudicialOpinion(
                    judge="Defense",
                    criterion_id=criterion_id,
                    score=3,
                    argument=f"Error evaluating, defaulting to average: {str(e)}",
                    cited_evidence_ids=[]
                )
                opinions.append(fallback)
        
        return {"opinions": opinions}


class TechLeadNode(BaseJudgeNode):
    """Tech Lead judge - pragmatic, production focus."""
    
    def __init__(self):
        super().__init__("TechLead", TECH_LEAD_PROMPT)
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate evidence as Tech Lead."""
        logger.info("🔧  TechLead: Analyzing evidence...")
        
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
            
            evidence_registry = self._format_evidence_registry(state, criterion_id)
            
            import time
            import random
            time.sleep(random.uniform(1.0, 3.0)) # Stable jitter
            
            try:
                opinion = self.chain.invoke({
                    "judge_name": self.judge_name,
                    "criterion_name": criterion_name,
                    "criterion_id": criterion_id,
                    "evidence_registry": evidence_registry
                })
                
                opinion.timestamp = datetime.now()
                opinions.append(opinion)
                
                logger.info(f"  → {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                logger.error(f"  ❌ Error for {criterion_id}: {str(e)}")
                fallback = JudicialOpinion(
                    judge="TechLead",
                    criterion_id=criterion_id,
                    score=3,
                    argument=f"Error evaluating, assuming average: {str(e)}",
                    cited_evidence_ids=[]
                )
                opinions.append(fallback)
        
        return {"opinions": opinions}

