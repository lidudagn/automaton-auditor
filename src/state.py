# import operator
# from typing import Annotated, Dict, List, Literal, Optional, Any
# from typing_extensions import TypedDict

# from pydantic import BaseModel, Field


# class Evidence(BaseModel):
#     """Forensic evidence collected by detectives - PURE FACTS ONLY."""
#     goal: str = Field(description="What we were looking for (from rubric)")
#     found: bool = Field(description="Whether the artifact exists")
#     content: Optional[str] = Field(default=None, description="The actual evidence (code snippet, text, etc.)")
#     location: str = Field(description="File path or commit hash where evidence was found")
#     rationale: str = Field(description="Why we're confident about this evidence")
#     confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")


# class JudicialOpinion(BaseModel):
#     """Opinion from a judge persona - will be used in final submission."""
#     judge: Literal["Prosecutor", "Defense", "TechLead"]
#     criterion_id: str
#     score: int = Field(ge=1, le=5, description="Score from 1-5")
#     argument: str = Field(description="Detailed reasoning for the score")
#     cited_evidence: List[str] = Field(description="List of evidence IDs used")


# class CriterionResult(BaseModel):
#     """Final result for a single rubric criterion."""
#     dimension_id: str
#     dimension_name: str
#     final_score: int = Field(ge=1, le=5)
#     judge_opinions: List[JudicialOpinion]
#     dissent_summary: Optional[str] = None
#     remediation: str = ""


# class AuditReport(BaseModel):
#     """Final audit report."""
#     repo_url: str
#     executive_summary: str
#     overall_score: float
#     criteria: List[CriterionResult]
#     remediation_plan: str


# class AgentState(TypedDict):
#     """State passed between graph nodes - WITH REDUCERS for parallel execution."""
    
#     repo_url: str
#     pdf_path: str
#     rubric_dimensions: List[Dict[str, AnyP]]
    
#     evidences: Annotated[Dict[str, List[Evidence]], operator.ior]  
#     """Key: detective name ('repo', 'doc', 'vision'), Value: list of Evidence objects.
#        operator.ior merges dictionaries from parallel nodes."""
    
#     opinions: Annotated[List[JudicialOpinion], operator.add]
#     """List of JudicialOpinion objects from all judges.
#        operator.add concatenates lists from parallel nodes."""
    
#     final_report: Optional[AuditReport]


"""State definitions for Automaton Auditor - Phase 2 (Pydantic)."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Literal, Annotated
from datetime import datetime
import operator

from src.core.evidence_registry import EvidenceRegistry, EvidenceRecord
from src.core.evidence_graph import EvidenceGraph
import uuid

def merge_dicts(left: Dict[str, List[Any]], right: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
    """Merge evidence dictionaries by concatenating lists for matching keys."""
    res = left.copy() if left else {}
    for k, v in (right or {}).items():
        # Enforce detector attribution
        for ev in v:
            if hasattr(ev, 'detector'):
                ev.detector = k
                
        if k in res:
            res[k] = res[k] + v
        else:
            res[k] = v
    return res


class Evidence(BaseModel):
    """Forensic evidence collected by detectives."""
    
    id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    goal: str = Field(description="What we were looking for")
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None, description="Actual evidence content")
    location: str = Field(description="File path or commit hash")
    rationale: str = Field(description="Why we're confident")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    timestamp: datetime = Field(default_factory=datetime.now, description="When evidence was collected")
    detector: str = Field(default="unknown", description="Which detective collected this")

    def to_record(self) -> EvidenceRecord:
        """Adapter to migrate legacy Evidence to canonical EvidenceRecord."""
        source_map = {"repo": "repo", "doc": "pdf", "vision": "vision"}
        return EvidenceRecord(
            id=self.id,
            source=source_map.get(self.detector, "repo"),
            artifact_path=self.location,
            claim_reference=self.goal,
            exists=self.found,
            metadata={"content": self.content, "rationale": self.rationale, "confidence": self.confidence}
        )


class JudicialOpinion(BaseModel):
    """Opinion from a judge persona."""
    
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str
    score: int = Field(ge=1, le=5, description="Score from 1-5")
    argument: str = Field(description="Detailed reasoning")
    cited_evidence_ids: List[str] = Field(default_factory=list, description="Explicit Evidence IDs referenced from registry")
    timestamp: datetime = Field(default_factory=datetime.now)


class CriterionResult(BaseModel):
    """Final result for a single rubric criterion."""
    
    dimension_id: str
    dimension_name: str
    final_score: int = Field(ge=1, le=5)
    base_score: int = Field(default=0, description="Score before contradiction penalties")
    penalty_applied: int = Field(default=0, description="Penalty deducted due to contradictions")
    prosecutor_score: int = Field(ge=1, le=5)
    defense_score: int = Field(ge=1, le=5)
    tech_lead_score: int = Field(ge=1, le=5)
    dissent_summary: Optional[str] = None
    contradiction_flag: bool = Field(default=False, description="True if repo and doc evidence conflict")
    reasoning_trace: List[str] = Field(default_factory=list, description="Ordered log of deterministic rules and overrides applied")
    remediation: str = Field(default="", description="Specific improvement instructions")


class AuditReport(BaseModel):
    """Final audit report."""
    
    repo_url: str
    audit_date: datetime = Field(default_factory=datetime.now)
    executive_summary: str
    overall_score: float
    criteria: List[CriterionResult]
    remediation_plan: str
    detected_contradictions: List[str] = Field(default_factory=list, description="List of high-level contradictions found")
    evidence_summary: Dict[str, int] = Field(description="Count of evidence by detector")


class AuditRun(BaseModel):
    """Data object for a single deterministic audit run."""
    run_id: int
    timestamp: datetime = Field(default_factory=datetime.now)
    overall_score: float
    opinions: List[JudicialOpinion]
    registry_state: Dict[str, EvidenceRecord]
    contradictions_found: List[str] = Field(default_factory=list)


class MetaAuditState(BaseModel):
    """Higher-order state for aggregating multiple audit runs."""
    repo_url: str
    runs: List[AuditRun] = Field(default_factory=list)
    meta_registry: Dict[str, EvidenceRecord] = Field(default_factory=dict)
    meta_scores: Dict[str, float] = Field(default_factory=dict)
    coherence_penalties: List[str] = Field(default_factory=list)
    reasoning_trace: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentState(BaseModel):
    """Shared state flowing through the LangGraph - Pydantic version."""
    
    # Inputs
    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Phase 3 Canonical Dependencies
    registry: EvidenceRegistry = Field(default_factory=EvidenceRegistry)
    graph: EvidenceGraph = Field(default_factory=EvidenceGraph)
    
    # Evidence collected (Legacy representation)
    evidences: Annotated[Dict[str, List[Evidence]], merge_dicts] = Field(default_factory=dict)
    
    # Judicial opinions
    opinions: Annotated[List[JudicialOpinion], operator.add] = Field(default_factory=list)
    
    # Final report
    final_report: Optional[AuditReport] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    def add_evidence(self, detector: str, evidence: Evidence) -> None:
        """Add evidence to the state."""
        if detector not in self.evidences:
            self.evidences[detector] = []
        evidence.detector = detector
        self.evidences[detector].append(evidence)
    
    def get_evidence_count(self) -> int:
        """Get total number of evidence items."""
        return sum(len(ev_list) for ev_list in self.evidences.values())
    
    def get_successful_evidence(self) -> int:
        """Get count of successful evidence (found=True)."""
        return sum(
            1 for ev_list in self.evidences.values() 
            for ev in ev_list if ev.found
        )
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.get_evidence_count()
        if total == 0:
            return 0.0
        successful = self.get_successful_evidence()
        return (successful / total) * 100