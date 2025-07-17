from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
from models.schemas import PolicyChecklist, PolicyStatus
from typing import Dict, Any

class IntelligentReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_dynamic_styles()
    
    def _setup_dynamic_styles(self):
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=25,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CategoryHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            alignment=TA_LEFT,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='RecommendationText',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=8,
            leftIndent=20,
            bulletIndent=10,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='OverallHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=25,
            alignment=TA_LEFT,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='OverallText',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=8,
            leftIndent=20,
            bulletIndent=10,
            wordWrap='CJK'
        ))
    
    def generate_intelligent_report(self, checklist: PolicyChecklist, doc1_filename: str, doc2_filename: str, output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        story = []
        
        story.append(Paragraph("RAIA – Smart Policy Review Report", self.styles['ReportTitle']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Recommendations / Suggested Amendments per Section", self.styles['SectionTitle']))
        story.append(Spacer(1, 20))
        
        categories = {}
        for item in checklist.items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        category_labels = {
            'employment_terms': '1. Organizational Design & Workforce Planning',
            'compensation_benefits': '6. Compensation & Benefits', 
            'working_conditions': '3. Learning & Development',
            'termination_conditions': '4. Performance Management',
            'confidentiality_non_compete': '5. Talent Management',
            'intellectual_property': '7. Human Capital Operations',
            'dispute_resolution': '8. Regulatory Compliance & Governance',
            'compliance_regulatory': '8. Regulatory Compliance & Governance',
            'health_safety': '7. Human Capital Operations',
            'leave_policies': '7. Human Capital Operations',
            'other': '9. Overall Policy Quality & Maturity'
        }
        
        talent_acquisition_items = []
        
        category_order = [
            'employment_terms',
            'compensation_benefits',
            'working_conditions', 
            'termination_conditions',
            'confidentiality_non_compete',
            'intellectual_property',
            'dispute_resolution',
            'compliance_regulatory',
            'health_safety',
            'leave_policies',
            'other'
        ]
        
        processed_categories = set()
        
        for category in category_order:
            if category in categories and category not in processed_categories:
                items = categories[category]
                if not items:
                    continue
                    
                category_label = category_labels.get(category, category.replace('_', ' ').title())
                
                if category == 'employment_terms':
                    story.append(Paragraph(category_label, self.styles['CategoryHeader']))
                    story.extend(self._generate_employment_recommendations(items))
                    
                    story.append(Paragraph("2. Talent Acquisition", self.styles['CategoryHeader']))
                    story.extend(self._generate_talent_acquisition_recommendations())
                    
                elif category == 'working_conditions':
                    story.append(Paragraph(category_label, self.styles['CategoryHeader']))
                    story.extend(self._generate_learning_development_recommendations(items))
                    
                elif category == 'termination_conditions':
                    story.append(Paragraph(category_label, self.styles['CategoryHeader']))
                    story.extend(self._generate_performance_management_recommendations(items))
                    
                elif category == 'confidentiality_non_compete':
                    story.append(Paragraph(category_label, self.styles['CategoryHeader']))
                    story.extend(self._generate_talent_management_recommendations(items))
                    
                elif category == 'compensation_benefits':
                    story.append(Paragraph(category_label, self.styles['CategoryHeader']))
                    story.extend(self._generate_compensation_recommendations(items))
                    
                elif category in ['intellectual_property', 'health_safety', 'leave_policies']:
                    if '7. Human Capital Operations' not in [p.text for p in story if hasattr(p, 'text') and p.text.startswith('7.')]:
                        story.append(Paragraph("7. Human Capital Operations", self.styles['CategoryHeader']))
                        story.extend(self._generate_hc_operations_recommendations(categories.get('intellectual_property', []) + 
                                                                               categories.get('health_safety', []) + 
                                                                               categories.get('leave_policies', [])))
                    
                elif category in ['dispute_resolution', 'compliance_regulatory']:
                    if '8. Regulatory Compliance & Governance' not in [p.text for p in story if hasattr(p, 'text') and p.text.startswith('8.')]:
                        story.append(Paragraph("8. Regulatory Compliance & Governance", self.styles['CategoryHeader']))
                        story.extend(self._generate_compliance_recommendations(categories.get('dispute_resolution', []) + 
                                                                             categories.get('compliance_regulatory', [])))
                    
                elif category == 'other':
                    story.append(Paragraph(category_label, self.styles['CategoryHeader']))
                    story.extend(self._generate_overall_recommendations(items))
                
                processed_categories.add(category)
        
        doc.build(story)
    
    def _generate_employment_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Review and update {item.item.lower()} requirements", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Review organizational structure and workforce planning policies", self.styles['RecommendationText']))
        
        return story
    
    def _generate_talent_acquisition_recommendations(self):
        story = []
        story.append(Paragraph("• Review recruitment and selection processes for effectiveness", self.styles['RecommendationText']))
        story.append(Paragraph("• Enhance onboarding procedures to improve new hire integration", self.styles['RecommendationText']))
        story.append(Paragraph("• Standardize talent acquisition practices across departments", self.styles['RecommendationText']))
        
        return story
    
    def _generate_learning_development_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Enhance {item.item.lower()} development programs", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Establish comprehensive learning and development framework", self.styles['RecommendationText']))
        
        return story
    
    def _generate_performance_management_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Improve {item.item.lower()} processes and procedures", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Strengthen performance management systems and processes", self.styles['RecommendationText']))
        
        return story
    
    def _generate_talent_management_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Address {item.item.lower()} requirements", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Develop comprehensive talent management strategies", self.styles['RecommendationText']))
        
        return story
    
    def _generate_compensation_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Review and update {item.item.lower()} policies", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Review compensation and benefits structure for market alignment", self.styles['RecommendationText']))
        
        return story
    
    def _generate_hc_operations_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Improve {item.item.lower()} procedures", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Enhance human capital operations and service delivery", self.styles['RecommendationText']))
        
        return story
    
    def _generate_compliance_recommendations(self, items):
        story = []
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
            elif item.comments and item.comments.strip():
                story.append(Paragraph(f"• {item.comments}", self.styles['RecommendationText']))
            else:
                story.append(Paragraph(f"• Ensure compliance with {item.item.lower()} requirements", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Strengthen regulatory compliance and governance framework", self.styles['RecommendationText']))
        
        return story
    
    def _generate_overall_recommendations(self, items):
        story = []
        
        unaligned_items = [item for item in items if item.status == PolicyStatus.UNALIGNED]
        moderate_items = [item for item in items if item.status == PolicyStatus.MODERATE]
        
        if unaligned_items:
            story.append(Paragraph("• Address critical policy gaps and missing requirements", self.styles['RecommendationText']))
        
        if moderate_items:
            story.append(Paragraph("• Review and enhance policies requiring moderate improvements", self.styles['RecommendationText']))
        
        for item in items:
            if item.suggested_amendments and item.suggested_amendments.strip():
                story.append(Paragraph(f"• {item.suggested_amendments}", self.styles['RecommendationText']))
        
        if not story:
            story.append(Paragraph("• Conduct comprehensive policy review and update", self.styles['RecommendationText']))
            story.append(Paragraph("• Implement quality assurance measures for policy management", self.styles['RecommendationText']))
        
        return story