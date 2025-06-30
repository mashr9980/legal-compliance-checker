from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
from models.schemas import ComplianceResult, ComplianceStatus, RiskLevel
import os

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompliancePass',
            parent=self.styles['Normal'],
            textColor=colors.green,
            leftIndent=20,
            fontSize=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='ComplianceFail',
            parent=self.styles['Normal'],
            textColor=colors.red,
            leftIndent=20,
            fontSize=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompliancePartial',
            parent=self.styles['Normal'],
            textColor=colors.orange,
            leftIndent=20,
            fontSize=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='IssueText',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=25,
            spaceBefore=3,
            spaceAfter=3
        ))
    
    def generate_report(
        self, 
        compliance_result: ComplianceResult, 
        legal_filename: str, 
        contract_filename: str, 
        output_path: str
    ):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        story = []
        
        story.extend(self._create_header(legal_filename, contract_filename))
        story.extend(self._create_executive_summary(compliance_result))
        story.extend(self._create_detailed_checklist(compliance_result))
        
        if compliance_result.missing_clauses:
            story.extend(self._create_missing_clauses_section(compliance_result.missing_clauses))
        
        story.extend(self._create_recommendations_summary(compliance_result))
        story.extend(self._create_footer())
        
        doc.build(story)
    
    def _create_header(self, legal_filename: str, contract_filename: str):
        elements = []
        
        elements.append(Paragraph("LEGAL COMPLIANCE CHECKLIST", self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))
        
        header_data = [
            ['Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Legal Document:', legal_filename],
            ['Contract Document:', contract_filename],
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_executive_summary(self, result: ComplianceResult):
        elements = []
        
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        score_color = colors.green if result.compliance_score >= 0.8 else colors.orange if result.compliance_score >= 0.6 else colors.red
        
        summary_data = [
            ['Total Requirements Checked:', str(result.total_requirements)],
            ['Overall Compliance Score:', f"{result.compliance_score:.1%}"],
            ['✅ Compliant:', str(result.compliant_count)],
            ['⚠️ Partially Compliant:', str(result.partial_count)],
            ['❌ Non-Compliant:', str(result.non_compliant_count)],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 1), (0, 1), colors.lightblue),
            ('TEXTCOLOR', (1, 1), (1, 1), score_color),
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        critical_issues = [issue for issue in result.issues if issue.risk_level == RiskLevel.HIGH and issue.status == ComplianceStatus.NON_COMPLIANT]
        if critical_issues:
            elements.append(Paragraph("🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:", self.styles['Normal']))
            elements.append(Spacer(1, 10))
            
            for issue in critical_issues[:3]:
                elements.append(Paragraph(f"• {issue.requirement_description}", self.styles['ComplianceFail']))
            
            elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_detailed_checklist(self, result: ComplianceResult):
        elements = []
        
        elements.append(Paragraph("DETAILED COMPLIANCE CHECKLIST", self.styles['SectionHeader']))
        elements.append(Spacer(1, 15))
        
        categories = {}
        for issue in result.issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)
        
        for category, issues in categories.items():
            elements.append(Paragraph(f"{category.upper().replace('_', ' ')} REQUIREMENTS", self.styles['SubHeader']))
            elements.append(Spacer(1, 10))
            
            for issue in issues:
                elements.extend(self._create_issue_block(issue))
                elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_issue_block(self, issue):
        elements = []
        
        status_symbol = "✅" if issue.status == ComplianceStatus.COMPLIANT else "⚠️" if issue.status == ComplianceStatus.PARTIAL else "❌"
        status_style = self.styles['CompliancePass'] if issue.status == ComplianceStatus.COMPLIANT else self.styles['CompliancePartial'] if issue.status == ComplianceStatus.PARTIAL else self.styles['ComplianceFail']
        
        req_text = f"<b>{status_symbol} REQUIREMENT:</b> {issue.requirement_description}"
        elements.append(Paragraph(req_text, status_style))
        
        info_data = [
            ['Legal Source:', issue.source_section],
            ['Status:', f"{issue.status.value}"],
            ['Risk Level:', f"{issue.risk_level.value}"],
        ]
        
        info_table = Table(info_data, colWidths=[1.2*inch, 3.8*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 25),
        ]))
        
        elements.append(info_table)
        
        if issue.current_text:
            current_text = issue.current_text[:300] + "..." if len(issue.current_text) > 300 else issue.current_text
            elements.append(Paragraph(f"<b>Current Contract Text:</b> \"{current_text}\"", self.styles['IssueText']))
        
        if issue.issue_description:
            elements.append(Paragraph(f"<b>Issue:</b> {issue.issue_description}", self.styles['IssueText']))
        
        if issue.recommendation:
            elements.append(Paragraph(f"<b>Recommendation:</b> {issue.recommendation}", self.styles['IssueText']))
        
        return elements
    
    def _create_missing_clauses_section(self, missing_clauses):
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("MISSING MANDATORY CLAUSES", self.styles['SectionHeader']))
        elements.append(Spacer(1, 15))
        
        elements.append(Paragraph("The following mandatory clauses are completely missing from the contract and must be added:", self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        missing_data = []
        for i, clause in enumerate(missing_clauses, 1):
            missing_data.append([f"{i}.", clause])
        
        if missing_data:
            missing_table = Table(missing_data, colWidths=[0.5*inch, 5.5*inch])
            missing_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.red),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(missing_table)
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_recommendations_summary(self, result):
        elements = []
        
        elements.append(Paragraph("PRIORITY RECOMMENDATIONS", self.styles['SectionHeader']))
        elements.append(Spacer(1, 15))
        
        high_priority = [issue for issue in result.issues if issue.risk_level == RiskLevel.HIGH and issue.recommendation]
        medium_priority = [issue for issue in result.issues if issue.risk_level == RiskLevel.MEDIUM and issue.recommendation]
        
        if high_priority:
            elements.append(Paragraph("HIGH PRIORITY ACTIONS:", self.styles['SubHeader']))
            high_data = []
            for i, issue in enumerate(high_priority[:5], 1):
                high_data.append([f"{i}.", issue.recommendation])
            
            if high_data:
                high_table = Table(high_data, colWidths=[0.5*inch, 5.5*inch])
                high_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.red),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(high_table)
            
            elements.append(Spacer(1, 15))
        
        if medium_priority:
            elements.append(Paragraph("MEDIUM PRIORITY ACTIONS:", self.styles['SubHeader']))
            medium_data = []
            for i, issue in enumerate(medium_priority[:5], 1):
                medium_data.append([f"{i}.", issue.recommendation])
            
            if medium_data:
                medium_table = Table(medium_data, colWidths=[0.5*inch, 5.5*inch])
                medium_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.orange),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(medium_table)
            
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_footer(self):
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("DISCLAIMER", self.styles['SubHeader']))
        elements.append(Paragraph(
            "This report is generated by an automated legal compliance checking system. "
            "While every effort has been made to ensure accuracy, this analysis should not be "
            "considered as legal advice. Please consult with qualified legal professionals for "
            "final review and validation of all compliance matters.",
            self.styles['Normal']
        ))
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("─" * 80, self.styles['Normal']))
        elements.append(Paragraph(
            f"Report generated by Legal Compliance Checker | {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
        ))
        
        return elements