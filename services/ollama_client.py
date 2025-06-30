import aiohttp
import asyncio
import json
from typing import Dict, List, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen3:1.7b"
        self.session = None
    
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
            print(f"Error checking models: {e}")
    
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
            print(f"Error pulling model: {e}")
    
    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 2048,
                "stop": ["</analysis>", "END"]
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
                    return f"Error: HTTP {response.status}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def extract_requirements(self, legal_text: str) -> List[Dict]:
        system_prompt = """You are a legal analyst. Extract specific, actionable requirements from legal documents.
Focus on mandatory obligations, prohibited actions, specific conditions, and measurable criteria.
Return only a JSON array of requirements."""
        
        prompt = f"""Analyze this legal document and extract all specific requirements:

{legal_text[:3000]}

Extract requirements in this JSON format:
[
  {{
    "id": "REQ001",
    "description": "Clear requirement description",
    "category": "termination|payment|leave|confidentiality|liability|other",
    "source_section": "Section/Article reference",
    "mandatory": true/false,
    "criteria": "Specific measurable criteria if applicable"
  }}
]

Focus on:
- Mandatory clauses that must be included
- Prohibited terms or conditions  
- Specific timeframes, amounts, or percentages
- Required procedures or processes

Return only the JSON array, no other text."""
        
        response = await self.generate(prompt, system_prompt)
        
        try:
            requirements = json.loads(response)
            if isinstance(requirements, list):
                return requirements
        except json.JSONDecodeError:
            pass
        
        return []
    
    async def check_compliance(self, requirement: Dict, contract_text: str) -> Dict:
        system_prompt = """You are a legal compliance checker. Compare contract clauses against legal requirements.
Provide precise compliance assessment with specific recommendations."""
        
        prompt = f"""Check compliance of this contract against the legal requirement:

LEGAL REQUIREMENT:
Description: {requirement.get('description', '')}
Category: {requirement.get('category', '')}
Mandatory: {requirement.get('mandatory', False)}
Criteria: {requirement.get('criteria', 'N/A')}

CONTRACT TEXT (relevant sections):
{contract_text[:2000]}

Analyze and return ONLY this JSON format:
{{
  "status": "COMPLIANT|NON_COMPLIANT|PARTIAL",
  "current_text": "exact text from contract or null",
  "issue_description": "what is wrong/missing or null if compliant",
  "recommendation": "specific suggested change or null if compliant",
  "risk_level": "HIGH|MEDIUM|LOW",
  "confidence": 0.8
}}

Rules:
- COMPLIANT: Requirement fully met
- NON_COMPLIANT: Requirement missing or contradicted
- PARTIAL: Requirement addressed but incomplete
- Be specific in recommendations
- Quote exact contract text when possible"""
        
        response = await self.generate(prompt, system_prompt)
        
        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            "status": "NON_COMPLIANT",
            "current_text": None,
            "issue_description": "Analysis failed",
            "recommendation": "Manual review required",
            "risk_level": "MEDIUM",
            "confidence": 0.0
        }
    
    async def batch_check_compliance(self, requirements: List[Dict], contract_text: str) -> List[Dict]:
        tasks = []
        semaphore = asyncio.Semaphore(3)
        
        async def check_with_semaphore(req):
            async with semaphore:
                return await self.check_compliance(req, contract_text)
        
        for req in requirements:
            tasks.append(check_with_semaphore(req))
        
        return await asyncio.gather(*tasks)
    
    async def close(self):
        if self.session:
            await self.session.close()