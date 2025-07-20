from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
from models.schemas import PolicyChecklist, PolicyStatus

class IntelligentReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_dynamic_styles()

    def _setup_dynamic_styles(self):
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='TableContent',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_LEFT,
            wordWrap='CJK'
        ))
        
        self.styles.add(ParagraphStyle(
            name='StatusText',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='SummaryText',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leftIndent=0,
            rightIndent=0,
            wordWrap='CJK'
        ))

        self.styles.add(ParagraphStyle(
            name='SummaryHeader',
            parent=self.styles['Normal'],
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=10,
            spaceBefore=15
        ))

        self.styles.add(ParagraphStyle(
            name='LegendText',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=4
        ))

    def generate_intelligent_report(self, checklist: PolicyChecklist, doc1_filename: str, doc2_filename: str, output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        story = []

        story.extend(self._create_checklist_table(checklist))
        story.extend(self._create_legend())
        story.extend(self._create_summary_section(checklist))

        doc.build(story)
    
    def _create_checklist_table(self, checklist: PolicyChecklist):
        elements = []
        
        elements.append(Paragraph("Policy Review Checklist", self.styles['ReportTitle']))
        elements.append(Spacer(1, 20))

        categories = {}
        for item in checklist.items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        category_labels = {
            'employment_terms': 'A. Organizational Development',
            'compensation_benefits': 'B. Talent Acquisition', 
            'working_conditions': 'C. Learning & development',
            'termination_conditions': 'D. Performance management',
            'confidentiality_non_compete': 'E. Talent Management',
            'intellectual_property': 'F. HC operation',
            'dispute_resolution': 'G. Compensation & benefits',
            'compliance_regulatory': 'H. Compliance',
            'health_safety': 'I. Health & Safety',
            'leave_policies': 'J. Leave Policies',
            'other': 'K. Other'
        }

        for category, items in categories.items():
            if not items:
                continue
                
            category_label = category_labels.get(category, category.replace('_', ' ').title())
            
            table_data = []
            table_data.append([
                Paragraph("Item", self.styles['TableHeader']),
                Paragraph("Chapter", self.styles['TableHeader']),
                Paragraph("Feedback", self.styles['TableHeader']),
                Paragraph("Comments", self.styles['TableHeader']),
                Paragraph("Suggested Amendments", self.styles['TableHeader'])
            ])
            
            for item in items:
                status_text = self._get_status_text(item.status)

                item_text = item.item if item.item else "General Item"
                chapter_text = item.chapter if item.chapter else "General"
                comments_text = item.comments if item.comments else ""
                amendments_text = item.suggested_amendments if item.suggested_amendments else ""

                table_data.append([
                    Paragraph(item_text, self.styles['TableContent']),
                    Paragraph(chapter_text, self.styles['TableContent']),
                    Paragraph(status_text, self.styles['StatusText']),
                    Paragraph(comments_text, self.styles['TableContent']),
                    Paragraph(amendments_text, self.styles['TableContent'])
                ])
            
            table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1.8*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.white])
            ]))
            
            elements.append(Paragraph(category_label, self.styles['TableHeader']))
            elements.append(Spacer(1, 10))
            elements.append(table)
            elements.append(Spacer(1, 20))
        
        return elements

    def _get_status_text(self, status: PolicyStatus) -> str:
        if status == PolicyStatus.ALIGNED:
            return "Aligned"
        elif status == PolicyStatus.MODERATE:
            return "Needs consideration"
        else:
            return "Unaligned/Missing"

    def _create_legend(self):
        elements = []

        elements.append(Paragraph("Policy Review Checklist", self.styles['SummaryHeader']))
        elements.append(Spacer(1, 10))

        legend_text = """<b>Unaligned/Missing:</b> Missing key information or not aligned to the labor law.<br/>
<b>Moderate:</b> minor comments / room for improvement or consideration.<br/>
<b>Aligned:</b> to our standard and market practices."""

        elements.append(Paragraph(legend_text, self.styles['LegendText']))
        elements.append(Spacer(1, 20))

        return elements

    def _create_summary_section(self, checklist: PolicyChecklist):
        elements = []

        elements.append(PageBreak())
        elements.append(Paragraph("Overall Policy Feedback", self.styles['SummaryHeader']))
        elements.append(Spacer(1, 15))

        stats = checklist.overall_feedback["statistics"]

        feedback_data = [
            ["Feedback", "#"],
            ["Aligned", str(stats["aligned"])],
            ["Moderate", str(stats["moderate"])],
            ["Unaligned/Missing", str(stats["unaligned"])]
        ]

        feedback_table = Table(feedback_data, colWidths=[2*inch, 1*inch])
        feedback_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(feedback_table)
        elements.append(Spacer(1, 20))
        
        assessment_text = checklist.overall_feedback.get("assessment", "")
        if assessment_text:
            elements.append(Paragraph(assessment_text, self.styles['SummaryText']))
        
        if checklist.additional_considerations:
            elements.append(Paragraph("Additional considerations:", self.styles['SummaryText']))
            for consideration in checklist.additional_considerations:
                consideration_text = f"- {consideration}"
                elements.append(Paragraph(consideration_text, self.styles['SummaryText']))
        
        return elements