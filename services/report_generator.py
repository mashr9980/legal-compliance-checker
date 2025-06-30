from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
from models.schemas import PolicyChecklist, PolicyStatus
from typing import Dict, Any

class IntelligentReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_dynamic_styles()
    
    def _setup_dynamic_styles(self):
        self.styles.add(ParagraphStyle(
            name='DynamicTitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            spaceAfter=25,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CategoryHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='AlignedItem',
            parent=self.styles['Normal'],
            textColor=colors.green,
            fontSize=10,
            leftIndent=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='ModerateItem', 
            parent=self.styles['Normal'],
            textColor=colors.orange,
            fontSize=10,
            leftIndent=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='UnalignedItem',
            parent=self.styles['Normal'],
            textColor=colors.red,
            fontSize=10,
            leftIndent=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='DetailText',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=25,
            spaceBefore=2,
            spaceAfter=2
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
        
        story.extend(self._create_dynamic_header(checklist, doc1_filename, doc2_filename))
        story.extend(self._create_executive_dashboard(checklist))
        story.extend(self._create_intelligent_checklist(checklist))
        story.extend(self._create_strategic_recommendations(checklist))
        story.extend(self._create_overall_policy_feedback(checklist))
        story.extend(self._create_intelligent_footer(checklist))
        
        doc.build(story)
    
    def _create_dynamic_header(self, checklist: PolicyChecklist, doc1_filename: str, doc2_filename: str):
        elements = []
        
        doc_analysis = checklist.document_analysis
        reference_doc = doc_analysis.get("reference_document", {})
        target_doc = doc_analysis.get("target_document", {})
        context = doc_analysis.get("comparison_context", {})
        
        title = f"INTELLIGENT POLICY COMPLIANCE ANALYSIS"
        subtitle = context.get("description", "Document Comparison Report").upper()
        
        elements.append(Paragraph(title, self.styles['DynamicTitle']))
        elements.append(Paragraph(subtitle, self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        header_data = [
            ['Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Analysis Type:', context.get("analysis_type", "Unknown").replace('_', ' ').title()],
            ['Reference Document:', f"{reference_doc.get('title', doc1_filename)} ({reference_doc.get('document_type', 'Unknown')})"],
            ['Target Document:', f"{target_doc.get('title', doc2_filename)} ({target_doc.get('document_type', 'Unknown')})"],
            ['Scope:', ', '.join(reference_doc.get('scope', []) + target_doc.get('scope', []))[:100] + '...' if len(', '.join(reference_doc.get('scope', []) + target_doc.get('scope', []))) > 100 else ', '.join(reference_doc.get('scope', []) + target_doc.get('scope', []))],
        ]
        
        header_table = Table(header_data, colWidths=[1.8*inch, 4.2*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 25))
        
        return elements
    
    def _create_executive_dashboard(self, checklist: PolicyChecklist):
        elements = []
        
        elements.append(Paragraph("EXECUTIVE DASHBOARD", self.styles['Heading2']))
        
        stats = checklist.overall_feedback["statistics"]
        
        dashboard_data = [
            ['Metric', 'Count', 'Percentage'],
            ['✅ Aligned Items', str(stats["aligned"]), f"{stats['alignment_percentage']:.1f}%"],
            ['⚠️ Moderate Items', str(stats["moderate"]), f"{stats['moderate_percentage']:.1f}%"],
            ['❌ Unaligned Items', str(stats["unaligned"]), f"{stats['unaligned_percentage']:.1f}%"],
            ['📊 Total Items Analyzed', str(stats["total"]), '100.0%'],
        ]
        
        dashboard_table = Table(dashboard_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        dashboard_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightyellow),
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightcoral)
        ]))
        
        elements.append(dashboard_table)
        elements.append(Spacer(1, 15))
        
        compliance_maturity = checklist.overall_feedback.get("compliance_maturity", "DEVELOPING")
        assessment = checklist.overall_feedback.get("assessment", "")
        
        elements.append(Paragraph(f"<b>Compliance Maturity Level:</b> {compliance_maturity}", self.styles['Normal']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Executive Assessment:</b> {assessment}", self.styles['Normal']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_intelligent_checklist(self, checklist: PolicyChecklist):
        elements = []
        
        elements.append(Paragraph("DETAILED POLICY CHECKLIST", self.styles['Heading2']))
        elements.append(Spacer(1, 15))
        
        categories = {}
        for item in checklist.items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        for category, items in categories.items():
            category_title = category.replace('_', ' ').title()
            elements.append(Paragraph(category_title, self.styles['CategoryHeader']))
            elements.append(Spacer(1, 10))
            
            for item in items:
                elements.extend(self._create_intelligent_item_block(item))
                elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_intelligent_item_block(self, item):
        elements = []
        
        status_symbol = "✅" if item.status == PolicyStatus.ALIGNED else "⚠️" if item.status == PolicyStatus.MODERATE else "❌"
        status_style = self.styles['AlignedItem'] if item.status == PolicyStatus.ALIGNED else self.styles['ModerateItem'] if item.status == PolicyStatus.MODERATE else self.styles['UnalignedItem']
        
        item_header = f"<b>{status_symbol} {item.chapter} - {item.item}</b>"
        elements.append(Paragraph(item_header, status_style))
        
        if item.requirement:
            elements.append(Paragraph(f"<b>Requirement:</b> {item.requirement}", self.styles['DetailText']))
        
        detail_data = [
            ['Status:', item.status.value],
            ['Source:', item.source_reference],
            ['Feedback:', item.feedback[:150] + '...' if len(item.feedback) > 150 else item.feedback],
        ]
        
        if item.comments:
            detail_data.append(['Comments:', item.comments[:150] + '...' if len(item.comments) > 150 else item.comments])
        
        if item.suggested_amendments:
            detail_data.append(['Amendments:', item.suggested_amendments[:150] + '...' if len(item.suggested_amendments) > 150 else item.suggested_amendments])
        
        detail_table = Table(detail_data, colWidths=[1*inch, 4.5*inch])
        detail_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 25),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(detail_table)
        
        return elements
    
    def _create_strategic_recommendations(self, checklist: PolicyChecklist):
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("STRATEGIC RECOMMENDATIONS", self.styles['Heading2']))
        elements.append(Spacer(1, 15))
        
        key_strengths = checklist.overall_feedback.get("key_strengths", [])
        critical_gaps = checklist.overall_feedback.get("critical_gaps", [])
        next_steps = checklist.overall_feedback.get("next_steps", [])
        
        if key_strengths:
            elements.append(Paragraph("KEY STRENGTHS IDENTIFIED:", self.styles['CategoryHeader']))
            for i, strength in enumerate(key_strengths[:5], 1):
                elements.append(Paragraph(f"{i}. {strength}", self.styles['AlignedItem']))
            elements.append(Spacer(1, 15))
        
        if critical_gaps:
            elements.append(Paragraph("CRITICAL GAPS TO ADDRESS:", self.styles['CategoryHeader']))
            for i, gap in enumerate(critical_gaps[:5], 1):
                elements.append(Paragraph(f"{i}. {gap}", self.styles['UnalignedItem']))
            elements.append(Spacer(1, 15))
        
        if checklist.recommendations:
            elements.append(Paragraph("STRATEGIC RECOMMENDATIONS:", self.styles['CategoryHeader']))
            for i, rec in enumerate(checklist.recommendations[:5], 1):
                elements.append(Paragraph(f"{i}. {rec}", self.styles['ModerateItem']))
            elements.append(Spacer(1, 15))
        
        if next_steps:
            elements.append(Paragraph("RECOMMENDED NEXT STEPS:", self.styles['CategoryHeader']))
            for i, step in enumerate(next_steps[:5], 1):
                elements.append(Paragraph(f"{i}. {step}", self.styles['Normal']))
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_overall_policy_feedback(self, checklist: PolicyChecklist):
        elements = []
        
        elements.append(Paragraph("OVERALL POLICY FEEDBACK", self.styles['Heading2']))
        elements.append(Spacer(1, 15))
        
        stats = checklist.overall_feedback["statistics"]
        
        feedback_data = [
            ['Feedback Category', 'Count', 'Percentage'],
            ['Aligned', str(stats["aligned"]), f"{stats['alignment_percentage']:.1f}%"],
            ['Moderate', str(stats["moderate"]), f"{stats['moderate_percentage']:.1f}%"],
            ['Unaligned/Missing', str(stats["unaligned"]), f"{stats['unaligned_percentage']:.1f}%"]
        ]
        
        feedback_table = Table(feedback_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        feedback_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightyellow),
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightcoral),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(feedback_table)
        elements.append(Spacer(1, 20))
        
        assessment = checklist.overall_feedback.get("assessment", "")
        if assessment:
            elements.append(Paragraph(assessment, self.styles['Normal']))
            elements.append(Spacer(1, 15))
        
        if checklist.additional_considerations:
            elements.append(Paragraph("ADDITIONAL CONSIDERATIONS:", self.styles['CategoryHeader']))
            
            consideration_data = []
            for consideration in checklist.additional_considerations[:5]:
                consideration_data.append(['•', consideration])
            
            if consideration_data:
                consideration_table = Table(consideration_data, colWidths=[0.3*inch, 5.7*inch])
                consideration_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(consideration_table)
        
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("POLICY REVIEW LEGEND:", self.styles['CategoryHeader']))
        legend_data = [
            ['Aligned:', 'Requirements fully met, no changes needed'],
            ['Moderate:', 'Partially met, minor improvements or considerations needed'],
            ['Unaligned/Missing:', 'Requirements not met, significant changes required']
        ]
        
        legend_table = Table(legend_data, colWidths=[1.2*inch, 4.8*inch])
        legend_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.green),
            ('TEXTCOLOR', (0, 1), (0, 1), colors.orange),
            ('TEXTCOLOR', (0, 2), (0, 2), colors.red),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(legend_table)
        
        return elements
    
    def _create_intelligent_footer(self, checklist: PolicyChecklist):
        elements = []
        
        elements.append(Spacer(1, 30))
        
        risk_assessment = checklist.overall_feedback.get("risk_assessment", "")
        if risk_assessment:
            elements.append(Paragraph("RISK ASSESSMENT", self.styles['CategoryHeader']))
            elements.append(Paragraph(risk_assessment, self.styles['Normal']))
            elements.append(Spacer(1, 15))
        
        improvement_timeline = checklist.overall_feedback.get("improvement_timeline", "")
        if improvement_timeline:
            elements.append(Paragraph(f"<b>Suggested Implementation Timeline:</b> {improvement_timeline}", self.styles['Normal']))
            elements.append(Spacer(1, 15))
        
        elements.append(Paragraph("DISCLAIMER", self.styles['CategoryHeader']))
        elements.append(Paragraph(
            "This report is generated by an intelligent policy compliance analysis system using advanced AI. "
            "While the system provides comprehensive analysis and recommendations, this should complement, "
            "not replace, professional legal and policy expertise. Final decisions should involve qualified "
            "subject matter experts and legal professionals.",
            self.styles['Normal']
        ))
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("─" * 80, self.styles['Normal']))
        elements.append(Paragraph(
            f"Intelligent Policy Compliance Report | Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            ParagraphStyle(
                name='IntelligentFooter',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
        ))
        
        return elements