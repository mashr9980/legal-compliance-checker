from typing import List, Dict, Any
from models.schemas import PolicyAssessment, DocumentAnalysis, CriteriaAnalysis
from services.intelligent_analyzer import IntelligentPolicyAnalyzer
import asyncio

class IntelligentComplianceEngine:
    def __init__(self):
        self.analyzer = IntelligentPolicyAnalyzer()
        asyncio.create_task(self.analyzer.initialize())
    
    async def comprehensive_policy_analysis(self, regulatory_texts: List[str], policy_text: str, 
                                          regulatory_filenames: List[str], policy_filename: str) -> PolicyAssessment:
        print(f"🔍 Starting comprehensive policy analysis...")
        print(f"📋 Regulatory documents: {len(regulatory_texts)}")
        print(f"📄 Policy document: {policy_filename}")
        
        try:
            print("📊 Phase 1: Document intelligence analysis...")
            document_analysis = await self.analyzer.analyze_document_intelligence(policy_text)
            print(f"   Document type: {document_analysis.document_type}")
            print(f"   Document title: {document_analysis.title}")
            
            print("🎯 Phase 2: Criteria coverage analysis...")
            criteria_results = await self.analyzer.analyze_criteria_coverage(
                policy_text, regulatory_texts, document_analysis
            )
            
            present_count = sum(1 for c in criteria_results if c.status.value == 'PRESENT')
            partial_count = sum(1 for c in criteria_results if c.status.value == 'PARTIAL')
            missing_count = sum(1 for c in criteria_results if c.status.value == 'MISSING')
            
            print(f"   Criteria analysis complete:")
            print(f"   - Present: {present_count}")
            print(f"   - Partial: {partial_count}")
            print(f"   - Missing: {missing_count}")
            
            print("📈 Phase 3: Strategic assessment generation...")
            strategic_assessment = await self.analyzer.generate_strategic_assessment(
                criteria_results, document_analysis
            )
            
            overall_coverage = sum(c.coverage_percentage for c in criteria_results) / len(criteria_results)
            print(f"   Overall coverage: {overall_coverage:.1f}%")
            print(f"   Maturity score: {strategic_assessment['maturity_score']:.1f}")
            
            policy_assessment = PolicyAssessment(
                document_analysis=document_analysis,
                criteria_results=criteria_results,
                overall_coverage=overall_coverage,
                maturity_score=strategic_assessment['maturity_score'],
                compliance_gaps=strategic_assessment['compliance_gaps'],
                strategic_recommendations=strategic_assessment['strategic_recommendations'],
                implementation_roadmap=strategic_assessment['implementation_roadmap'],
                regulatory_summary=strategic_assessment['regulatory_summary']
            )
            
            print("✅ Comprehensive policy analysis completed successfully")
            return policy_assessment
            
        except Exception as e:
            print(f"❌ Error in comprehensive policy analysis: {e}")
            return self._create_fallback_assessment(regulatory_filenames, policy_filename)
    
    def _create_fallback_assessment(self, regulatory_filenames: List[str], policy_filename: str) -> PolicyAssessment:
        print("🔧 Creating fallback assessment...")
        
        from models.schemas import DocumentType, CriteriaStatus, ConfidenceLevel
        from config import POLICY_ANALYSIS_CRITERIA
        
        fallback_document_analysis = DocumentAnalysis(
            document_type=DocumentType.POLICY,
            title=f"Policy Assessment - {policy_filename}",
            structure_quality="FAIR",
            content_density="MEDIUM",
            semantic_themes=["policy", "organizational"],
            key_sections=["general provisions"],
            regulatory_references=[],
            language_quality="STANDARD"
        )
        
        fallback_criteria = []
        for criteria in POLICY_ANALYSIS_CRITERIA:
            fallback_criteria.append(CriteriaAnalysis(
                criteria_id=criteria['id'],
                criteria_name=criteria['name'],
                status=CriteriaStatus.MISSING,
                confidence=ConfidenceLevel.LOW,
                coverage_percentage=0.0,
                found_content=[],
                missing_elements=[f"{criteria['name']} requires professional assessment"],
                quality_assessment=f"Analysis of {criteria['name']} could not be completed automatically",
                recommendations=[f"Professional review recommended for {criteria['name']}"],
                regulatory_alignment="Professional assessment needed",
                implementation_priority="HIGH"
            ))
        
        return PolicyAssessment(
            document_analysis=fallback_document_analysis,
            criteria_results=fallback_criteria,
            overall_coverage=0.0,
            maturity_score=25.0,
            compliance_gaps=["Comprehensive professional review required"],
            strategic_recommendations=[
                "Engage professional policy consultant",
                "Conduct detailed manual assessment",
                "Implement systematic policy framework"
            ],
            implementation_roadmap=[
                "Phase 1: Professional consultation",
                "Phase 2: Gap analysis and planning",
                "Phase 3: Implementation and monitoring"
            ],
            regulatory_summary={
                "compliance_level": "NEEDS_IMPROVEMENT",
                "key_risks": ["Professional assessment required"],
                "priority_actions": ["Seek expert consultation"]
            }
        )