import aiohttp
import asyncio
import json
import re
from typing import Dict, List, Optional, Any

class IntelligentAnalyzer:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen2.5:3b"
        self.session = None
        self.context_memory = {}
    
    async def initialize(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            connector=aiohttp.TCPConnector(limit=10)
        )
        await self._ensure_model_available()
    
    async def _ensure_model_available(self):
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                models = await response.json()
                model_names = [model['name'] for model in models.get('models', [])]
                if self.model not in model_names:
                    await self._pull_model()
        except Exception as e:
            print(f"Model check error: {e}")
    
    async def _pull_model(self):
        try:
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model}
            ) as response:
                async for line in response.content:
                    if line:
                        status = json.loads(line.decode())
                        if status.get('status') == 'success':
                            break
        except Exception as e:
            print(f"Model pull error: {e}")
    
    async def generate(self, prompt: str, system_prompt: str = None, context: str = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 4096
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if context:
            payload["context"] = context
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '').strip()
                else:
                    return f"Error: HTTP {response.status}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def analyze_document_type_and_structure(self, text: str) -> Dict[str, Any]:
        system_prompt = """You are an expert document analyzer. Analyze any type of document and determine its nature, structure, and key components."""
        
        prompt = f"""Analyze this document and provide a comprehensive analysis:

DOCUMENT TEXT:
{text[:3000]}

Analyze and return ONLY this JSON structure:
{{
    "document_type": "POLICY|LAW|REGULATION|STANDARD|CONTRACT|GUIDELINE",
    "title": "document title",
    "authority": "issuing authority or organization",
    "scope": ["area1", "area2", "area3"],
    "key_topics": ["topic1", "topic2", "topic3"],
    "structure": {{
        "chapters": ["chapter1", "chapter2"],
        "sections": ["section1", "section2"],
        "main_areas": ["area1", "area2"]
    }},
    "compliance_domains": ["domain1", "domain2"],
    "regulatory_framework": "applicable framework",
    "target_audience": "who this applies to"
}}

Determine document type based on:
- POLICY: organizational policies, procedures, guidelines
- LAW: legal statutes, acts, legislation
- REGULATION: regulatory requirements, compliance rules
- STANDARD: industry standards, best practices
- CONTRACT: agreements, terms of service
- GUIDELINE: guidance documents, recommendations"""
        
        response = await self.generate(prompt, system_prompt)
        return self._parse_json_response(response)
    
    async def extract_requirements_intelligently(self, doc1_text: str, doc1_analysis: Dict, doc2_text: str, doc2_analysis: Dict) -> List[Dict]:
        system_prompt = """You are an expert policy analyst. Compare two documents and extract comprehensive requirements for policy compliance checking."""
        
        prompt = f"""You have two documents to analyze:

DOCUMENT 1: {doc1_analysis.get('document_type', 'Unknown')} - {doc1_analysis.get('title', 'Unknown')}
SCOPE: {', '.join(doc1_analysis.get('scope', []))}
KEY TOPICS: {', '.join(doc1_analysis.get('key_topics', []))}

DOCUMENT 2: {doc2_analysis.get('document_type', 'Unknown')} - {doc2_analysis.get('title', 'Unknown')}
SCOPE: {', '.join(doc2_analysis.get('scope', []))}
KEY TOPICS: {', '.join(doc2_analysis.get('key_topics', []))}

DOCUMENT 1 TEXT:
{doc1_text[:2500]}

DOCUMENT 2 TEXT:
{doc2_text[:2500]}

Extract comprehensive policy checklist items by comparing these documents. Return ONLY this JSON array:
[
    {{
        "chapter": "extracted chapter/section name",
        "item": "specific item or provision",
        "requirement": "what must be done or checked",
        "source_reference": "where this comes from",
        "category": "category of requirement",
        "mandatory": true/false,
        "criteria": "how to measure compliance",
        "expected_content": "what should be present"
    }}
]

Extract requirements based on:
- Explicit obligations and prohibitions
- Structural requirements (what sections must exist)
- Content requirements (what information must be included)  
- Process requirements (what procedures must be followed)
- Compliance standards and thresholds
- Documentation requirements
- Governance and oversight requirements

Cover all major areas found in the documents."""
        
        response = await self.generate(prompt, system_prompt)
        return self._parse_json_array_response(response)
    
    async def check_policy_compliance(self, requirement: Dict, target_doc_text: str, target_doc_analysis: Dict) -> Dict:
        system_prompt = """You are a policy compliance expert. Assess whether a document meets specific requirements and provide detailed feedback."""
        
        prompt = f"""Check compliance of this document against a specific requirement:

TARGET DOCUMENT: {target_doc_analysis.get('document_type', 'Unknown')} - {target_doc_analysis.get('title', 'Unknown')}

REQUIREMENT TO CHECK:
Chapter: {requirement.get('chapter', '')}
Item: {requirement.get('item', '')}
Requirement: {requirement.get('requirement', '')}
Expected Content: {requirement.get('expected_content', '')}
Criteria: {requirement.get('criteria', '')}

DOCUMENT TEXT TO ANALYZE:
{target_doc_text[:3000]}

Analyze compliance and return ONLY this JSON:
{{
    "status": "ALIGNED|MODERATE|UNALIGNED",
    "feedback": "overall assessment of this requirement",
    "comments": "specific observations about current state",
    "suggested_amendments": "specific improvements needed",
    "current_content": "what currently exists (if any)",
    "gap_analysis": "what is missing or inadequate",
    "priority": "HIGH|MEDIUM|LOW",
    "compliance_percentage": 85
}}

Status definitions:
- ALIGNED: Requirement fully met, no changes needed
- MODERATE: Partially met, minor improvements needed
- UNALIGNED: Not met, significant changes required

Be specific and actionable in feedback and suggestions."""
        
        response = await self.generate(prompt, system_prompt)
        return self._parse_json_response(response)
    
    async def generate_overall_assessment(self, checklist_items: List[Dict], doc1_analysis: Dict, doc2_analysis: Dict) -> Dict:
        aligned_count = len([item for item in checklist_items if item.get('status') == 'ALIGNED'])
        moderate_count = len([item for item in checklist_items if item.get('status') == 'MODERATE']) 
        unaligned_count = len([item for item in checklist_items if item.get('status') == 'UNALIGNED'])
        total_count = len(checklist_items)
        
        system_prompt = """You are a senior policy advisor. Provide executive-level assessment and strategic recommendations."""
        
        categories = {}
        high_priority_issues = []
        
        for item in checklist_items:
            category = item.get('category', 'General')
            if category not in categories:
                categories[category] = {'aligned': 0, 'moderate': 0, 'unaligned': 0}
            categories[category][item.get('status', 'unaligned').lower()] += 1
            
            if item.get('priority') == 'HIGH' and item.get('status') in ['MODERATE', 'UNALIGNED']:
                high_priority_issues.append(item)
        
        prompt = f"""Generate comprehensive assessment for policy compliance analysis:

ANALYSIS CONTEXT:
Reference Document: {doc1_analysis.get('document_type')} - {doc1_analysis.get('title')}
Target Document: {doc2_analysis.get('document_type')} - {doc2_analysis.get('title')}

COMPLIANCE STATISTICS:
Total Items Checked: {total_count}
Aligned: {aligned_count} ({aligned_count/total_count*100:.1f}% if total_count > 0 else 0)
Moderate: {moderate_count} ({moderate_count/total_count*100:.1f}% if total_count > 0 else 0)
Unaligned: {unaligned_count} ({unaligned_count/total_count*100:.1f}% if total_count > 0 else 0)

HIGH PRIORITY ISSUES: {len(high_priority_issues)}

CATEGORY BREAKDOWN:
{json.dumps(categories, indent=2)}

Generate ONLY this JSON:
{{
    "overall_assessment": "executive summary of compliance status",
    "key_strengths": ["strength1", "strength2", "strength3"],
    "critical_gaps": ["gap1", "gap2", "gap3"],
    "strategic_recommendations": ["rec1", "rec2", "rec3"],
    "implementation_priorities": ["priority1", "priority2", "priority3"],
    "risk_assessment": "assessment of risks from non-compliance",
    "additional_considerations": ["consideration1", "consideration2"],
    "next_steps": ["step1", "step2", "step3"],
    "compliance_maturity": "BASIC|DEVELOPING|ADVANCED|LEADING",
    "improvement_timeline": "suggested timeframe for addressing issues"
}}

Provide strategic, actionable insights suitable for senior management."""
        
        response = await self.generate(prompt, system_prompt)
        return self._parse_json_response(response)
    
    async def batch_compliance_check(self, requirements: List[Dict], target_doc_text: str, target_doc_analysis: Dict) -> List[Dict]:
        semaphore = asyncio.Semaphore(3)
        
        async def check_with_semaphore(req):
            async with semaphore:
                return await self.check_policy_compliance(req, target_doc_text, target_doc_analysis)
        
        tasks = [check_with_semaphore(req) for req in requirements]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _parse_json_response(self, response: str) -> Dict:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        return {}
    
    def _parse_json_array_response(self, response: str) -> List[Dict]:
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                if isinstance(result, list):
                    return result
        except:
            pass
        return []
    
    async def close(self):
        if self.session:
            await self.session.close()