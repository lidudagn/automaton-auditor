import operator
from typing import Annotated, Dict, List, Literal, Optional, Any
from typing_extensions import TypedDict

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Forensic evidence collected by detectives - PURE FACTS ONLY."""
    goal: str = Field(description="What we were looking for (from rubric)")
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None, description="The actual evidence (code snippet, text, etc.)")
    location: str = Field(description="File path or commit hash where evidence was found")
    rationale: str = Field(description="Why we're confident about this evidence")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")


class JudicialOpinion(BaseModel):
    """Opinion from a judge persona - will be used in final submission."""
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str
    score: int = Field(ge=1, le=5, description="Score from 1-5")
    argument: str = Field(description="Detailed reasoning for the score")
    cited_evidence: List[str] = Field(description="List of evidence IDs used")


class CriterionResult(BaseModel):
    """Final result for a single rubric criterion."""
    dimension_id: str
    dimension_name: str
    final_score: int = Field(ge=1, le=5)
    judge_opinions: List[JudicialOpinion]
    dissent_summary: Optional[str] = None
    remediation: str = ""


class AuditReport(BaseModel):
    """Final audit report."""
    repo_url: str
    executive_summary: str
    overall_score: float
    criteria: List[CriterionResult]
    remediation_plan: str


class AgentState(TypedDict):
    """State passed between graph nodes - WITH REDUCERS for parallel execution."""
    
    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict[str, Any]]
    
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]  
    """Key: detective name ('repo', 'doc', 'vision'), Value: list of Evidence objects.
       operator.ior merges dictionaries from parallel nodes."""
    
    opinions: Annotated[List[JudicialOpinion], operator.add]
    """List of JudicialOpinion objects from all judges.
       operator.add concatenates lists from parallel nodes."""
    
    final_report: Optional[AuditReport]