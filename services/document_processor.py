import pdfplumber
import re
from typing import Dict, List, Tuple, Optional
from config import CHUNK_SIZE, OVERLAP_SIZE
import asyncio

class DocumentProcessor:
    def __init__(self):
        self.text_patterns = {
            'headers': r'^[A-Z\s]{10,}',
            'legal_sections': r'(Article|Section|Chapter|Clause|Part)\s+[IVX\d]+',
            'obligations': r'\b(shall|must|required|mandatory|obligated)\b',
            'definitions': r'\b(means|defined as|refers to|includes)\b'
        }
        self.llm_analyzer = None
    
    def set_llm_analyzer(self, analyzer):
        self.llm_analyzer = analyzer
    
    async def intelligent_extract_text(self, pdf_path: str) -> Dict[str, any]:
        try:
            print(f"Starting intelligent text extraction from: {pdf_path}")
            
            raw_text = self.extract_text(pdf_path)
            
            if len(raw_text) < 100:
                return {
                    "extracted_text": raw_text,
                    "quality": "POOR",
                    "structure": {},
                    "recommendations": ["Document appears to have minimal text", "Check if PDF is readable"]
                }
            
            if self.llm_analyzer:
                print("Performing intelligent content analysis...")
                content_analysis = await self._intelligent_content_analysis(raw_text)
            else:
                content_analysis = self._basic_content_analysis(raw_text)
            
            structure = self.analyze_document_structure(raw_text)
            
            quality_assessment = self._assess_document_quality(raw_text, structure)
            
            return {
                "extracted_text": raw_text,
                "content_analysis": content_analysis,
                "structure": structure,
                "quality": quality_assessment["quality"],
                "recommendations": quality_assessment["recommendations"],
                "extraction_metadata": {
                    "character_count": len(raw_text),
                    "word_count": len(raw_text.split()),
                    "language": structure.get("document_language", "unknown"),
                    "complexity": structure.get("estimated_complexity", "unknown")
                }
            }
            
        except Exception as e:
            print(f"Error in intelligent text extraction: {e}")
            return {
                "extracted_text": f"EXTRACTION_ERROR: {str(e)}",
                "quality": "ERROR",
                "structure": {},
                "recommendations": ["Extraction failed", "Check PDF format and integrity"]
            }
    
    async def _intelligent_content_analysis(self, text: str) -> Dict[str, any]:
        if not self.llm_analyzer:
            return self._basic_content_analysis(text)
        
        system_prompt = """You are an expert document analyst. Analyze the content structure, key themes, and document characteristics.
        Focus on identifying the document's purpose, main topics, and structural elements."""
        
        text_sample = text[:2000] if len(text) > 2000 else text
        
        prompt = f"""Analyze this document content and provide detailed insights:

DOCUMENT CONTENT:
{text_sample}

Provide analysis in JSON format:
{{
    "document_themes": ["[main themes and topics]"],
    "content_type": "[legal/contract/policy/technical/other]",
    "structural_elements": ["[headers, sections, lists, etc.]"],
    "key_entities": ["[important names, organizations, concepts]"],
    "language_style": "[formal/informal/legal/technical]",
    "content_density": "[high/medium/low] - how much substantive content",
    "logical_flow": "[excellent/good/fair/poor] - how well organized",
    "completeness": "[complete/partial/fragmented]",
    "main_purposes": ["[what this document is trying to achieve]"],
    "target_audience": "[who this document is for]",
    "content_quality_indicators": ["[signs of quality or issues]"]
}}

Provide only the JSON response with detailed analysis."""
        
        try:
            response = await self.llm_analyzer.generate_with_context(prompt, system_prompt, 1024)
            return self._parse_content_analysis(response)
        except Exception as e:
            print(f"Error in intelligent content analysis: {e}")
            return self._basic_content_analysis(text)
    
    def _parse_content_analysis(self, response: str) -> Dict[str, any]:
        try:
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                
                default_fields = {
                    "document_themes": [],
                    "content_type": "unknown",
                    "structural_elements": [],
                    "key_entities": [],
                    "language_style": "unknown",
                    "content_density": "medium",
                    "logical_flow": "fair",
                    "completeness": "partial",
                    "main_purposes": [],
                    "target_audience": "unknown",
                    "content_quality_indicators": []
                }
                
                for field, default in default_fields.items():
                    if field not in analysis:
                        analysis[field] = default
                
                return analysis
        except Exception as e:
            print(f"Error parsing content analysis: {e}")
        
        return self._basic_content_analysis("")
    
    def _basic_content_analysis(self, text: str) -> Dict[str, any]:
        text_lower = text.lower()
        
        theme_keywords = {
            "employment": ["employment", "employee", "employer", "work", "job"],
            "legal": ["law", "legal", "regulation", "compliance", "statute"],
            "financial": ["payment", "salary", "compensation", "money", "cost"],
            "procedural": ["procedure", "process", "step", "method", "protocol"],
            "technical": ["technical", "specification", "requirement", "standard"]
        }
        
        themes = []
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        if any(word in text_lower for word in ["contract", "agreement"]):
            content_type = "contract"
        elif any(word in text_lower for word in ["law", "regulation", "code"]):
            content_type = "legal"
        elif any(word in text_lower for word in ["policy", "procedure"]):
            content_type = "policy"
        else:
            content_type = "unknown"
        
        return {
            "document_themes": themes,
            "content_type": content_type,
            "structural_elements": ["text paragraphs"],
            "key_entities": [],
            "language_style": "formal" if any(word in text_lower for word in ["shall", "must", "whereas"]) else "unknown",
            "content_density": "medium",
            "logical_flow": "fair",
            "completeness": "partial",
            "main_purposes": ["document communication"],
            "target_audience": "stakeholders",
            "content_quality_indicators": ["basic text present"]
        }
    
    def _assess_document_quality(self, text: str, structure: Dict) -> Dict[str, any]:
        word_count = len(text.split())
        
        quality_indicators = {
            "length": "good" if word_count > 500 else "poor" if word_count < 100 else "fair",
            "structure": "good" if len(structure.get("sections", [])) > 3 else "fair",
            "legal_content": "good" if len(structure.get("obligations", [])) > 2 else "fair",
            "organization": "good" if len(structure.get("legal_references", [])) > 1 else "fair"
        }
        
        good_count = sum(1 for v in quality_indicators.values() if v == "good")
        fair_count = sum(1 for v in quality_indicators.values() if v == "fair")
        
        if good_count >= 3:
            overall_quality = "EXCELLENT"
        elif good_count >= 2:
            overall_quality = "GOOD"
        elif fair_count >= 2:
            overall_quality = "FAIR"
        else:
            overall_quality = "POOR"
        
        recommendations = []
        if quality_indicators["length"] == "poor":
            recommendations.append("Document appears to have insufficient content")
        if quality_indicators["structure"] == "poor":
            recommendations.append("Document lacks clear structural organization")
        if quality_indicators["legal_content"] == "poor":
            recommendations.append("Limited legal content detected")
        
        if not recommendations:
            recommendations.append("Document quality is satisfactory for analysis")
        
        return {
            "quality": overall_quality,
            "quality_indicators": quality_indicators,
            "recommendations": recommendations
        }
    
    def extract_text(self, pdf_path: str) -> str:
        try:
            print(f"Extracting text from: {pdf_path}")
            extracted_text = ""
            extraction_methods = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"Processing {total_pages} pages...")
                
                for i, page in enumerate(pdf.pages):
                    page_text = ""
                    
                    try:
                        text_extract = page.extract_text()
                        if text_extract and len(text_extract.strip()) > 20:
                            page_text = text_extract
                            if i == 0:
                                extraction_methods.append("direct_text")
                    except Exception as e:
                        print(f"   Page {i+1}: Direct text extraction failed - {e}")
                    
                    if not page_text or len(page_text.strip()) < 20:
                        try:
                            table_text = self._extract_table_text(page)
                            if table_text and len(table_text.strip()) > 20:
                                page_text = table_text
                                if i == 0:
                                    extraction_methods.append("table_extraction")
                        except Exception as e:
                            print(f"   Page {i+1}: Table extraction failed - {e}")
                    
                    if not page_text or len(page_text.strip()) < 10:
                        try:
                            char_text = self._extract_characters(page)
                            if char_text and len(char_text.strip()) > 10:
                                page_text = char_text
                                if i == 0:
                                    extraction_methods.append("character_extraction")
                        except Exception as e:
                            print(f"   Page {i+1}: Character extraction failed - {e}")
                    
                    if page_text:
                        cleaned_page = self._intelligent_page_cleaning(page_text)
                        if cleaned_page:
                            extracted_text += cleaned_page + "\n\n"
                            if i < 3:
                                print(f"   Page {i+1}: {len(cleaned_page)} chars extracted")
                    else:
                        print(f"   Page {i+1}: No text extracted")
            
            print(f"Extraction methods used: {', '.join(set(extraction_methods))}")
            
            processed_text = self._comprehensive_text_processing(extracted_text)
            print(f"Final extraction: {len(processed_text)} characters")
            
            if len(processed_text) < 100:
                print(f"Warning: Very little text extracted ({len(processed_text)} chars)")
                return self._create_extraction_report(pdf_path, processed_text, extraction_methods)
            
            return processed_text
            
        except Exception as e:
            error_msg = f"Critical error extracting from {pdf_path}: {str(e)}"
            print(f"Error: {error_msg}")
            return f"EXTRACTION_ERROR: {error_msg}"
    
    def _extract_characters(self, page) -> str:
        try:
            chars = page.chars
            if not chars:
                return ""
            
            text_content = ""
            for char in chars:
                if 'text' in char:
                    text_content += char['text']
            
            return text_content
        except Exception as e:
            print(f"Character extraction error: {e}")
            return ""
    
    def _extract_table_text(self, page) -> str:
        try:
            tables = page.extract_tables()
            table_text = ""
            
            for table in tables:
                if table and len(table) > 0:
                    for row in table:
                        if row:
                            clean_cells = []
                            for cell in row:
                                if cell:
                                    cell_text = str(cell).strip()
                                    if len(cell_text) > 0 and cell_text not in ['', 'None', 'null']:
                                        clean_cells.append(cell_text)
                            
                            if clean_cells:
                                table_text += " | ".join(clean_cells) + "\n"
            
            return table_text
        except Exception as e:
            print(f"Table extraction error: {e}")
            return ""
    
    def _intelligent_page_cleaning(self, page_text: str) -> str:
        if not page_text:
            return ""
        
        text = page_text.strip()
        
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1 \2', text)
        text = re.sub(r'\n([a-z])', r' \1', text)
        
        lines = text.split('\n')
        meaningful_lines = []
        
        for line in lines:
            line = line.strip()
            if self._is_meaningful_line(line):
                line = self._clean_meaningful_line(line)
                meaningful_lines.append(line)
        
        return '\n'.join(meaningful_lines)
    
    def _clean_meaningful_line(self, line: str) -> str:
        line = re.sub(r'\s+', ' ', line)
        
        ocr_fixes = {
            r'\bl\b': 'I',
            r'\b0\b': 'O',
            r'rn': 'm',
            r'vv': 'w',
        }
        
        for pattern, replacement in ocr_fixes.items():
            line = re.sub(pattern, replacement, line)
        
        return line.strip()
    
    def _is_meaningful_line(self, line: str) -> bool:
        if len(line) < 3:
            return False
        
        skip_patterns = [
            r'^\d+$',
            r'^Page\s+\d+',
            r'^(Header|Footer|Copyright|©)',
            r'^(Confidential|Draft|Version)',
            r'^\s*[-_=]+\s*$',
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return False
        
        legal_indicators = [
            'article', 'section', 'chapter', 'clause', 'shall', 'must', 'required',
            'contract', 'agreement', 'employee', 'employer', 'party', 'parties',
            'law', 'regulation', 'code', 'act', 'decree', 'policy', 'procedure',
            'whereas', 'therefore', 'hereby', 'notwithstanding', 'pursuant'
        ]
        
        line_lower = line.lower()
        
        if any(indicator in line_lower for indicator in legal_indicators):
            return True
        
        word_count = len(line.split())
        if word_count >= 5 and '.' in line:
            return True
        
        if re.match(r'^\d+\.|\([a-z]\)|\([0-9]+\)', line.strip()):
            return True
        
        return False
    
    def _comprehensive_text_processing(self, raw_text: str) -> str:
        if not raw_text:
            return ""
        
        text = raw_text.strip()
        
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1\n\2', text)
        text = re.sub(r'\n([a-z])', r' \1', text)
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        meaningful_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if self._is_meaningful_sentence(sentence):
                sentence = self._enhance_sentence(sentence)
                meaningful_sentences.append(sentence)
        
        final_text = ' '.join(meaningful_sentences)
        
        final_text = re.sub(r'\s+', ' ', final_text)
        final_text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', final_text)
        
        return final_text.strip()
    
    def _enhance_sentence(self, sentence: str) -> str:
        sentence = re.sub(r'\s+', ' ', sentence)
        
        sentence = re.sub(r'([.!?])([A-Z])', r'\1 \2', sentence)
        sentence = re.sub(r'([,;:])([A-Za-z])', r'\1 \2', sentence)
        
        def capitalize_after_period(match):
            return match.group(1) + ' ' + match.group(2).upper()
        
        sentence = re.sub(r'(\.)(\s+)([a-z])', capitalize_after_period, sentence)
        
        return sentence.strip()
    
    def _is_meaningful_sentence(self, sentence: str) -> bool:
        if len(sentence) < 10:
            return False
        
        word_count = len(sentence.split())
        if word_count < 3:
            return False
        
        legal_content_indicators = [
            'shall', 'must', 'required', 'mandatory', 'prohibited', 'entitled',
            'agreement', 'contract', 'employee', 'employer', 'party', 'parties',
            'article', 'section', 'chapter', 'clause', 'provision', 'term',
            'law', 'regulation', 'code', 'act', 'decree', 'policy', 'rule',
            'compensation', 'salary', 'payment', 'benefit', 'leave', 'termination',
            'confidentiality', 'intellectual', 'property', 'dispute', 'resolution',
            'whereas', 'therefore', 'hereby', 'notwithstanding', 'pursuant',
            'obligations', 'responsibilities', 'rights', 'duties', 'compliance'
        ]
        
        sentence_lower = sentence.lower()
        has_legal_content = any(indicator in sentence_lower for indicator in legal_content_indicators)
        
        if has_legal_content:
            return True
        
        if word_count >= 7 and not self._is_header_footer_content(sentence):
            return True
        
        if '.' in sentence and word_count >= 5:
            return True
        
        return False
    
    def _is_header_footer_content(self, text: str) -> bool:
        text_lower = text.lower()
        
        header_footer_patterns = [
            r'page\s+\d+',
            r'copyright\s+©',
            r'all\s+rights\s+reserved',
            r'confidential',
            r'draft',
            r'version\s+\d',
            r'document\s+title',
            r'file\s+name',
            r'printed\s+on',
            r'generated\s+on'
        ]
        
        for pattern in header_footer_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def analyze_document_structure(self, text: str) -> Dict[str, any]:
        if not text or len(text) < 50:
            return self._create_minimal_structure()
        
        structure = {
            'total_length': len(text),
            'word_count': len(text.split()),
            'sentence_count': len(re.split(r'[.!?]+', text)),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
            'sections': self._find_sections(text),
            'legal_references': self._find_legal_references(text),
            'key_terms': self._extract_key_terms(text),
            'obligations': self._find_obligations(text),
            'definitions': self._find_definitions(text),
            'contract_elements': self._find_contract_elements(text),
            'dates_found': self._extract_dates(text),
            'numbers_found': self._extract_numbers(text),
            'document_language': self._detect_language(text),
            'estimated_complexity': self._estimate_complexity(text),
            'document_quality': self._assess_basic_quality(text),
            'content_density': self._calculate_content_density(text),
            'structural_indicators': self._find_structural_indicators(text)
        }
        return structure
    
    def _calculate_content_density(self, text: str) -> str:
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return "EMPTY"
        
        meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
        density_ratio = len(meaningful_words) / word_count
        
        if density_ratio > 0.7:
            return "HIGH"
        elif density_ratio > 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _find_structural_indicators(self, text: str) -> Dict[str, bool]:
        return {
            "has_numbered_sections": bool(re.search(r'^\d+\.', text, re.MULTILINE)),
            "has_lettered_sections": bool(re.search(r'^\([a-z]\)', text, re.MULTILINE)),
            "has_bullet_points": bool(re.search(r'^\s*[•·▪▫]\s', text, re.MULTILINE)),
            "has_definitions_section": "definition" in text.lower(),
            "has_signature_block": any(word in text.lower() for word in ["signature", "signed", "executed"]),
            "has_date_references": bool(self._extract_dates(text)),
            "has_monetary_values": bool(re.search(r'\$\d+|\d+\s*(dollars?|USD|SAR)', text, re.IGNORECASE)),
            "has_legal_citations": bool(self._find_legal_references(text)),
            "has_cross_references": bool(re.search(r'see\s+(section|article|chapter|clause)', text, re.IGNORECASE))
        }
    
    def _assess_basic_quality(self, text: str) -> str:
        word_count = len(text.split())
        
        artifacts = [
            len(re.findall(r'[^\w\s.!?,:;()"\'-]', text)),
            len(re.findall(r'\b\w{1,2}\b', text)),
            len(re.findall(r'\w{30,}', text))
        ]
        
        artifact_ratio = sum(artifacts) / max(word_count, 1)
        
        if word_count < 100:
            return 'POOR'
        elif word_count < 500:
            return 'BASIC'
        elif artifact_ratio > 0.1:
            return 'FAIR'
        elif word_count < 2000:
            return 'GOOD'
        else:
            return 'EXCELLENT'
    
    def _create_minimal_structure(self) -> Dict[str, any]:
        return {
            'total_length': 0,
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'sections': [],
            'legal_references': [],
            'key_terms': [],
            'obligations': [],
            'definitions': [],
            'contract_elements': [],
            'dates_found': [],
            'numbers_found': [],
            'document_language': 'unknown',
            'estimated_complexity': 'MINIMAL',
            'document_quality': 'POOR',
            'content_density': 'EMPTY',
            'structural_indicators': {}
        }
    
    def _detect_language(self, text: str) -> str:
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if arabic_chars > english_chars:
            return 'arabic'
        elif english_chars > 0:
            return 'english'
        else:
            return 'mixed'
    
    def _extract_dates(self, text: str) -> List[str]:
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))[:10]
    
    def _extract_numbers(self, text: str) -> List[str]:
        number_patterns = [
            r'\b\d+\.?\d*\s*%\b',
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?\b',
            r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:SAR|SR|USD|Riyal)\b',
            r'\b\d+\s*(?:days?|months?|years?|hours?)\b'
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)
        
        return list(set(numbers))[:15]
    
    def _find_sections(self, text: str) -> List[str]:
        section_patterns = [
            r'(Chapter|Section|Article|Part|Title)\s+[IVX\d]+[:\-\s]*([^\n]{10,100})',
            r'^(\d+\.(?:\d+\.)*)\s+([A-Z][^\n]{10,100})',
            r'^([A-Z][A-Z\s]{8,50})\s*',
            r'(WHEREAS|THEREFORE|NOW THEREFORE|IN WITNESS WHEREOF)',
            r'(Employment|Compensation|Benefits|Termination|Confidentiality|Obligations|Rights|Duties)'
        ]
        
        sections = []
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    sections.append(f"{match.group(1)} {match.group(2)}")
                else:
                    sections.append(match.group(0))
        
        return list(set(sections))[:25]
    
    def _find_legal_references(self, text: str) -> List[str]:
        reference_patterns = [
            r'(Article|Section|Chapter|Clause|Paragraph)\s+\d+(?:\.\d+)*',
            r'(Schedule|Appendix|Annex|Exhibit)\s+[A-Z\d]+',
            r'(Part|Title|Book)\s+[IVX\d]+',
            r'([A-Z][A-Za-z\s]+(?:Act|Law|Code|Regulation|Decree))\s*(?:\d{4})?',
            r'(Royal Decree|Ministerial Decision|Cabinet Resolution)\s+No\.?\s*[A-Z]*[/\d]+',
            r'(Labor Code|Employment Act|Civil Code|Commercial Code|Penal Code)'
        ]
        
        references = []
        for pattern in reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    references.extend([m for m in match if m and len(m) > 2])
                else:
                    references.append(match)
        
        return list(set(references))[:20]
    
    def _find_obligations(self, text: str) -> List[str]:
        obligation_patterns = [
            r'([^.]*\b(?:shall|must|required|mandatory|obligated|is required to)\b[^.]*\.)',
            r'([^.]*\b(?:prohibited|forbidden|not permitted|shall not|must not)\b[^.]*\.)',
            r'([^.]*\b(?:entitled to|has the right to|may|is authorized to)\b[^.]*\.)'
        ]
        
        obligations = []
        for pattern in obligation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            obligations.extend([match.strip() for match in matches if len(match.strip()) > 20])
        
        return obligations[:20]
    
    def _find_definitions(self, text: str) -> List[str]:
        definition_patterns = [
            r'([^.]*\b(?:means|defined as|refers to|includes|shall mean)\b[^.]*\.)',
            r'(For purposes of this [^.]*\.)',
            r'(As used in this [^.]*\.)',
            r'(["\']([^"\']+)["\'] means [^.]*\.)'
        ]
        
        definitions = []
        for pattern in definition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            definitions.extend([match[0] if isinstance(match, tuple) else match for match in matches if len(str(match)) > 15])
        
        return definitions[:15]
    
    def _find_contract_elements(self, text: str) -> List[str]:
        contract_indicators = [
            'effective date', 'commencement date', 'start date', 'beginning',
            'termination', 'expiration', 'end date', 'conclusion',
            'salary', 'compensation', 'remuneration', 'payment', 'wage',
            'benefits', 'allowances', 'perquisites', 'bonus', 'incentive',
            'working hours', 'work schedule', 'duty hours', 'overtime',
            'leave', 'vacation', 'holiday', 'absence', 'time off',
            'confidentiality', 'non-disclosure', 'proprietary', 'secret',
            'non-compete', 'restraint of trade', 'competition',
            'intellectual property', 'inventions', 'copyrights', 'patents',
            'governing law', 'jurisdiction', 'dispute resolution', 'arbitration'
        ]
        
        found_elements = []
        text_lower = text.lower()
        
        for indicator in contract_indicators:
            if indicator in text_lower:
                found_elements.append(indicator)
        
        return found_elements[:20]
    
    def _extract_key_terms(self, text: str) -> List[str]:
        legal_terms = [
            'employment', 'employee', 'employer', 'contract', 'agreement',
            'compensation', 'salary', 'wage', 'benefits', 'allowance',
            'termination', 'resignation', 'dismissal', 'notice',
            'confidentiality', 'disclosure', 'proprietary', 'secret',
            'intellectual property', 'invention', 'copyright', 'patent',
            'working hours', 'overtime', 'leave', 'vacation', 'holiday',
            'performance', 'evaluation', 'promotion', 'transfer',
            'discipline', 'grievance', 'dispute', 'arbitration',
            'compliance', 'regulation', 'law', 'statute', 'code',
            'health', 'safety', 'insurance', 'medical', 'retirement',
            'obligation', 'responsibility', 'duty', 'right', 'entitlement'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in legal_terms:
            count = text_lower.count(term)
            if count >= 1:
                found_terms.append((term, count))
        
        found_terms.sort(key=lambda x: x[1], reverse=True)
        return [term[0] for term in found_terms[:20]]
    
    def _estimate_complexity(self, text: str) -> str:
        word_count = len(text.split())
        legal_term_count = len(self._extract_key_terms(text))
        section_count = len(self._find_sections(text))
        obligation_count = len(self._find_obligations(text))
        
        complexity_score = (
            (word_count / 1000) + 
            (legal_term_count * 2) + 
            (section_count * 3) + 
            (obligation_count * 1.5)
        )
        
        if complexity_score < 5:
            return "MINIMAL"
        elif complexity_score < 15:
            return "LOW"
        elif complexity_score < 35:
            return "MEDIUM"
        elif complexity_score < 70:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def chunk_text(self, text: str) -> List[str]:
        if len(text) <= CHUNK_SIZE:
            return [text]
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= CHUNK_SIZE:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0 and len(chunks[i-1]) >= OVERLAP_SIZE:
                prev_chunk_end = chunks[i-1][-OVERLAP_SIZE:]
                overlapped_chunks.append(prev_chunk_end + " " + chunk)
            else:
                overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def _create_extraction_report(self, pdf_path: str, extracted_text: str, methods: List[str]) -> str:
        report = f"""
        INTELLIGENT DOCUMENT EXTRACTION REPORT
        ======================================

        File: {pdf_path}
        Extraction Methods Attempted: {', '.join(methods) if methods else 'None successful'}
        Extracted Content Length: {len(extracted_text)} characters
        Word Count: {len(extracted_text.split()) if extracted_text else 0}

        EXTRACTION STATUS:
        {'SUCCESS' if len(extracted_text) > 100 else 'LIMITED' if len(extracted_text) > 10 else 'FAILED'}

        EXTRACTED CONTENT PREVIEW:
        {extracted_text[:1000]}{'...' if len(extracted_text) > 1000 else ''}

        DIAGNOSTIC INFORMATION:
        - PDF may contain scanned images instead of selectable text
        - Document may be password protected or corrupted
        - Complex layouts or tables may affect extraction quality
        - Consider OCR preprocessing for image-based PDFs

        RECOMMENDATIONS:
        - Verify PDF contains selectable text (not scanned images)
        - Check if document is password protected
        - Ensure PDF file is not corrupted
        - For scanned documents, use OCR tools before processing
        - Consider converting document to a different format
        - Manual review may be required for complex layouts

        NEXT STEPS:
        1. Check document format and quality
        2. Try alternative extraction methods if available
        3. Consider OCR preprocessing for image-based content
        4. Manual review and typing may be necessary for critical documents
        """
        return report