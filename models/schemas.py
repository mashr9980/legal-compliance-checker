from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class PolicyStatus(str, Enum):
    ALIGNED = "ALIGNED"
    MODERATE = "MODERATE" 
    UNALIGNED = "UNALIGNED"

class DocumentType(str, Enum):
    POLICY = "POLICY"
    LAW = "LAW"
    REGULATION = "REGULATION"
    STANDARD = "STANDARD"
    CONTRACT = "CONTRACT"
    GUIDELINE = "GUIDELINE"
    AMENDMENT = "AMENDMENT"
    DECREE = "DECREE"
    CODE = "CODE"
    CIRCULAR = "CIRCULAR"
    NOTICE = "NOTICE"
    UNKNOWN = "UNKNOWN"

class PolicyItem(BaseModel):
    chapter: str
    item: str
    requirement: str
    status: PolicyStatus
    feedback: str
    comments: str
    suggested_amendments: str
    source_reference: str
    category: str

class PolicyChecklist(BaseModel):
    document_analysis: Dict[str, Any]
    items: List[PolicyItem]
    overall_feedback: Dict[str, Any]
    recommendations: List[str]
    additional_considerations: List[str]

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