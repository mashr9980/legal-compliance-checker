import aiohttp
import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from config import MODEL_NAME, MAX_PROMPT_LENGTH, POLICY_ANALYSIS_CRITERIA, CONFIDENCE_THRESHOLD
from models.schemas import CriteriaAnalysis, CriteriaStatus, ConfidenceLevel, DocumentAnalysis, DocumentType

class IntelligentPolicyAnalyzer:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = MODEL_NAME
        self.session = None
        self.criteria_framework = POLICY_ANALYSIS_CRITERIA
        self.max_retries = 3
        self.timeout = 200

    async def initialize(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            connector=aiohttp.TCPConnector(limit=10)
        )
        await self._ensure_model_available()

    async def _ensure_model_available(self):
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    model_names = [model['name'] for model in models.get('models', [])]
                    if self.model not in model_names:
                        await self._pull_model()
                    else:
                        print(f"✅ Model {self.model} is available")
                else:
                    print(f"❌ Failed to check models: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Model check error: {e}")

    async def _pull_model(self):
        try:
            print(f"📥 Pulling model {self.model}...")
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model}
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                status = json.loads(line.decode())
                                if 'status' in status:
                                    print(f"   {status.get('status')}")
                                if status.get('status') == 'success':
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"❌ Failed to pull model: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Model pull error: {e}")

    async def generate_with_context(self, prompt: str, system_prompt: str = None, max_tokens: int = 2048) -> str:
        for attempt in range(self.max_retries):
            try:
                result = await self._generate_completion(prompt, system_prompt, max_tokens)
                if result and not result.startswith("Error:") and len(result.strip()) > 50:
                    return result
                print(f"🔄 Attempt {attempt + 1} produced insufficient response, retrying...")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return f"Error after {self.max_retries} attempts: {str(e)}"
                await asyncio.sleep(2)
        
        return "Error: All retry attempts failed"

    async def _generate_completion(self, prompt: str, system_prompt: str = None, max_tokens: int = 2048) -> str:
        if len(prompt) > MAX_PROMPT_LENGTH:
            prompt = prompt[:MAX_PROMPT_LENGTH] + "...[content truncated for analysis]"
            
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 50,
                "num_predict": max_tokens,
                "repeat_penalty": 1.1,
                "num_ctx": 8192
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '').strip()
                else:
                    error_text = await response.text()
                    return f"HTTP Error {response.status}: {error_text}"
        except asyncio.TimeoutError:
            return "Error: Request timeout"
        except Exception as e:
            return f"Connection Error: {str(e)}"

    async def analyze_document_intelligence(self, text: str) -> DocumentAnalysis:
        system_prompt = """You are an expert policy and legal document analyst. Analyze documents with deep understanding of organizational policies, legal frameworks, and regulatory requirements."""
        
        text_sample = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""Analyze this document comprehensively and provide a detailed assessment:

DOCUMENT CONTENT:
{text_sample}

Provide analysis in this exact JSON format:
{{
    "document_type": "[POLICY/LAW/REGULATION/STANDARD/CONTRACT/GUIDELINE/FRAMEWORK/DECREE/CODE/CIRCULAR/NOTICE]",
    "title": "[descriptive document title]",
    "structure_quality": "[EXCELLENT/GOOD/FAIR/POOR]",
    "content_density": "[HIGH/MEDIUM/LOW]",
    "semantic_themes": ["theme1", "theme2", "theme3"],
    "key_sections": ["section1", "section2", "section3"],
    "regulatory_references": ["ref1", "ref2"],
    "language_quality": "[PROFESSIONAL/STANDARD/INFORMAL]"
}}

Analyze the document's purpose, structure, content quality, and key themes. Focus on organizational policy elements, legal requirements, and regulatory compliance aspects."""

        try:
            response = await self.generate_with_context(prompt, system_prompt, 1024)
            return self._parse_document_analysis(response, text)
        except Exception as e:
            print(f"❌ Document analysis error: {e}")
            return self._create_fallback_document_analysis(text)

    def _parse_document_analysis(self, response: str, original_text: str) -> DocumentAnalysis:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                
                return DocumentAnalysis(
                    document_type=DocumentType(analysis.get('document_type', 'POLICY')),
                    title=analysis.get('title', 'Policy Document')[:200],
                    structure_quality=analysis.get('structure_quality', 'FAIR'),
                    content_density=analysis.get('content_density', 'MEDIUM'),
                    semantic_themes=analysis.get('semantic_themes', [])[:10],
                    key_sections=analysis.get('key_sections', [])[:15],
                    regulatory_references=analysis.get('regulatory_references', [])[:10],
                    language_quality=analysis.get('language_quality', 'STANDARD')
                )
        except Exception as e:
            print(f"⚠️ Error parsing document analysis: {e}")
        
        return self._create_fallback_document_analysis(original_text)

    def _create_fallback_document_analysis(self, text: str) -> DocumentAnalysis:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["policy", "procedure", "manual"]):
            doc_type = DocumentType.POLICY
        elif any(word in text_lower for word in ["law", "act", "statute"]):
            doc_type = DocumentType.LAW
        elif any(word in text_lower for word in ["regulation", "rule", "code"]):
            doc_type = DocumentType.REGULATION
        else:
            doc_type = DocumentType.POLICY
            
        return DocumentAnalysis(
            document_type=doc_type,
            title="Document Analysis",
            structure_quality="FAIR",
            content_density="MEDIUM",
            semantic_themes=["policy", "organizational"],
            key_sections=["general provisions"],
            regulatory_references=[],
            language_quality="STANDARD"
        )

    async def analyze_criteria_coverage(self, policy_text: str, regulatory_texts: List[str], 
                                      document_analysis: DocumentAnalysis) -> List[CriteriaAnalysis]:
        print(f"🎯 Analyzing coverage for {len(self.criteria_framework)} criteria...")
        
        results = []
        semaphore = asyncio.Semaphore(2)
        
        async def analyze_single_criteria(criteria):
            async with semaphore:
                try:
                    result = await self._analyze_single_criteria_intelligent(
                        criteria, policy_text, regulatory_texts, document_analysis
                    )
                    return result
                except Exception as e:
                    print(f"❌ Error analyzing {criteria['name']}: {e}")
                    return self._create_fallback_criteria_analysis(criteria)
        
        tasks = [analyze_single_criteria(criteria) for criteria in self.criteria_framework]
        results = await asyncio.gather(*tasks)
        
        print(f"✅ Completed criteria analysis: {len(results)} results")
        return results

    async def _analyze_single_criteria_intelligent(self, criteria: Dict, policy_text: str, 
                                                 regulatory_texts: List[str], 
                                                 document_analysis: DocumentAnalysis) -> CriteriaAnalysis:
        
        system_prompt = f"""You are an expert policy analyst specializing in {criteria['name']}. 
        Analyze documents for comprehensive coverage of this specific area with deep understanding of organizational requirements and regulatory compliance."""
        
        regulatory_context = "\n---\n".join(regulatory_texts[:3])[:2000] if regulatory_texts else "No regulatory context provided"
        policy_sample = policy_text[:2000] if len(policy_text) > 2000 else policy_text
        
        prompt = f"""Analyze this policy document for coverage of: {criteria['name']}

CRITERIA DESCRIPTION: {criteria['description']}
KEY FOCUS AREAS: {', '.join(criteria['keywords'])}

POLICY DOCUMENT:
{policy_sample}

REGULATORY CONTEXT:
{regulatory_context}

Provide analysis in this exact JSON format:
{{
    "status": "[PRESENT/PARTIAL/MISSING]",
    "confidence": "[HIGH/MEDIUM/LOW]",
    "coverage_percentage": [0-100],
    "found_content": ["specific provision 1", "specific provision 2"],
    "missing_elements": ["missing element 1", "missing element 2"],
    "quality_assessment": "[detailed quality assessment]",
    "recommendations": ["recommendation 1", "recommendation 2"],
    "regulatory_alignment": "[alignment assessment with regulations]",
    "implementation_priority": "[HIGH/MEDIUM/LOW]"
}}

ANALYSIS GUIDELINES:
- PRESENT: Comprehensive coverage with clear provisions
- PARTIAL: Some coverage but significant gaps exist
- MISSING: No meaningful coverage found
- Focus on substance over keywords
- Consider regulatory compliance requirements
- Provide specific, actionable recommendations"""

        try:
            response = await self.generate_with_context(prompt, system_prompt, 1536)
            return self._parse_criteria_analysis(response, criteria)
        except Exception as e:
            print(f"⚠️ Error in criteria analysis for {criteria['name']}: {e}")
            return self._create_fallback_criteria_analysis(criteria)

    def _parse_criteria_analysis(self, response: str, criteria: Dict) -> CriteriaAnalysis:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                
                status_str = analysis.get('status', 'MISSING').upper()
                if status_str not in ['PRESENT', 'PARTIAL', 'MISSING']:
                    status_str = 'MISSING'
                
                confidence_str = analysis.get('confidence', 'MEDIUM').upper()
                if confidence_str not in ['HIGH', 'MEDIUM', 'LOW']:
                    confidence_str = 'MEDIUM'
                
                coverage = analysis.get('coverage_percentage', 0)
                if not isinstance(coverage, (int, float)) or coverage < 0 or coverage > 100:
                    coverage = 50 if status_str == 'PARTIAL' else 0 if status_str == 'MISSING' else 80
                
                return CriteriaAnalysis(
                    criteria_id=criteria['id'],
                    criteria_name=criteria['name'],
                    status=CriteriaStatus(status_str),
                    confidence=ConfidenceLevel(confidence_str),
                    coverage_percentage=float(coverage),
                    found_content=analysis.get('found_content', [])[:5],
                    missing_elements=analysis.get('missing_elements', [])[:5],
                    quality_assessment=analysis.get('quality_assessment', 'Assessment completed')[:500],
                    recommendations=analysis.get('recommendations', [])[:3],
                    regulatory_alignment=analysis.get('regulatory_alignment', 'Review required')[:300],
                    implementation_priority=analysis.get('implementation_priority', 'MEDIUM')
                )
        except Exception as e:
            print(f"⚠️ Error parsing criteria analysis: {e}")
        
        return self._create_fallback_criteria_analysis(criteria)

    def _create_fallback_criteria_analysis(self, criteria: Dict) -> CriteriaAnalysis:
        return CriteriaAnalysis(
            criteria_id=criteria['id'],
            criteria_name=criteria['name'],
            status=CriteriaStatus.MISSING,
            confidence=ConfidenceLevel.LOW,
            coverage_percentage=0.0,
            found_content=[],
            missing_elements=[f"{criteria['name']} provisions not found"],
            quality_assessment=f"Analysis of {criteria['name']} could not be completed",
            recommendations=[f"Professional review recommended for {criteria['name']}"],
            regulatory_alignment="Professional assessment needed",
            implementation_priority="HIGH"
        )

    async def generate_strategic_assessment(self, criteria_results: List[CriteriaAnalysis], 
                                          document_analysis: DocumentAnalysis) -> Dict[str, Any]:
        system_prompt = """You are a senior policy strategist and organizational development expert. 
        Provide executive-level strategic recommendations based on comprehensive policy analysis."""
        
        present_criteria = [c for c in criteria_results if c.status == CriteriaStatus.PRESENT]
        partial_criteria = [c for c in criteria_results if c.status == CriteriaStatus.PARTIAL]
        missing_criteria = [c for c in criteria_results if c.status == CriteriaStatus.MISSING]
        
        overall_coverage = sum(c.coverage_percentage for c in criteria_results) / len(criteria_results)
        
        summary = f"""
ANALYSIS SUMMARY:
- Total Criteria: {len(criteria_results)}
- Present: {len(present_criteria)} ({len(present_criteria)/len(criteria_results)*100:.1f}%)
- Partial: {len(partial_criteria)} ({len(partial_criteria)/len(criteria_results)*100:.1f}%)
- Missing: {len(missing_criteria)} ({len(missing_criteria)/len(criteria_results)*100:.1f}%)
- Overall Coverage: {overall_coverage:.1f}%

MISSING CRITERIA:
{', '.join([c.criteria_name for c in missing_criteria]) if missing_criteria else 'None'}

PARTIAL COVERAGE:
{', '.join([c.criteria_name for c in partial_criteria]) if partial_criteria else 'None'}
"""

        prompt = f"""Based on this policy analysis, provide strategic recommendations:

{summary}

Generate response in this exact JSON format:
{{
    "maturity_score": [0-100],
    "compliance_gaps": ["gap1", "gap2", "gap3"],
    "strategic_recommendations": ["recommendation1", "recommendation2", "recommendation3"],
    "implementation_roadmap": ["phase1", "phase2", "phase3"],
    "regulatory_summary": {{
        "compliance_level": "[EXCELLENT/GOOD/NEEDS_IMPROVEMENT/POOR]",
        "key_risks": ["risk1", "risk2"],
        "priority_actions": ["action1", "action2"]
    }}
}}

Focus on executive-level strategic guidance for organizational improvement and regulatory compliance."""

        try:
            response = await self.generate_with_context(prompt, system_prompt, 1024)
            return self._parse_strategic_assessment(response, overall_coverage)
        except Exception as e:
            print(f"⚠️ Error generating strategic assessment: {e}")
            return self._create_fallback_strategic_assessment(overall_coverage)

    def _parse_strategic_assessment(self, response: str, coverage_score: float) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                assessment = json.loads(json_match.group(0))
                
                maturity_score = assessment.get('maturity_score', coverage_score)
                if not isinstance(maturity_score, (int, float)) or maturity_score < 0 or maturity_score > 100:
                    maturity_score = coverage_score
                
                return {
                    'maturity_score': float(maturity_score),
                    'compliance_gaps': assessment.get('compliance_gaps', [])[:5],
                    'strategic_recommendations': assessment.get('strategic_recommendations', [])[:5],
                    'implementation_roadmap': assessment.get('implementation_roadmap', [])[:5],
                    'regulatory_summary': assessment.get('regulatory_summary', {
                        'compliance_level': 'NEEDS_IMPROVEMENT',
                        'key_risks': ['Professional review required'],
                        'priority_actions': ['Conduct comprehensive assessment']
                    })
                }
        except Exception as e:
            print(f"⚠️ Error parsing strategic assessment: {e}")
        
        return self._create_fallback_strategic_assessment(coverage_score)

    def _create_fallback_strategic_assessment(self, coverage_score: float) -> Dict[str, Any]:
        return {
            'maturity_score': coverage_score,
            'compliance_gaps': ['Comprehensive policy review required'],
            'strategic_recommendations': [
                'Conduct professional policy assessment',
                'Implement missing policy frameworks',
                'Establish governance mechanisms'
            ],
            'implementation_roadmap': [
                'Phase 1: Assessment and gap analysis',
                'Phase 2: Policy development and implementation', 
                'Phase 3: Monitoring and continuous improvement'
            ],
            'regulatory_summary': {
                'compliance_level': 'NEEDS_IMPROVEMENT',
                'key_risks': ['Regulatory non-compliance risks'],
                'priority_actions': ['Professional consultation recommended']
            }
        }

    async def close(self):
        if self.session:
            await self.session.close()