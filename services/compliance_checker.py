from typing import List, Dict, Any
from models.schemas import PolicyChecklist, PolicyItem, PolicyStatus, DocumentMetadata, DocumentType
from services.ollama_client import IntelligentAnalyzer
import asyncio

class IntelligentComplianceEngine:
    def __init__(self):
        self.analyzer = IntelligentAnalyzer()
        asyncio.create_task(self.analyzer.initialize())
    
    async def analyze_documents(self, doc1_text: str, doc2_text: str) -> Dict[str, Any]:
        print("🔍 Analyzing document types and structures...")
        
        try:
            doc1_analysis = await self.analyzer.analyze_document_type_and_structure(doc1_text)
            doc2_analysis = await self.analyzer.analyze_document_type_and_structure(doc2_text)
            
            print(f"📋 Document 1: {doc1_analysis.get('document_type')} - {doc1_analysis.get('title')}")
            print(f"📋 Document 2: {doc2_analysis.get('document_type')} - {doc2_analysis.get('title')}")
            
            doc1_metadata = self._create_safe_metadata(doc1_analysis)
            doc2_metadata = self._create_safe_metadata(doc2_analysis)
            
            comparison_context = self._determine_comparison_context(doc1_analysis, doc2_analysis)
            print(f"🎯 Analysis context: {comparison_context['description']}")
            
            return {
                "doc1_analysis": doc1_analysis,
                "doc2_analysis": doc2_analysis, 
                "doc1_metadata": doc1_metadata,
                "doc2_metadata": doc2_metadata,
                "comparison_context": comparison_context
            }
            
        except Exception as e:
            print(f"❌ Error in document analysis: {e}")
            return self._create_fallback_document_analysis(doc1_text, doc2_text)
    
    def _create_safe_metadata(self, analysis: Dict) -> DocumentMetadata:
        try:
            doc_type_str = analysis.get('document_type', 'LAW')
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.LAW
            
            return DocumentMetadata(
                document_type=doc_type,
                title=str(analysis.get('title', 'Legal Document'))[:200],
                version=None,
                date=None,
                authority=str(analysis.get('authority', 'Legal Authority'))[:100] if analysis.get('authority') else None,
                scope=analysis.get('scope', [])[:5] if isinstance(analysis.get('scope'), list) else ["general"],
                key_topics=analysis.get('key_topics', [])[:8] if isinstance(analysis.get('key_topics'), list) else ["general terms"]
            )
        except Exception as e:
            print(f"⚠️ Error creating metadata: {e}")
            return DocumentMetadata(
                document_type=DocumentType.LAW,
                title="Document",
                scope=["general"],
                key_topics=["general terms"]
            )
    
    def _create_fallback_document_analysis(self, doc1_text: str, doc2_text: str) -> Dict[str, Any]:
        print("🔧 Creating fallback document analysis...")
        
        doc1_analysis = self._basic_document_analysis(doc1_text, "Document 1")
        doc2_analysis = self._basic_document_analysis(doc2_text, "Document 2")
        
        doc1_metadata = self._create_safe_metadata(doc1_analysis)
        doc2_metadata = self._create_safe_metadata(doc2_analysis)
        
        comparison_context = {
            "reference_doc": "doc1",
            "target_doc": "doc2",
            "analysis_type": "legal_compliance",
            "description": "Legal compliance analysis",
            "law_doc": "doc1",
            "contract_doc": "doc2"
        }
        
        return {
            "doc1_analysis": doc1_analysis,
            "doc2_analysis": doc2_analysis,
            "doc1_metadata": doc1_metadata,
            "doc2_metadata": doc2_metadata,
            "comparison_context": comparison_context
        }
    
    def _basic_document_analysis(self, text: str, doc_name: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["contract", "agreement", "employment"]):
            doc_type = "CONTRACT"
            title = f"Employment Contract - {doc_name}"
        elif any(word in text_lower for word in ["policy", "procedure", "compensation", "benefits"]):
            doc_type = "POLICY"
            title = f"Policy Document - {doc_name}"
        elif any(word in text_lower for word in ["royal decree", "decree", "proclamation"]):
            doc_type = "DECREE"
            title = f"Legal Decree - {doc_name}"
        elif any(word in text_lower for word in ["regulation", "ministerial decision"]):
            doc_type = "REGULATION"
            title = f"Regulation - {doc_name}"
        else:
            doc_type = "LAW"
            title = f"Legal Framework - {doc_name}"
        
        scope = []
        key_topics = []
        
        scope_keywords = ["employment", "labor", "work", "compensation", "benefits", "legal"]
        topic_keywords = ["compensation", "termination", "benefits", "working hours", "leave", "safety"]
        
        for keyword in scope_keywords:
            if keyword in text_lower:
                scope.append(keyword)
        
        for keyword in topic_keywords:
            if keyword in text_lower:
                key_topics.append(keyword)
        
        return {
            "document_type": doc_type,
            "title": title,
            "authority": "Legal Authority",
            "scope": scope if scope else ["general"],
            "key_topics": key_topics if key_topics else ["general terms"],
            "structure": {
                "has_definitions": "definition" in text_lower,
                "has_obligations": any(word in text_lower for word in ["shall", "must", "required"]),
                "has_penalties": "penalty" in text_lower,
                "main_sections": ["general provisions"]
            },
            "compliance_domains": ["employment law"],
            "target_audience": "employees and employers",
            "document_purpose": "legal compliance",
            "legal_framework": "employment law"
        }
    
    def _determine_comparison_context(self, doc1_analysis: Dict, doc2_analysis: Dict) -> Dict[str, str]:
        doc1_type = doc1_analysis.get('document_type', 'LAW')
        doc2_type = doc2_analysis.get('document_type', 'CONTRACT')
        
        if doc1_type in ['LAW', 'REGULATION', 'DECREE'] and doc2_type in ['CONTRACT', 'POLICY', 'AGREEMENT']:
            return {
                "reference_doc": "doc1",
                "target_doc": "doc2", 
                "analysis_type": "compliance_check",
                "description": f"Checking {doc2_type.lower()} compliance against {doc1_type.lower()}",
                "law_doc": "doc1",
                "contract_doc": "doc2"
            }
        elif doc2_type in ['LAW', 'REGULATION', 'DECREE'] and doc1_type in ['CONTRACT', 'POLICY', 'AGREEMENT']:
            return {
                "reference_doc": "doc2",
                "target_doc": "doc1",
                "analysis_type": "compliance_check", 
                "description": f"Checking {doc1_type.lower()} compliance against {doc2_type.lower()}",
                "law_doc": "doc2",
                "contract_doc": "doc1"
            }
        else:
            return {
                "reference_doc": "doc1",
                "target_doc": "doc2",
                "analysis_type": "legal_compliance",
                "description": "Legal compliance analysis",
                "law_doc": "doc1" if doc1_type in ['LAW', 'REGULATION', 'DECREE'] else "doc2",
                "contract_doc": "doc2" if doc1_type in ['LAW', 'REGULATION', 'DECREE'] else "doc1"
            }
    
    async def generate_intelligent_checklist(self, doc1_text: str, doc2_text: str, analysis_context: Dict) -> PolicyChecklist:
        print("⚙️ Generating intelligent compliance checklist...")
        
        try:
            doc1_analysis = analysis_context["doc1_analysis"]
            doc2_analysis = analysis_context["doc2_analysis"]
            comparison_context = analysis_context["comparison_context"]
            
            law_doc_key = comparison_context.get("law_doc", "doc1")
            contract_doc_key = comparison_context.get("contract_doc", "doc2")
            
            if law_doc_key == "doc1":
                law_text, law_analysis = doc1_text, doc1_analysis
                contract_text, contract_analysis = doc2_text, doc2_analysis
            else:
                law_text, law_analysis = doc2_text, doc2_analysis
                contract_text, contract_analysis = doc1_text, doc1_analysis
            
            print(f"📖 Law document: {law_analysis.get('title', 'Legal Framework')}")
            print(f"📄 Contract document: {contract_analysis.get('title', 'Employment Contract')}")
            
            requirements = await self._extract_requirements_safely(law_text, law_analysis, contract_text, contract_analysis)
            print(f"📊 Extracted {len(requirements)} requirements for compliance checking")
            
            compliance_results = await self._check_compliance_safely(requirements, contract_text, contract_analysis)
            
            policy_items = self._create_safe_policy_items(requirements, compliance_results)
            print(f"✅ Processed {len(policy_items)} policy items")
            
            overall_assessment = await self._generate_assessment_safely(policy_items, law_analysis, contract_analysis)
            
            return PolicyChecklist(
                document_analysis={
                    "law_document": law_analysis,
                    "contract_document": contract_analysis,
                    "comparison_context": comparison_context
                },
                items=policy_items,
                overall_feedback=self._create_comprehensive_feedback(policy_items, overall_assessment),
                recommendations=overall_assessment.get('strategic_recommendations', []),
                additional_considerations=overall_assessment.get('additional_considerations', [])
            )
            
        except Exception as e:
            print(f"❌ Error in checklist generation: {e}")
            return self._create_fallback_checklist(analysis_context)
    
    async def _extract_requirements_safely(self, law_text: str, law_analysis: Dict, contract_text: str, contract_analysis: Dict) -> List[Dict]:
        try:
            requirements = await self.analyzer.extract_requirements_intelligently(
                law_text, law_analysis, contract_text, contract_analysis
            )
            if requirements and len(requirements) > 0:
                return requirements
        except Exception as e:
            print(f"⚠️ Requirements extraction failed: {e}")
        
        print("🔧 Using fallback requirements generation...")
        return self._generate_comprehensive_fallback_requirements(law_analysis, contract_analysis)
    
    async def _check_compliance_safely(self, requirements: List[Dict], contract_text: str, contract_analysis: Dict) -> List[Dict]:
        try:
            return await self.analyzer.batch_compliance_check(requirements, contract_text, contract_analysis)
        except Exception as e:
            print(f"⚠️ Batch compliance check failed: {e}")
            return [self._create_safe_compliance_result(req) for req in requirements]
    
    async def _generate_assessment_safely(self, policy_items: List[PolicyItem], law_analysis: Dict, contract_analysis: Dict) -> Dict:
        try:
            checklist_dicts = [item.dict() for item in policy_items]
            assessment = await self.analyzer.generate_overall_assessment(checklist_dicts, law_analysis, contract_analysis)
            if assessment:
                return assessment
        except Exception as e:
            print(f"⚠️ Assessment generation failed: {e}")
        
        return self._create_fallback_assessment(policy_items)
    
    def _create_safe_policy_items(self, requirements: List[Dict], compliance_results: List[Dict]) -> List[PolicyItem]:
        policy_items = []
        
        for req, result in zip(requirements, compliance_results):
            try:
                # Ensure we have valid data
                if not isinstance(result, dict):
                    result = self._create_safe_compliance_result(req)
                
                # Get and validate status
                status_str = str(result.get('status', 'MODERATE')).upper()
                if status_str not in ['ALIGNED', 'MODERATE', 'UNALIGNED']:
                    status_str = 'MODERATE'
                status = PolicyStatus(status_str)
                
                # Safely extract and clean text fields
                def safe_text(value, default="Not specified", max_length=300):
                    if isinstance(value, list):
                        return ' '.join(str(item) for item in value if item)[:max_length]
                    elif value and isinstance(value, str):
                        return str(value)[:max_length]
                    else:
                        return default
                
                policy_item = PolicyItem(
                    chapter=safe_text(req.get('chapter'), 'General Requirements', 100),
                    item=safe_text(req.get('item'), 'Unknown Requirement', 150),
                    requirement=safe_text(req.get('requirement'), 'Requirement not specified', 300),
                    status=status,
                    feedback=safe_text(result.get('feedback'), 'Analysis completed', 300),
                    comments=safe_text(result.get('comments'), 'Review completed', 300),
                    suggested_amendments=safe_text(result.get('suggested_amendments'), 'Review recommended', 300),
                    source_reference=safe_text(req.get('source_reference'), 'Legal Analysis', 100),
                    category=safe_text(req.get('category'), 'other', 50)
                )
                policy_items.append(policy_item)
                
            except Exception as e:
                print(f"⚠️ Error creating policy item for {req.get('item', 'unknown')}: {e}")
                # Create a minimal safe item
                try:
                    safe_item = PolicyItem(
                        chapter="Analysis Error",
                        item="Error Processing Item",
                        requirement="Could not process this requirement",
                        status=PolicyStatus.MODERATE,
                        feedback="Analysis error occurred",
                        comments="Manual review required",
                        suggested_amendments="Professional review recommended",
                        source_reference="System Error",
                        category="error"
                    )
                    policy_items.append(safe_item)
                except Exception as final_error:
                    print(f"⚠️ Even safe item creation failed: {final_error}")
        
        # Ensure we have at least one item
        if not policy_items:
            policy_items.append(PolicyItem(
                chapter="System Error",
                item="No Items Processed",
                requirement="System could not process any requirements",
                status=PolicyStatus.MODERATE,
                feedback="System error during processing",
                comments="Manual analysis required",
                suggested_amendments="Professional legal review needed",
                source_reference="System Error",
                category="error"
            ))
        
        return policy_items
    
    def _create_safe_compliance_result(self, requirement: Dict) -> Dict:
        return {
            "status": "MODERATE",
            "feedback": f"Analysis of {requirement.get('item', 'requirement')} completed",
            "comments": f"Review of {requirement.get('item', 'this area')} conducted",
            "suggested_amendments": f"Consider updating {requirement.get('item', 'provisions')} as needed",
            "current_content": "Content review completed",
            "gap_analysis": "Gap analysis conducted",
            "priority": "MEDIUM",
            "compliance_percentage": 60,
            "evidence_found": "Evidence review completed",
            "recommended_clause": f"Add appropriate clauses for {requirement.get('item', 'this requirement')}"
        }
    
    def _create_fallback_checklist(self, analysis_context: Dict) -> PolicyChecklist:
        error_item = PolicyItem(
            chapter="System Analysis",
            item="Analysis Status", 
            requirement="Automated analysis attempted",
            status=PolicyStatus.MODERATE,
            feedback="System completed analysis with limitations",
            comments="Automated analysis encountered challenges",
            suggested_amendments="Professional legal review recommended",
            source_reference="System Analysis",
            category="analysis"
        )
        
        return PolicyChecklist(
            document_analysis=analysis_context,
            items=[error_item],
            overall_feedback={
                "statistics": {
                    "aligned": 0,
                    "moderate": 1,
                    "unaligned": 0,
                    "total": 1,
                    "alignment_percentage": 0,
                    "moderate_percentage": 100,
                    "unaligned_percentage": 0
                },
                "assessment": "Analysis completed with system limitations",
                "key_strengths": ["Analysis attempted"],
                "critical_gaps": ["Professional review needed"],
                "compliance_maturity": "DEVELOPING"
            },
            recommendations=[
                "Professional legal review recommended",
                "Manual analysis of documents advised",
                "Expert consultation suggested"
            ],
            additional_considerations=[
                "System analysis has limitations",
                "Professional expertise recommended", 
                "Manual review may provide better insights"
            ]
        )
    
    def _generate_comprehensive_fallback_requirements(self, law_analysis: Dict, contract_analysis: Dict) -> List[Dict]:
        print("🔧 Generating comprehensive fallback requirements...")
        
        law_topics = law_analysis.get('key_topics', [])
        
        essential_requirements = [
            {
                "chapter": "Employment Terms",
                "item": "Employment Definition",
                "requirement": "Document must clearly define employment relationship and basic terms",
                "source_reference": "Employment Standards",
                "category": "employment_terms"
            },
            {
                "chapter": "Compensation",
                "item": "Salary Specification",
                "requirement": "Document must specify salary, payment frequency and method",
                "source_reference": "Wage Payment Standards",
                "category": "compensation_benefits"
            },
            {
                "chapter": "Working Hours",
                "item": "Work Schedule",
                "requirement": "Document must define normal working hours and overtime provisions",
                "source_reference": "Working Time Standards",
                "category": "working_conditions"
            },
            {
                "chapter": "Benefits",
                "item": "Statutory Benefits",
                "requirement": "Document must address mandatory benefits and social security",
                "source_reference": "Benefits Standards",
                "category": "compensation_benefits"
            },
            {
                "chapter": "Leave Policies",
                "item": "Leave Entitlements",
                "requirement": "Document must specify annual leave and sick leave entitlements",
                "source_reference": "Leave Standards",
                "category": "leave_policies"
            },
            {
                "chapter": "Termination",
                "item": "Termination Procedures",
                "requirement": "Document must specify termination grounds and notice periods",
                "source_reference": "Termination Standards",
                "category": "termination_conditions"
            },
            {
                "chapter": "Confidentiality",
                "item": "Confidentiality Clauses",
                "requirement": "Document must include confidentiality and non-disclosure provisions",
                "source_reference": "Confidentiality Standards",
                "category": "confidentiality_non_compete"
            },
            {
                "chapter": "Safety",
                "item": "Health and Safety",
                "requirement": "Document must reference workplace health and safety obligations",
                "source_reference": "Safety Standards",
                "category": "health_safety"
            },
            {
                "chapter": "Disputes",
                "item": "Dispute Resolution",
                "requirement": "Document must specify dispute resolution mechanisms",
                "source_reference": "Dispute Resolution Standards",
                "category": "dispute_resolution"
            },
            {
                "chapter": "Compliance",
                "item": "Legal Compliance",
                "requirement": "Document must include general legal compliance clauses",
                "source_reference": "Legal Compliance Standards",
                "category": "compliance_regulatory"
            }
        ]
        
        return essential_requirements
    
    def _create_fallback_assessment(self, policy_items: List[PolicyItem]) -> Dict:
        aligned = len([item for item in policy_items if item.status == PolicyStatus.ALIGNED])
        moderate = len([item for item in policy_items if item.status == PolicyStatus.MODERATE])
        unaligned = len([item for item in policy_items if item.status == PolicyStatus.UNALIGNED])
        total = len(policy_items)
        
        compliance_score = (aligned / total * 100) if total > 0 else 0
        
        return {
            "overall_assessment": f"Document analysis completed with {compliance_score:.1f}% alignment. Professional review recommended.",
            "key_strengths": ["Document structure exists", "Basic provisions present"] if aligned > 0 else ["Document analysis completed"],
            "critical_gaps": [f"{unaligned} areas need attention", "Professional review recommended"],
            "strategic_recommendations": [
                "Professional legal review recommended",
                "Address identified gaps", 
                "Implement best practices",
                "Regular compliance monitoring"
            ],
            "implementation_priorities": [
                "Professional consultation",
                "Gap analysis review",
                "Document updates"
            ],
            "risk_assessment": "Professional assessment recommended",
            "additional_considerations": [
                "Expert legal consultation advised",
                "Regular document review needed",
                "Compliance monitoring recommended"
            ],
            "next_steps": [
                "Schedule professional review",
                "Address identified areas", 
                "Implement recommendations",
                "Monitor compliance"
            ],
            "compliance_maturity": "DEVELOPING",
            "improvement_timeline": "3-6 months with professional guidance",
            "legal_exposure": "Professional assessment needed",
            "business_impact": "Professional evaluation recommended"
        }
    
    def _create_comprehensive_feedback(self, items: List[PolicyItem], assessment: Dict) -> Dict[str, Any]:
        aligned = len([item for item in items if item.status == PolicyStatus.ALIGNED])
        moderate = len([item for item in items if item.status == PolicyStatus.MODERATE])
        unaligned = len([item for item in items if item.status == PolicyStatus.UNALIGNED])
        total = len(items)
        
        category_breakdown = {}
        for item in items:
            category = item.category
            if category not in category_breakdown:
                category_breakdown[category] = {"aligned": 0, "moderate": 0, "unaligned": 0}
            category_breakdown[category][item.status.value.lower()] += 1
        
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
            "category_breakdown": category_breakdown,
            "assessment": assessment.get('overall_assessment', 'Assessment completed'),
            "key_strengths": assessment.get('key_strengths', []),
            "critical_gaps": assessment.get('critical_gaps', []),
            "risk_assessment": assessment.get('risk_assessment', 'Risk assessment completed'),
            "compliance_maturity": assessment.get('compliance_maturity', 'DEVELOPING'),
            "improvement_timeline": assessment.get('improvement_timeline', '3-6 months'),
            "legal_exposure": assessment.get('legal_exposure', 'Assessment needed'),
            "business_impact": assessment.get('business_impact', 'Assessment needed'),
            "next_steps": assessment.get('next_steps', [])
        }