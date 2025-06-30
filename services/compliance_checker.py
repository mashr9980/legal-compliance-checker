import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from models.schemas import ComplianceResult, ComplianceIssue, ComplianceStatus, RiskLevel, LegalRequirement
from services.ollama_client import OllamaClient
import asyncio

class ComplianceChecker:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.requirements_cache = []
        self.ollama_client = OllamaClient()
        asyncio.create_task(self.ollama_client.initialize())
    
    async def extract_requirements(self, legal_text: str) -> List[LegalRequirement]:
        requirements_data = await self.ollama_client.extract_requirements(legal_text)
        
        requirements = []
        for i, req_data in enumerate(requirements_data):
            req = LegalRequirement(
                id=req_data.get('id', f'REQ{i+1:03d}'),
                description=req_data.get('description', ''),
                category=req_data.get('category', 'other'),
                source_section=req_data.get('source_section', ''),
                mandatory=req_data.get('mandatory', True)
            )
            requirements.append(req)
        
        self.requirements_cache = requirements
        self._build_faiss_index([req.description for req in requirements])
        
        return requirements
    
    def _build_faiss_index(self, texts: List[str]):
        if not texts:
            return
            
        embeddings = self.embedding_model.encode(texts)
        embeddings = embeddings.astype('float32')
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
    
    def _find_relevant_sections(self, contract_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        if not self.index:
            return [(contract_text[:1000], 1.0)]
        
        sentences = self._split_into_sentences(contract_text)
        if not sentences:
            return [(contract_text[:1000], 1.0)]
        
        query_embeddings = self.embedding_model.encode(sentences)
        query_embeddings = query_embeddings.astype('float32')
        faiss.normalize_L2(query_embeddings)
        
        all_sections = []
        for embedding in query_embeddings:
            scores, indices = self.index.search(embedding.reshape(1, -1), min(top_k, len(self.requirements_cache)))
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(sentences):
                    all_sections.append((sentences[idx], float(score)))
        
        all_sections.sort(key=lambda x: x[1], reverse=True)
        return all_sections[:top_k]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    async def check_compliance(self, requirements: List[LegalRequirement], contract_text: str) -> ComplianceResult:
        relevant_sections = self._find_relevant_sections(contract_text)
        relevant_text = ' '.join([section[0] for section in relevant_sections])
        
        requirements_dict = [req.dict() for req in requirements]
        compliance_results = await self.ollama_client.batch_check_compliance(requirements_dict, relevant_text)
        
        issues = []
        compliant_count = 0
        non_compliant_count = 0
        partial_count = 0
        
        for req, result in zip(requirements, compliance_results):
            status_str = result.get('status', 'NON_COMPLIANT')
            
            if status_str == 'COMPLIANT':
                status = ComplianceStatus.COMPLIANT
                compliant_count += 1
            elif status_str == 'PARTIAL':
                status = ComplianceStatus.PARTIAL
                partial_count += 1
            else:
                status = ComplianceStatus.NON_COMPLIANT
                non_compliant_count += 1
            
            risk_str = result.get('risk_level', 'MEDIUM')
            risk_level = RiskLevel.HIGH if risk_str == 'HIGH' else RiskLevel.MEDIUM if risk_str == 'MEDIUM' else RiskLevel.LOW
            
            issue = ComplianceIssue(
                requirement_id=req.id,
                requirement_description=req.description,
                status=status,
                current_text=result.get('current_text'),
                issue_description=result.get('issue_description'),
                recommendation=result.get('recommendation'),
                risk_level=risk_level,
                source_section=req.source_section,
                category=req.category
            )
            issues.append(issue)
        
        total_requirements = len(requirements)
        compliance_score = (compliant_count + partial_count * 0.5) / total_requirements if total_requirements > 0 else 0
        
        missing_clauses = self._identify_missing_clauses(issues)
        
        return ComplianceResult(
            total_requirements=total_requirements,
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            partial_count=partial_count,
            compliance_score=round(compliance_score, 2),
            issues=issues,
            missing_clauses=missing_clauses
        )
    
    def _identify_missing_clauses(self, issues: List[ComplianceIssue]) -> List[str]:
        missing = []
        for issue in issues:
            if issue.status == ComplianceStatus.NON_COMPLIANT and not issue.current_text:
                missing.append(f"{issue.category.title()}: {issue.requirement_description}")
        return missing