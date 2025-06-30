import pdfplumber
import re
from typing import Dict, List, Tuple

class DocumentProcessor:
    def __init__(self):
        self.text_patterns = {
            'headers': r'^[A-Z\s]{10,}$',
            'section_numbers': r'^\d+(\.\d+)*\s',
            'legal_references': r'(Article|Section|Chapter|Clause)\s+\d+',
            'obligations': r'(shall|must|required|mandatory|prohibited)',
            'definitions': r'(means|defined as|refers to|includes)'
        }
    
    def extract_text(self, pdf_path: str) -> str:
        try:
            print(f"🔍 Extracting text from: {pdf_path}")
            raw_text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"📄 Processing {total_pages} pages...")
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        raw_text += page_text + "\n"
                        if i < 3:
                            print(f"   Page {i+1}: {len(page_text)} chars")
                    
                    if i == 0 and not page_text:
                        table_text = self._extract_table_text(page)
                        if table_text:
                            raw_text += table_text + "\n"
                            print(f"   Page {i+1}: Extracted table data")
            
            processed_text = self._intelligent_text_processing(raw_text)
            print(f"✅ Extracted {len(processed_text)} characters total")
            
            if len(processed_text) < 100:
                print(f"⚠️  Warning: Very little text extracted")
                print(f"   Raw text sample: {raw_text[:200]}...")
            
            return processed_text
            
        except Exception as e:
            error_msg = f"Error extracting text from {pdf_path}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _extract_table_text(self, page) -> str:
        try:
            tables = page.extract_tables()
            table_text = ""
            for table in tables:
                for row in table:
                    if row:
                        clean_row = [cell.strip() if cell else "" for cell in row]
                        table_text += " | ".join(clean_row) + "\n"
            return table_text
        except:
            return ""
    
    def _intelligent_text_processing(self, raw_text: str) -> str:
        text = raw_text
        
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1 \2', text)
        text = re.sub(r'\n([a-z])', r' \1', text)
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\-\"\'\/\%\$\&\@\#\n]', '', text)
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 5:
                if not self._is_header_footer(line):
                    processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _is_header_footer(self, line: str) -> bool:
        if len(line) < 5:
            return True
        if re.match(r'^\d+$', line.strip()):
            return True
        if re.match(r'^Page\s+\d+', line, re.IGNORECASE):
            return True
        if line.count(' ') < 2 and len(line) < 50:
            return True
        return False
    
    def analyze_document_structure(self, text: str) -> Dict[str, any]:
        structure = {
            'sections': self._find_sections(text),
            'legal_references': self._find_legal_references(text),
            'key_terms': self._extract_key_terms(text),
            'document_length': len(text),
            'estimated_complexity': self._estimate_complexity(text)
        }
        return structure
    
    def _find_sections(self, text: str) -> List[str]:
        sections = []
        patterns = [
            r'(Chapter|Section|Article|Part)\s+[IVX\d]+[:\-\s]+([^\n]{10,80})',
            r'^(\d+\.(?:\d+\.)*)\s+([^\n]{10,80})',
            r'^([A-Z][A-Z\s]{5,30})\s*$'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    sections.append(f"{match.group(1)} {match.group(2)}")
                else:
                    sections.append(match.group(0))
        
        return list(set(sections))[:20]
    
    def _find_legal_references(self, text: str) -> List[str]:
        patterns = [
            r'(Article|Section|Chapter|Clause|Paragraph)\s+\d+(?:\.\d+)*',
            r'(Schedule|Appendix|Annex)\s+[A-Z\d]+',
            r'(Part|Title)\s+[IVX\d]+'
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend([f"{match[0]} {match[1]}" if isinstance(match, tuple) else match for match in matches])
        
        return list(set(references))[:15]
    
    def _extract_key_terms(self, text: str) -> List[str]:
        legal_terms = [
            'compliance', 'requirement', 'obligation', 'prohibition', 'penalty',
            'procedure', 'process', 'standard', 'guideline', 'policy',
            'regulation', 'law', 'act', 'statute', 'ordinance',
            'contract', 'agreement', 'terms', 'conditions', 'provisions'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in legal_terms:
            if term in text_lower:
                count = text_lower.count(term)
                if count >= 2:
                    found_terms.append((term, count))
        
        found_terms.sort(key=lambda x: x[1], reverse=True)
        return [term[0] for term in found_terms[:10]]
    
    def _estimate_complexity(self, text: str) -> str:
        word_count = len(text.split())
        
        if word_count < 1000:
            return "LOW"
        elif word_count < 5000:
            return "MEDIUM"
        elif word_count < 15000:
            return "HIGH"
        else:
            return "VERY_HIGH"