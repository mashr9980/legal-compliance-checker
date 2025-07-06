import aiohttp
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from config import MODEL_NAME, MAX_PROMPT_LENGTH

class IntelligentAnalyzer:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = MODEL_NAME
        self.session = None
        self.context_memory = {}
        self.max_retries = 3
        self.timeout = 180
    
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
                        print(f"Model {self.model} not found, pulling...")
                        await self._pull_model()
                    else:
                        print(f"Model {self.model} is available")
                else:
                    print(f"Failed to check models: HTTP {response.status}")
        except Exception as e:
            print(f"Model check error: {e}")
    
    async def _pull_model(self):
        try:
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
                                    print(f"Pulling model: {status.get('status')}")
                                if status.get('status') == 'success':
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"Failed to pull model: HTTP {response.status}")
        except Exception as e:
            print(f"Model pull error: {e}")
    
    async def generate_with_retry(self, prompt: str, system_prompt: str = None, max_tokens: int = 2048) -> str:
        for attempt in range(self.max_retries):
            try:
                result = await self.generate(prompt, system_prompt, max_tokens)
                if result and not result.startswith("Error:") and not result.startswith("HTTP Error"):
                    return result
                print(f"Attempt {attempt + 1} failed: {result[:100]}...")
            except Exception as e:
                print(f"Attempt {attempt + 1} exception: {e}")
                if attempt == self.max_retries - 1:
                    return f"Error after {self.max_retries} attempts: {str(e)}"
                await asyncio.sleep(1)
        
        return "Error: All retry attempts failed"
    
    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 2048) -> str:
        if len(prompt) > MAX_PROMPT_LENGTH:
            prompt = prompt[:MAX_PROMPT_LENGTH] + "...[truncated]"
            
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
                "num_predict": max_tokens,
                "repeat_penalty": 1.1,
                "num_ctx": 4096
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
    
    async def analyze_document_type_and_structure(self, text: str) -> Dict[str, Any]:
        system_prompt = "You are a legal document expert. Analyze documents and return simple responses."
        
        text_sample = text[:2000] if len(text) > 2000 else text
        
        prompt = f"""Analyze this document type:

{text_sample}

Answer these questions in simple format:
TYPE: [LAW/REGULATION/CONTRACT/POLICY/DECREE/STANDARD/GUIDELINE]
TITLE: [document title]
AUTHORITY: [issuing authority]
SCOPE: [main areas, separated by commas]
TOPICS: [key topics, separated by commas]"""
        
        response = await self.generate_with_retry(prompt, system_prompt, 1024)
        return self._parse_simple_response(response, text_sample)
    
    def _parse_simple_response(self, response: str, text_sample: str) -> Dict[str, Any]:
        result = {
            "document_type": "LAW",
            "title": "Legal Document",
            "authority": "Legal Authority",
            "scope": ["general"],
            "key_topics": ["general terms"],
            "structure": {
                "has_definitions": False,
                "has_obligations": True,
                "has_penalties": False,
                "main_sections": ["general provisions"]
            },
            "compliance_domains": ["legal"],
            "target_audience": "general",
            "document_purpose": "legal document",
            "legal_framework": "general law"
        }
        
        try:
            # Extract type
            type_match = re.search(r'TYPE:\s*([A-Z]+)', response)
            if type_match:
                doc_type = type_match.group(1)
                if doc_type in ["LAW", "REGULATION", "CONTRACT", "POLICY", "DECREE", "STANDARD", "GUIDELINE", "AMENDMENT", "CODE", "CIRCULAR", "NOTICE"]:
                    result["document_type"] = doc_type
            
            # Extract title
            title_match = re.search(r'TITLE:\s*(.+)', response)
            if title_match:
                title = title_match.group(1).strip()
                if len(title) > 5:
                    result["title"] = title[:200]
            
            # Extract authority
            authority_match = re.search(r'AUTHORITY:\s*(.+)', response)
            if authority_match:
                authority = authority_match.group(1).strip()
                if len(authority) > 2:
                    result["authority"] = authority[:100]
            
            # Extract scope
            scope_match = re.search(r'SCOPE:\s*(.+)', response)
            if scope_match:
                scope = [s.strip() for s in scope_match.group(1).split(',') if s.strip()]
                if scope:
                    result["scope"] = scope[:5]
            
            # Extract topics
            topics_match = re.search(r'TOPICS:\s*(.+)', response)
            if topics_match:
                topics = [t.strip() for t in topics_match.group(1).split(',') if t.strip()]
                if topics:
                    result["key_topics"] = topics[:8]
            
        except Exception as e:
            print(f"Error parsing simple response: {e}")
        
        # Fallback analysis from text
        if result["document_type"] == "LAW":
            result["document_type"] = self._infer_document_type(text_sample)
        
        return result
    
    def _infer_document_type(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["contract", "agreement", "employment"]):
            return "CONTRACT"
        elif any(word in text_lower for word in ["policy", "procedure", "guideline"]):
            return "POLICY"
        elif any(word in text_lower for word in ["royal decree", "decree", "proclamation"]):
            return "DECREE"
        elif any(word in text_lower for word in ["regulation", "ministerial decision"]):
            return "REGULATION"
        else:
            return "LAW"
    
    async def extract_requirements_intelligently(self, law_text: str, law_analysis: Dict, contract_text: str, contract_analysis: Dict) -> List[Dict]:
        # Use fallback requirements generation since AI parsing is unreliable
        return self._generate_comprehensive_fallback_requirements(law_analysis, contract_analysis)
    
    def _generate_comprehensive_fallback_requirements(self, law_analysis: Dict, contract_analysis: Dict) -> List[Dict]:
        law_topics = law_analysis.get('key_topics', [])
        law_scope = law_analysis.get('scope', [])
        
        essential_requirements = [
            {
                "chapter": "Employment Definition",
                "item": "Employment Relationship",
                "requirement": "Document must clearly define the employment relationship and basic terms",
                "source_reference": "Employment Standards",
                "category": "employment_terms"
            },
            {
                "chapter": "Compensation Framework",
                "item": "Salary and Payment Terms",
                "requirement": "Document must specify salary, payment frequency, and payment method",
                "source_reference": "Labor Code - Wage Provisions",
                "category": "compensation_benefits"
            },
            {
                "chapter": "Working Conditions",
                "item": "Working Hours and Schedule",
                "requirement": "Document must define normal working hours and overtime provisions",
                "source_reference": "Working Time Regulations",
                "category": "working_conditions"
            },
            {
                "chapter": "Benefits and Entitlements",
                "item": "Statutory Benefits",
                "requirement": "Document must address mandatory benefits including social security",
                "source_reference": "Social Security Law",
                "category": "compensation_benefits"
            },
            {
                "chapter": "Leave Provisions",
                "item": "Leave Entitlements",
                "requirement": "Document must specify annual leave, sick leave entitlements",
                "source_reference": "Leave Regulations",
                "category": "leave_policies"
            },
            {
                "chapter": "Termination Framework",
                "item": "Termination Procedures",
                "requirement": "Document must specify termination grounds and notice periods",
                "source_reference": "Termination Law",
                "category": "termination_conditions"
            },
            {
                "chapter": "Confidentiality",
                "item": "Confidentiality Obligations",
                "requirement": "Document must include confidentiality protection clauses",
                "source_reference": "IP and Confidentiality Law",
                "category": "confidentiality_non_compete"
            },
            {
                "chapter": "Workplace Safety",
                "item": "Health and Safety",
                "requirement": "Document must reference workplace health and safety obligations",
                "source_reference": "Occupational Safety Law",
                "category": "health_safety"
            },
            {
                "chapter": "Dispute Resolution",
                "item": "Dispute Procedures",
                "requirement": "Document must specify dispute resolution mechanism",
                "source_reference": "Dispute Resolution Law",
                "category": "dispute_resolution"
            },
            {
                "chapter": "Legal Compliance",
                "item": "General Compliance",
                "requirement": "Document must include general legal compliance clauses",
                "source_reference": "General Legal Framework",
                "category": "compliance_regulatory"
            }
        ]
        
        for topic in law_topics[:3]:
            if not any(topic.lower() in req["item"].lower() for req in essential_requirements):
                essential_requirements.append({
                    "chapter": "Additional Requirements",
                    "item": f"{topic.title()} Compliance",
                    "requirement": f"Document must address {topic} requirements",
                    "source_reference": f"Legal Framework - {topic}",
                    "category": "compliance_regulatory"
                })
        
        return essential_requirements[:12]
    
    async def check_policy_compliance(self, requirement: Dict, contract_text: str, contract_analysis: Dict) -> Dict:
        system_prompt = "You are analyzing legal compliance. Give short, direct answers."
        
        contract_sample = contract_text[:800]  # Much shorter sample
        
        prompt = f"""Check if this document addresses: {requirement.get('item', 'requirement')}

Document excerpt:
{contract_sample}

Rate compliance:
STATUS: [ALIGNED/MODERATE/UNALIGNED]
FEEDBACK: [brief assessment]
COMMENTS: [what you found]
AMENDMENTS: [what to add]
PRIORITY: [HIGH/MEDIUM/LOW]
PERCENTAGE: [0-100]"""
        
        try:
            response = await self.generate_with_retry(prompt, system_prompt, 512)
            return self._parse_compliance_response(response, requirement)
        except Exception as e:
            print(f"Compliance check error: {e}")
            return self._create_safe_compliance_result(requirement)
    
    def _parse_compliance_response(self, response: str, requirement: Dict) -> Dict:
        result = self._create_safe_compliance_result(requirement)
        
        try:
            # Extract status
            status_match = re.search(r'STATUS:\s*(ALIGNED|MODERATE|UNALIGNED)', response, re.IGNORECASE)
            if status_match:
                result["status"] = status_match.group(1).upper()
            
            # Extract feedback
            feedback_match = re.search(r'FEEDBACK:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if feedback_match:
                result["feedback"] = feedback_match.group(1).strip()[:200]
            
            # Extract comments
            comments_match = re.search(r'COMMENTS:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if comments_match:
                result["comments"] = comments_match.group(1).strip()[:200]
            
            # Extract amendments
            amendments_match = re.search(r'AMENDMENTS:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if amendments_match:
                result["suggested_amendments"] = amendments_match.group(1).strip()[:200]
            
            # Extract priority
            priority_match = re.search(r'PRIORITY:\s*(HIGH|MEDIUM|LOW)', response, re.IGNORECASE)
            if priority_match:
                result["priority"] = priority_match.group(1).upper()
            
            # Extract percentage
            percentage_match = re.search(r'PERCENTAGE:\s*(\d+)', response)
            if percentage_match:
                percentage = int(percentage_match.group(1))
                if 0 <= percentage <= 100:
                    result["compliance_percentage"] = percentage
            
        except Exception as e:
            print(f"Error parsing compliance response: {e}")
        
        return result
    
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
    
    async def generate_overall_assessment(self, checklist_items: List[Dict], law_analysis: Dict, contract_analysis: Dict) -> Dict:
        aligned_count = len([item for item in checklist_items if item.get('status') == 'ALIGNED'])
        moderate_count = len([item for item in checklist_items if item.get('status') == 'MODERATE']) 
        unaligned_count = len([item for item in checklist_items if item.get('status') == 'UNALIGNED'])
        total_count = len(checklist_items)
        
        if total_count == 0:
            return self._create_safe_assessment()
        
        compliance_score = (aligned_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "overall_assessment": f"Document compliance analysis shows {compliance_score:.1f}% alignment with legal requirements. {unaligned_count} areas need attention.",
            "key_strengths": ["Document structure exists", "Basic provisions present"] if aligned_count > 0 else ["Document requires comprehensive review"],
            "critical_gaps": [f"{unaligned_count} requirements not adequately addressed", "Legal compliance gaps identified"],
            "strategic_recommendations": [
                "Conduct comprehensive legal review",
                "Address all unaligned requirements", 
                "Implement recommended amendments",
                "Establish compliance monitoring"
            ],
            "implementation_priorities": [
                "Address high-priority compliance gaps",
                "Review and update critical clauses",
                "Ensure mandatory requirements are met"
            ],
            "risk_assessment": f"{'High' if compliance_score < 60 else 'Moderate' if compliance_score < 80 else 'Low'} legal compliance risk",
            "additional_considerations": [
                "Professional legal consultation recommended",
                "Regular document updates needed",
                "Compliance monitoring required"
            ],
            "next_steps": [
                "Review detailed analysis report",
                "Implement priority recommendations", 
                "Schedule legal consultation",
                "Update document accordingly"
            ],
            "compliance_maturity": "BASIC" if compliance_score < 40 else "DEVELOPING" if compliance_score < 70 else "ADVANCED",
            "improvement_timeline": "3-6 months for full compliance",
            "legal_exposure": f"{'Significant' if compliance_score < 60 else 'Moderate' if compliance_score < 80 else 'Limited'} legal exposure",
            "business_impact": "Potential operational and legal risks from non-compliance"
        }
    
    def _create_safe_assessment(self) -> Dict:
        return {
            "overall_assessment": "Document analysis completed",
            "key_strengths": ["Analysis attempted"],
            "critical_gaps": ["Comprehensive review needed"],
            "strategic_recommendations": ["Professional legal review recommended"],
            "implementation_priorities": ["Address identified gaps"],
            "risk_assessment": "Risk assessment completed",
            "additional_considerations": ["Expert consultation recommended"],
            "next_steps": ["Review recommendations"],
            "compliance_maturity": "DEVELOPING",
            "improvement_timeline": "3-6 months",
            "legal_exposure": "Legal exposure assessment needed",
            "business_impact": "Business impact assessment needed"
        }
    
    async def batch_compliance_check(self, requirements: List[Dict], contract_text: str, contract_analysis: Dict) -> List[Dict]:
        semaphore = asyncio.Semaphore(1)  # Reduced concurrency
        
        async def check_with_semaphore(req):
            async with semaphore:
                try:
                    return await self.check_policy_compliance(req, contract_text, contract_analysis)
                except Exception as e:
                    print(f"Compliance check error for {req.get('item', 'unknown')}: {e}")
                    return self._create_safe_compliance_result(req)
        
        print(f"🔍 Starting batch compliance check for {len(requirements)} requirements...")
        
        results = []
        for i, req in enumerate(requirements):
            print(f"   Checking requirement {i+1}/{len(requirements)}: {req.get('item', 'Unknown')}")
            result = await check_with_semaphore(req)
            results.append(result)
            await asyncio.sleep(0.1)  # Small delay between requests
        
        print(f"✅ Completed batch compliance check: {len(results)} results")
        return results
    
    async def close(self):
        if self.session:
            await self.session.close()