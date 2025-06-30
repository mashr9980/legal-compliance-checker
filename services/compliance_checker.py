from typing import List, Dict, Any
from models.schemas import PolicyChecklist, PolicyItem, PolicyStatus, DocumentMetadata, DocumentType
from services.ollama_client import IntelligentAnalyzer
import asyncio

class IntelligentComplianceEngine:
    def __init__(self):
        self.analyzer = IntelligentAnalyzer()
        asyncio.create_task(self.analyzer.initialize())
    
    async def analyze_documents(self, doc1_text: str, doc2_text: str) -> Dict[str, Any]:
        doc1_analysis = await self.analyzer.analyze_document_type_and_structure(doc1_text)
        doc2_analysis = await self.analyzer.analyze_document_type_and_structure(doc2_text)
        
        doc1_metadata = self._create_metadata(doc1_analysis)
        doc2_metadata = self._create_metadata(doc2_analysis)
        
        return {
            "doc1_analysis": doc1_analysis,
            "doc2_analysis": doc2_analysis, 
            "doc1_metadata": doc1_metadata,
            "doc2_metadata": doc2_metadata,
            "comparison_context": self._determine_comparison_context(doc1_analysis, doc2_analysis)
        }
    
    def _create_metadata(self, analysis: Dict) -> DocumentMetadata:
        doc_type_str = analysis.get('document_type', 'POLICY')
        doc_type = DocumentType(doc_type_str) if doc_type_str in [e.value for e in DocumentType] else DocumentType.POLICY
        
        return DocumentMetadata(
            document_type=doc_type,
            title=analysis.get('title', 'Unknown Document'),
            authority=analysis.get('authority'),
            scope=analysis.get('scope', []),
            key_topics=analysis.get('key_topics', [])
        )
    
    def _determine_comparison_context(self, doc1_analysis: Dict, doc2_analysis: Dict) -> Dict[str, str]:
        doc1_type = doc1_analysis.get('document_type', 'UNKNOWN')
        doc2_type = doc2_analysis.get('document_type', 'UNKNOWN')
        
        if doc1_type in ['LAW', 'REGULATION'] and doc2_type in ['POLICY', 'CONTRACT']:
            return {
                "reference_doc": "doc1",
                "target_doc": "doc2", 
                "analysis_type": "compliance_check",
                "description": f"Checking {doc2_type.lower()} compliance against {doc1_type.lower()}"
            }
        elif doc2_type in ['LAW', 'REGULATION'] and doc1_type in ['POLICY', 'CONTRACT']:
            return {
                "reference_doc": "doc2",
                "target_doc": "doc1",
                "analysis_type": "compliance_check", 
                "description": f"Checking {doc1_type.lower()} compliance against {doc2_type.lower()}"
            }
        else:
            return {
                "reference_doc": "doc1",
                "target_doc": "doc2",
                "analysis_type": "gap_analysis",
                "description": f"Comparing {doc1_type.lower()} with {doc2_type.lower()}"
            }
    
    async def generate_intelligent_checklist(self, doc1_text: str, doc2_text: str, analysis_context: Dict) -> PolicyChecklist:
        doc1_analysis = analysis_context["doc1_analysis"]
        doc2_analysis = analysis_context["doc2_analysis"]
        comparison_context = analysis_context["comparison_context"]
        
        if comparison_context["reference_doc"] == "doc1":
            reference_text, reference_analysis = doc1_text, doc1_analysis
            target_text, target_analysis = doc2_text, doc2_analysis
        else:
            reference_text, reference_analysis = doc2_text, doc2_analysis
            target_text, target_analysis = doc1_text, doc1_analysis
        
        requirements = await self.analyzer.extract_requirements_intelligently(
            reference_text, reference_analysis, target_text, target_analysis
        )
        
        if not requirements:
            requirements = self._generate_fallback_requirements(reference_analysis, target_analysis)
        
        compliance_results = await self.analyzer.batch_compliance_check(
            requirements, target_text, target_analysis
        )
        
        policy_items = []
        for req, result in zip(requirements, compliance_results):
            if isinstance(result, Exception):
                result = self._create_fallback_result()
            
            status = PolicyStatus(result.get('status', 'UNALIGNED'))
            
            policy_item = PolicyItem(
                chapter=req.get('chapter', 'General'),
                item=req.get('item', req.get('requirement', 'Unknown')),
                requirement=req.get('requirement', ''),
                status=status,
                feedback=result.get('feedback', ''),
                comments=result.get('comments', ''),
                suggested_amendments=result.get('suggested_amendments', ''),
                source_reference=req.get('source_reference', ''),
                category=req.get('category', 'General')
            )
            policy_items.append(policy_item)
        
        overall_assessment = await self.analyzer.generate_overall_assessment(
            [item.dict() for item in policy_items], reference_analysis, target_analysis
        )
        
        return PolicyChecklist(
            document_analysis={
                "reference_document": reference_analysis,
                "target_document": target_analysis,
                "comparison_context": comparison_context
            },
            items=policy_items,
            overall_feedback=self._create_overall_feedback(policy_items, overall_assessment),
            recommendations=overall_assessment.get('strategic_recommendations', []),
            additional_considerations=overall_assessment.get('additional_considerations', [])
        )
    
    def _generate_fallback_requirements(self, reference_analysis: Dict, target_analysis: Dict) -> List[Dict]:
        key_topics = reference_analysis.get('key_topics', []) + target_analysis.get('key_topics', [])
        scope_areas = reference_analysis.get('scope', []) + target_analysis.get('scope', [])
        
        fallback_requirements = []
        
        for i, topic in enumerate(set(key_topics[:10]), 1):
            fallback_requirements.append({
                "chapter": f"Chapter {i}",
                "item": f"{topic} Requirements", 
                "requirement": f"Document must address {topic} adequately",
                "source_reference": "Structural Analysis",
                "category": topic.replace(' ', '_').lower(),
                "mandatory": True,
                "criteria": f"Presence and adequacy of {topic} provisions",
                "expected_content": f"Clear policies and procedures for {topic}"
            })
        
        for i, scope in enumerate(set(scope_areas[:5]), len(fallback_requirements)+1):
            fallback_requirements.append({
                "chapter": f"Section {i}",
                "item": f"{scope} Coverage",
                "requirement": f"Document must cover {scope} comprehensively", 
                "source_reference": "Scope Analysis",
                "category": "coverage",
                "mandatory": True,
                "criteria": f"Comprehensive coverage of {scope}",
                "expected_content": f"Detailed provisions for {scope}"
            })
        
        return fallback_requirements
    
    def _create_fallback_result(self) -> Dict:
        return {
            "status": "MODERATE",
            "feedback": "Analysis requires manual review",
            "comments": "Automated analysis was inconclusive",
            "suggested_amendments": "Manual review recommended",
            "priority": "MEDIUM",
            "compliance_percentage": 50
        }
    
    def _create_overall_feedback(self, items: List[PolicyItem], assessment: Dict) -> Dict[str, Any]:
        aligned = len([item for item in items if item.status == PolicyStatus.ALIGNED])
        moderate = len([item for item in items if item.status == PolicyStatus.MODERATE])
        unaligned = len([item for item in items if item.status == PolicyStatus.UNALIGNED])
        total = len(items)
        
        return {
            "statistics": {
                "aligned": aligned,
                "moderate": moderate, 
                "unaligned": unaligned,
                "total": total,
                "alignment_percentage": (aligned / total * 100) if total > 0 else 0,
                "moderate_percentage": (moderate / total * 100) if total > 0 else 0,
                "unaligned_percentage": (unaligned / total * 100) if total > 0 else 0
            },
            "assessment": assessment.get('overall_assessment', ''),
            "key_strengths": assessment.get('key_strengths', []),
            "critical_gaps": assessment.get('critical_gaps', []),
            "risk_assessment": assessment.get('risk_assessment', ''),
            "compliance_maturity": assessment.get('compliance_maturity', 'DEVELOPING'),
            "improvement_timeline": assessment.get('improvement_timeline', ''),
            "next_steps": assessment.get('next_steps', [])
        }