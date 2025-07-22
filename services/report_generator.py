from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Circle, Rect, Line
from reportlab.graphics import renderPDF
from datetime import datetime
from models.schemas import PolicyAssessment, CriteriaStatus
import os

class IntelligentReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Brand colors from frontend
        self.primary_color = colors.Color(0, 92/255, 77/255)  # #005C4D
        self.accent_color = colors.Color(196/255, 152/255, 79/255)  # #C4984F
        self.success_color = colors.Color(16/255, 185/255, 129/255)  # #10b981
        self.warning_color = colors.Color(245/255, 158/255, 11/255)  # #f59e0b
        self.error_color = colors.Color(239/255, 68/255, 68/255)  # #ef4444
        self.text_primary = colors.Color(30/255, 41/255, 59/255)  # #1e293b
        self.text_secondary = colors.Color(100/255, 116/255, 139/255)  # #64748b
        self.background_alt = colors.Color(248/255, 250/255, 252/255)  # #f8fafc
        self.border_color = colors.Color(226/255, 232/255, 240/255)  # #e2e8f0
        self._setup_professional_styles()

    def _setup_professional_styles(self):
        style_names = [style.name for style in self.styles.byName.values()]
        
        if 'ReportTitle' not in style_names:
            self.styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Heading1'],
                fontSize=22,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=self.primary_color,
                fontName='Helvetica-Bold'
            ))

        if 'ExecutiveHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='ExecutiveHeader',
                parent=self.styles['Heading1'],
                fontSize=16,
                fontName='Helvetica-Bold',
                textColor=self.primary_color,
                alignment=TA_LEFT,
                spaceAfter=15,
                spaceBefore=25
            ))

        if 'CriteriaHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='CriteriaHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                fontName='Helvetica-Bold',
                textColor=self.primary_color,
                alignment=TA_LEFT,
                spaceAfter=12,
                spaceBefore=20,
                leftIndent=0
            ))

        if 'ProfessionalBody' not in style_names:
            self.styles.add(ParagraphStyle(
                name='ProfessionalBody',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica',
                textColor=self.text_primary,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                spaceBefore=3,
                leftIndent=20,
                rightIndent=20,
                firstLineIndent=0,
                wordWrap='CJK',
                leading=14
            ))

        if 'StatusPresent' not in style_names:
            self.styles.add(ParagraphStyle(
                name='StatusPresent',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=self.success_color,
                alignment=TA_LEFT,
                spaceAfter=5,
                leftIndent=30
            ))

        if 'StatusPartial' not in style_names:
            self.styles.add(ParagraphStyle(
                name='StatusPartial',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=self.warning_color,
                alignment=TA_LEFT,
                spaceAfter=5,
                leftIndent=30
            ))

        if 'StatusMissing' not in style_names:
            self.styles.add(ParagraphStyle(
                name='StatusMissing',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=self.error_color,
                alignment=TA_LEFT,
                spaceAfter=5,
                leftIndent=30
            ))

        if 'RecommendationText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='RecommendationText',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica',
                textColor=self.text_primary,
                alignment=TA_JUSTIFY,
                spaceAfter=8,
                leftIndent=40,
                rightIndent=20,
                leading=13
            ))

        if 'ExecutiveText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='ExecutiveText',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica',
                textColor=self.text_primary,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leftIndent=0,
                rightIndent=0,
                leading=14,
                wordWrap='CJK'
            ))

        if 'BrandText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='BrandText',
                parent=self.styles['Normal'],
                fontSize=10,
                fontName='Helvetica',
                textColor=self.text_secondary,
                alignment=TA_CENTER,
                spaceAfter=6
            ))

    def _create_brand_logo(self):
        """Create RAIA brand logo matching the frontend design"""
        drawing = Drawing(200, 60)
        
        # Main brain circle with gradient-like effect (matching frontend)
        main_circle = Circle(30, 30, 28)
        main_circle.fillColor = self.primary_color
        main_circle.strokeColor = self.accent_color
        main_circle.strokeWidth = 1
        drawing.add(main_circle)
        
        # Brain hemispheres (more accurate to frontend brain icon)
        left_hemisphere = Circle(22, 32, 12)
        left_hemisphere.fillColor = colors.white
        left_hemisphere.strokeColor = colors.white
        left_hemisphere.strokeWidth = 0.5
        drawing.add(left_hemisphere)
        
        right_hemisphere = Circle(38, 32, 12)
        right_hemisphere.fillColor = colors.white
        right_hemisphere.strokeColor = colors.white
        right_hemisphere.strokeWidth = 0.5
        drawing.add(right_hemisphere)
        
        # Central division line
        center_line = Line(30, 20, 30, 44)
        center_line.strokeColor = self.primary_color
        center_line.strokeWidth = 2
        drawing.add(center_line)
        
        # Brain texture lines (simplified)
        texture_line1 = Line(18, 38, 26, 35)
        texture_line1.strokeColor = self.primary_color
        texture_line1.strokeWidth = 1
        drawing.add(texture_line1)
        
        texture_line2 = Line(34, 35, 42, 38)
        texture_line2.strokeColor = self.primary_color
        texture_line2.strokeWidth = 1
        drawing.add(texture_line2)
        
        texture_line3 = Line(18, 26, 26, 29)
        texture_line3.strokeColor = self.primary_color
        texture_line3.strokeWidth = 1
        drawing.add(texture_line3)
        
        texture_line4 = Line(34, 29, 42, 26)
        texture_line4.strokeColor = self.primary_color
        texture_line4.strokeWidth = 1
        drawing.add(texture_line4)
        
        return drawing

    def generate_professional_report(self, assessment: PolicyAssessment, regulatory_docs: str, 
                                   policy_filename: str, output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            title="RAIA - Reward AI Assistant Report",
            author="RAIA", 
            subject="Policy Assessment Report",
            topMargin=72,
            bottomMargin=72
        )

        story = []
        story.extend(self._create_branded_header(assessment, policy_filename))
        story.extend(self._create_executive_summary(assessment))
        story.extend(self._create_coverage_overview(assessment))
        story.extend(self._create_criteria_analysis(assessment))
        story.extend(self._create_strategic_recommendations(assessment))
        story.extend(self._create_implementation_roadmap(assessment))

        doc.build(story)

    def _create_branded_header(self, assessment: PolicyAssessment, policy_filename: str):
        elements = []
        
        # Brand header with logo and colors
        # header_table_data = [
        #     [self._create_brand_logo(), "", ""],
        #     ["", "", ""]
        # ]
        
        # header_table = Table(header_table_data, colWidths=[1.5*inch, 3*inch, 1.5*inch], rowHeights=[60, 10])
        # header_table.setStyle(TableStyle([
        #     ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        #     ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        #     ('SPAN', (1, 0), (2, 0)),
        #     ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        #     ('LINEBELOW', (0, 1), (-1, 1), 2, self.primary_color)
        # ]))
        
        # elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Brand title with gradient-like effect
        brand_title = """
        <para align="center" fontSize="24" fontName="Helvetica-Bold">
        <font color="#005C4D">RAIA</font> – <font color="#C4984F">Reward AI Assistant Report</font>
        </para>
        """
        elements.append(Paragraph(brand_title, self.styles['ReportTitle']))
        elements.append(Spacer(1, 15))
        
        # Document info in branded card-like layout
        info_data = [
            ["Document:", assessment.document_analysis.title],
            ["Analysis Date:", datetime.now().strftime('%B %d, %Y')],
            ["Overall Coverage:", f"{assessment.overall_coverage:.1f}%"],
            ["Maturity Score:", f"{assessment.maturity_score:.1f}%"]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.background_alt),
            ('TEXTCOLOR', (0, 0), (0, -1), self.primary_color),
            ('TEXTCOLOR', (1, 0), (1, -1), self.text_primary),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.border_color)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        return elements

    def _create_executive_summary(self, assessment: PolicyAssessment):
        elements = []
        elements.append(Paragraph("Executive Summary", self.styles['ExecutiveHeader']))
        
        present_count = sum(1 for c in assessment.criteria_results if c.status == CriteriaStatus.PRESENT)
        partial_count = sum(1 for c in assessment.criteria_results if c.status == CriteriaStatus.PARTIAL)
        missing_count = sum(1 for c in assessment.criteria_results if c.status == CriteriaStatus.MISSING)
        
        summary_text = f"""
        This comprehensive analysis evaluates the policy document against 9 key organizational criteria. 
        The assessment reveals {present_count} criteria fully present, {partial_count} partially covered, 
        and {missing_count} requiring implementation. The overall coverage score of {assessment.overall_coverage:.1f}% 
        indicates {"excellent" if assessment.overall_coverage >= 80 else "good" if assessment.overall_coverage >= 60 else "moderate" if assessment.overall_coverage >= 40 else "significant"} 
        policy maturity with {"minimal" if assessment.overall_coverage >= 80 else "moderate" if assessment.overall_coverage >= 60 else "substantial"} 
        opportunities for enhancement.
        
        The policy demonstrates {assessment.document_analysis.structure_quality.lower()} structural quality 
        with {assessment.document_analysis.content_density.lower()} content density. Key strengths include 
        {", ".join(assessment.document_analysis.semantic_themes[:3]) if assessment.document_analysis.semantic_themes else "foundational policy elements"}. 
        Priority areas for development focus on {", ".join([c.criteria_name for c in assessment.criteria_results if c.status == CriteriaStatus.MISSING][:3]) if missing_count > 0 else "continuous improvement and refinement"}.
        """
        
        elements.append(Paragraph(summary_text, self.styles['ExecutiveText']))
        elements.append(Spacer(1, 20))
        
        return elements

    def _create_coverage_overview(self, assessment: PolicyAssessment):
        elements = []
        elements.append(Paragraph("Coverage Overview", self.styles['ExecutiveHeader']))
        
        coverage_data = [["Criteria", "Coverage", "Coverage %"]]
        
        for criteria in assessment.criteria_results:
            status_text = "✓ Present" if criteria.status == CriteriaStatus.PRESENT else \
                         "◐ Partial" if criteria.status == CriteriaStatus.PARTIAL else "✗ Missing"
            
            coverage_data.append([
                criteria.criteria_name,
                status_text,
                f"{criteria.coverage_percentage:.0f}%"
            ])
        
        coverage_table = Table(coverage_data, colWidths=[4.5*inch, 1.2*inch, 1*inch])
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.text_primary),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, self.border_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.background_alt])
        ]))
        
        elements.append(coverage_table)
        elements.append(Spacer(1, 25))
        
        return elements

    def _create_criteria_analysis(self, assessment: PolicyAssessment):
        elements = []
        elements.append(Paragraph("Detailed Criteria Analysis", self.styles['ExecutiveHeader']))
        elements.append(Spacer(1, 10))
        
        for i, criteria in enumerate(assessment.criteria_results, 1):
            criteria_title = f"{i}. {criteria.criteria_name}"
            elements.append(Paragraph(criteria_title, self.styles['CriteriaHeader']))
            
            status_style = 'StatusPresent' if criteria.status == CriteriaStatus.PRESENT else \
                          'StatusPartial' if criteria.status == CriteriaStatus.PARTIAL else 'StatusMissing'
            
            status_text = f"Coverage: {criteria.status.value} ({criteria.coverage_percentage:.0f}% coverage)"
            elements.append(Paragraph(status_text, self.styles[status_style]))
            
            if criteria.status == CriteriaStatus.PRESENT:
                analysis_text = f"""
                <b>Quality Assessment:</b> {criteria.quality_assessment}
                
                <b>Found Provisions:</b> {"; ".join(criteria.found_content[:3]) if criteria.found_content else "Comprehensive coverage identified"}
                
                <b>Regulatory Alignment:</b> {criteria.regulatory_alignment}
                """
            elif criteria.status == CriteriaStatus.PARTIAL:
                analysis_text = f"""
                <b>Current Coverage:</b> {criteria.quality_assessment}
                
                <b>Present Elements:</b> {"; ".join(criteria.found_content[:3]) if criteria.found_content else "Basic provisions identified"}
                
                <b>Missing Elements:</b> {"; ".join(criteria.missing_elements[:3]) if criteria.missing_elements else "Additional coverage required"}
                """
            else:
                analysis_text = f"""
                <b>Gap Analysis:</b> {criteria.criteria_name} provisions are not adequately addressed in the current policy framework.
                
                <b>Missing Elements:</b> {"; ".join(criteria.missing_elements[:3]) if criteria.missing_elements else "Comprehensive framework required"}
                
                <b>Impact:</b> This gap represents a significant opportunity for policy enhancement and organizational development.
                """
            
            elements.append(Paragraph(analysis_text, self.styles['ProfessionalBody']))
            
            if criteria.recommendations:
                elements.append(Paragraph("<b>Recommendations:</b>", self.styles['ProfessionalBody']))
                for rec in criteria.recommendations[:2]:
                    elements.append(Paragraph(f"• {rec}", self.styles['RecommendationText']))
            
            elements.append(Spacer(1, 15))
        
        return elements

    def _create_strategic_recommendations(self, assessment: PolicyAssessment):
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("Strategic Recommendations", self.styles['ExecutiveHeader']))
        
        intro_text = f"""
        Based on the comprehensive analysis revealing {assessment.overall_coverage:.1f}% policy coverage, 
        the following strategic recommendations are prioritized to enhance organizational effectiveness and regulatory compliance:
        """
        elements.append(Paragraph(intro_text, self.styles['ExecutiveText']))
        elements.append(Spacer(1, 15))
        
        if assessment.strategic_recommendations:
            for i, recommendation in enumerate(assessment.strategic_recommendations, 1):
                elements.append(Paragraph(f"<b>{i}. {recommendation}</b>", self.styles['ProfessionalBody']))
        
        elements.append(Spacer(1, 20))
        
        return elements

    def _create_implementation_roadmap(self, assessment: PolicyAssessment):
        elements = []
        
        # Branded footer with colors
        footer_table_data = [
            ["", ""],
        ]
        
        footer_table = Table(footer_table_data, colWidths=[6*inch], rowHeights=[2])
        footer_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, self.primary_color),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white)
        ]))
        
        elements.append(Spacer(1, 15))
        elements.append(footer_table)
        elements.append(Spacer(1, 10))
        
        footer_text = f"""
        This analysis provides a comprehensive foundation for policy enhancement. 
        Professional consultation is recommended for detailed implementation planning and regulatory compliance verification.
        """
        elements.append(Paragraph(footer_text, self.styles['ExecutiveText']))
        elements.append(Spacer(1, 10))
        
        # Branded report generation info
        brand_footer = f"""
        <para align="center" fontSize="10">
        <b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')} by 
        <font color="#005C4D"><b>RAIA</b></font> - <font color="#C4984F">Reward AI Assistant Report</font>
        </para>
        """
        elements.append(Paragraph(brand_footer, self.styles['BrandText']))
        
        return elements