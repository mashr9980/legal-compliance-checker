import pdfplumber
import re
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DocumentSection:
    title: str
    content: str
    section_number: str

class DocumentProcessor:
    def __init__(self):
        self.section_patterns = [
            r'^\d+\.\s+(.+?)$',
            r'^Article\s+\d+\s*[-:]\s*(.+?)$',
            r'^Section\s+\d+\s*[-:]\s*(.+?)$',
            r'^Chapter\s+\d+\s*[-:]\s*(.+?)$',
            r'^\([a-z]\)\s+(.+?)$',
            r'^\([0-9]+\)\s+(.+?)$'
        ]
    
    def extract_text(self, pdf_path: str) -> str:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\-\"\'\/\%\$\&\@\#]', '', text)
        return text.strip()
    
    def extract_sections(self, text: str) -> List[DocumentSection]:
        sections = []
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            section_match = self._find_section_header(line)
            if section_match:
                if current_section:
                    sections.append(DocumentSection(
                        title=current_section['title'],
                        content=' '.join(current_content).strip(),
                        section_number=current_section['number']
                    ))
                
                current_section = section_match
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        if current_section and current_content:
            sections.append(DocumentSection(
                title=current_section['title'],
                content=' '.join(current_content).strip(),
                section_number=current_section['number']
            ))
        
        return sections
    
    def _find_section_header(self, line: str) -> Dict:
        for pattern in self.section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'title': match.group(1).strip(),
                    'number': self._extract_section_number(line)
                }
        return None
    
    def _extract_section_number(self, line: str) -> str:
        number_match = re.search(r'(\d+(?:\.\d+)*|\([a-z0-9]+\))', line)
        return number_match.group(1) if number_match else ""
    
    def extract_key_phrases(self, text: str) -> List[str]:
        legal_keywords = [
            r'shall\s+(?:not\s+)?(?:be\s+)?(?:required|prohibited|entitled|liable)',
            r'must\s+(?:not\s+)?(?:be\s+)?(?:include|contain|provide|maintain)',
            r'(?:minimum|maximum)\s+(?:of\s+)?\d+(?:\s+days?|\s+months?|\s+years?|\%)',
            r'(?:not\s+)?(?:less|more)\s+than\s+\d+',
            r'(?:terminate|termination)(?:\s+with|\s+without|\s+upon)',
            r'(?:notice\s+)?period\s+of\s+\d+',
            r'(?:overtime|additional)\s+(?:pay|compensation|rate)',
            r'(?:annual\s+)?leave\s+(?:entitlement|days)',
            r'(?:confidentiality|non-disclosure)(?:\s+agreement)?',
            r'(?:indemnity|liability|damages)(?:\s+clause)?'
        ]
        
        phrases = []
        for pattern in legal_keywords:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend(matches)
        
        return list(set(phrases))