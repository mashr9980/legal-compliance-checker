from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"

class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class LegalRequirement(BaseModel):
    id: str
    description: str
    category: str
    source_section: str
    mandatory: bool

class ComplianceIssue(BaseModel):
    requirement_id: str
    requirement_description: str
    status: ComplianceStatus
    current_text: Optional[str] = None
    issue_description: Optional[str] = None
    recommendation: Optional[str] = None
    risk_level: RiskLevel
    source_section: str
    category: str

class ComplianceResult(BaseModel):
    total_requirements: int
    compliant_count: int
    non_compliant_count: int
    partial_count: int
    compliance_score: float
    issues: List[ComplianceIssue]
    missing_clauses: List[str]

class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str