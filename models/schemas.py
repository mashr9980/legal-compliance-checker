from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class CriteriaStatus(str, Enum):
    PRESENT = "PRESENT"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class DocumentType(str, Enum):
    POLICY = "POLICY"
    LAW = "LAW"
    REGULATION = "REGULATION"
    STANDARD = "STANDARD"
    CONTRACT = "CONTRACT"
    GUIDELINE = "GUIDELINE"
    FRAMEWORK = "FRAMEWORK"
    DECREE = "DECREE"
    CODE = "CODE"
    CIRCULAR = "CIRCULAR"
    NOTICE = "NOTICE"
    UNKNOWN = "UNKNOWN"

class CriteriaAnalysis(BaseModel):
    criteria_id: str
    criteria_name: str
    status: CriteriaStatus
    confidence: ConfidenceLevel
    coverage_percentage: float
    found_content: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)
    quality_assessment: str
    recommendations: List[str] = Field(default_factory=list)
    regulatory_alignment: Optional[str] = None
    implementation_priority: str

class DocumentAnalysis(BaseModel):
    document_type: DocumentType
    title: str
    structure_quality: str
    content_density: str
    semantic_themes: List[str] = Field(default_factory=list)
    key_sections: List[str] = Field(default_factory=list)
    regulatory_references: List[str] = Field(default_factory=list)
    language_quality: str

class PolicyAssessment(BaseModel):
    document_analysis: DocumentAnalysis
    criteria_results: List[CriteriaAnalysis]
    overall_coverage: float
    maturity_score: float
    compliance_gaps: List[str] = Field(default_factory=list)
    strategic_recommendations: List[str] = Field(default_factory=list)
    implementation_roadmap: List[str] = Field(default_factory=list)
    regulatory_summary: Dict[str, Any] = Field(default_factory=dict)

class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str

class DocumentMetadata(BaseModel):
    document_type: DocumentType
    title: str
    version: Optional[str] = None
    date: Optional[str] = None
    authority: Optional[str] = None
    scope: List[str] = Field(default_factory=list)
    key_topics: List[str] = Field(default_factory=list)
    semantic_fingerprint: Optional[str] = None