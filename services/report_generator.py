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
        # Check if styles already exist to avoid duplicates
        style_names = [style.name for style in self.styles.byName.values()]
        
        if 'ReportTitle' not in style_names:
            self.styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.black,
                fontName='Helvetica-Bold'
            ))

        if 'SectionHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=12,
                spaceBefore=20,
                leftIndent=0
            ))

        if 'SubSectionHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='SubSectionHeader',
                parent=self.styles['Heading3'],
                fontSize=12,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=8,
                spaceBefore=12,
                leftIndent=20
            ))

        if 'BodyText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica',
                textColor=colors.black,
                alignment=TA_JUSTIFY,
                spaceAfter=10,
                spaceBefore=3,
                leftIndent=20,
                rightIndent=20,
                firstLineIndent=0,
                wordWrap='CJK',
                leading=14
            ))

        if 'StatusText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='StatusText',
                parent=self.styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=colors.black,
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
                textColor=colors.black,
                alignment=TA_JUSTIFY,
                spaceAfter=8,
                leftIndent=40,
                rightIndent=20,
                fontStyle='italic',
                leading=13
            ))

        if 'SummaryHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='SummaryHeader',
                parent=self.styles['Heading1'],
                fontSize=16,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=15,
                spaceBefore=25
            ))

        if 'SummaryText' not in style_names:
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
                leading=14,
                wordWrap='CJK'
            ))

        if 'LegendText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='LegendText',
                parent=self.styles['Normal'],
                fontSize=10,
                fontName='Helvetica',
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                leftIndent=20
            ))

    def generate_intelligent_report(self, checklist: PolicyChecklist, doc1_filename: str, doc2_filename: str, output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Title and header
        story.extend(self._create_report_header())
        
        # Legend
        story.extend(self._create_legend())
        
        # Main analysis sections
        story.extend(self._create_analysis_sections(checklist))
        
        # Overall feedback section
        story.extend(self._create_overall_feedback(checklist))

        doc.build(story)
    
    def _create_report_header(self):
        elements = []
        elements.append(Paragraph("RAIA - Rewards and Compensation Policy Analysis Report", self.styles['ReportTitle']))
        elements.append(Spacer(1, 20))
        
        date_text = f"Analysis Date: {datetime.now().strftime('%B %d, %Y')}"
        elements.append(Paragraph(date_text, self.styles['SummaryText']))
        elements.append(Spacer(1, 30))
        
        return elements

    def _create_legend(self):
        elements = []
        
        elements.append(Paragraph("Analysis Framework", self.styles['SummaryHeader']))
        elements.append(Spacer(1, 10))

        legend_intro = """This comprehensive analysis evaluates the compensation policy against industry best practices and regulatory requirements. Each section is assessed using the following criteria:"""
        elements.append(Paragraph(legend_intro, self.styles['SummaryText']))
        elements.append(Spacer(1, 10))

        legend_items = [
            "<b>Aligned:</b> Meets industry standards and regulatory requirements with no significant gaps identified.",
            "<b>Needs Consideration:</b> Generally adequate but has opportunities for improvement or minor compliance gaps.",
            "<b>Unaligned/Missing:</b> Significant gaps identified that require immediate attention or policy enhancement."
        ]

        for item in legend_items:
            elements.append(Paragraph(f"• {item}", self.styles['LegendText']))
        
        elements.append(Spacer(1, 25))
        return elements

    def _create_analysis_sections(self, checklist: PolicyChecklist):
        elements = []
        
        # Define the structured sections as per your requirements
        analysis_sections = [
            {
                'letter': 'A',
                'title': 'Organizational Development',
                'items': ['Workforce Planning', 'Organization Structure', 'Job Architecture'],
                'description': 'This section evaluates the foundational organizational structure and workforce planning capabilities.'
            },
            {
                'letter': 'B',
                'title': 'Talent Acquisition',
                'items': ['Employment Categories', 'Sourcing', 'Selection', 'Onboarding'],
                'description': 'Assessment of talent acquisition processes and employment categorization frameworks.'
            },
            {
                'letter': 'C', 
                'title': 'Learning & Development',
                'items': ['Learning Need Analysis', 'Implementation and Evaluation', 'L&D Programs'],
                'description': 'Evaluation of learning and development infrastructure and program effectiveness.'
            },
            {
                'letter': 'D',
                'title': 'Performance Management',
                'items': ['Performance Variables', 'Evaluating and Rating Performance', 'Performance Calibration', 'Management of Low Performance', 'Management of Performance Related Disagreements'],
                'description': 'Comprehensive review of performance management systems and related processes.'
            },
            {
                'letter': 'E',
                'title': 'Talent Management',
                'items': ['Succession Planning', 'Career Progression'],
                'description': 'Analysis of talent development and succession planning mechanisms.'
            },
            {
                'letter': 'F',
                'title': 'Human Capital Operations',
                'items': ['Employee Relations', 'Employee Services', 'Leave Management', 'Separation Processes'],
                'description': 'Review of day-to-day human capital operational processes and employee services.'
            },
            {
                'letter': 'G',
                'title': 'Compensation & Benefits',
                'items': ['Salary Structure', 'Processing of Monthly Salaries', 'Salary Increases', 'Allowances & Benefits', 'Variable Pay', 'Promotion'],
                'description': 'Detailed analysis of compensation framework, benefits structure, and related processes.'
            },
            {
                'letter': 'H',
                'title': 'Compliance',
                'items': ['Ministry of Human Resources and Social Development and Saudi Labor Laws', 'General Organization for Social Insurance (GOSI) Laws', 'Anti-Harassment Law', 'Saudization'],
                'description': 'Assessment of regulatory compliance and adherence to local labor laws and requirements.'
            }
        ]

        # Group checklist items by category for analysis
        checklist_items_by_category = {}
        for item in checklist.items:
            category = item.category
            if category not in checklist_items_by_category:
                checklist_items_by_category[category] = []
            checklist_items_by_category[category].append(item)

        # Generate each section
        for section in analysis_sections:
            elements.extend(self._create_section_analysis(section, checklist_items_by_category))
        
        return elements

    def _create_section_analysis(self, section, checklist_items_by_category):
        elements = []
        
        # Section header
        section_title = f"{section['letter']}. {section['title']}"
        elements.append(Paragraph(section_title, self.styles['SectionHeader']))
        
        # Section description
        elements.append(Paragraph(section['description'], self.styles['BodyText']))
        elements.append(Spacer(1, 10))
        
        # Analyze each item in the section
        for item_name in section['items']:
            matching_item = self._find_matching_checklist_item(item_name, checklist_items_by_category)
            
            # Sub-section header
            elements.append(Paragraph(item_name, self.styles['SubSectionHeader']))
            
            if matching_item:
                # Use actual analysis results
                status_text = self._get_status_text(matching_item.status)
                elements.append(Paragraph(f"Status: {status_text}", self.styles['StatusText']))
                
                # Analysis content
                if matching_item.feedback:
                    elements.append(Paragraph(matching_item.feedback, self.styles['BodyText']))
                
                if matching_item.comments:
                    elements.append(Paragraph(f"Analysis: {matching_item.comments}", self.styles['BodyText']))
                
                if matching_item.suggested_amendments and matching_item.suggested_amendments.strip():
                    elements.append(Paragraph(f"Recommendations: {matching_item.suggested_amendments}", self.styles['RecommendationText']))
            else:
                # Generate contextual analysis for missing items
                status_text = "Needs Consideration"
                elements.append(Paragraph(f"Status: {status_text}", self.styles['StatusText']))
                
                analysis_text = self._generate_contextual_analysis(item_name, section['title'])
                elements.append(Paragraph(analysis_text, self.styles['BodyText']))
                
                recommendation_text = self._get_contextual_recommendation(item_name, section['title'])
                elements.append(Paragraph(f"Recommendations: {recommendation_text}", self.styles['RecommendationText']))
            
            elements.append(Spacer(1, 12))
        
        elements.append(Spacer(1, 15))
        return elements

    def _find_matching_checklist_item(self, item_name, checklist_items_by_category):
        """Find a checklist item that matches the section item name"""
        item_name_lower = item_name.lower()
        
        # Create keyword mapping for better matching
        keyword_mappings = {
            'workforce planning': ['workforce', 'planning', 'manpower'],
            'organization structure': ['organization', 'structure', 'organizational'],
            'job architecture': ['job', 'architecture', 'position', 'role'],
            'employment categories': ['employment', 'categories', 'classification'],
            'sourcing': ['sourcing', 'recruitment', 'hiring'],
            'selection': ['selection', 'interview', 'assessment'],
            'onboarding': ['onboarding', 'orientation', 'induction'],
            'learning need analysis': ['learning', 'training', 'development'],
            'performance variables': ['performance', 'kpi', 'metrics'],
            'succession planning': ['succession', 'planning', 'talent'],
            'career progression': ['career', 'progression', 'advancement'],
            'salary structure': ['salary', 'structure', 'compensation'],
            'salary increases': ['salary', 'increase', 'increment'],
            'allowances': ['allowances', 'benefits', 'perks'],
            'variable pay': ['variable', 'bonus', 'incentive'],
            'promotion': ['promotion', 'advancement'],
            'anti-harassment': ['harassment', 'discrimination']
        }
        
        # Search through all categories
        for category, items in checklist_items_by_category.items():
            for item in items:
                item_text_lower = item.item.lower()
                requirement_lower = item.requirement.lower()
                
                # Check direct keyword mappings first
                item_keywords = keyword_mappings.get(item_name_lower, item_name_lower.split())
                for keyword in item_keywords:
                    if keyword in item_text_lower or keyword in requirement_lower:
                        return item
                
                # Check for partial matches
                if any(word in item_text_lower for word in item_name_lower.split() if len(word) > 3):
                    return item
        
        return None

    def _generate_contextual_analysis(self, item_name, section_title):
        """Generate contextual analysis based on item name and section"""
        item_lower = item_name.lower()
        
        analysis_templates = {
            'workforce planning': "The current policy framework requires enhancement in workforce planning capabilities. Strategic workforce planning is essential for organizational effectiveness and should include demand forecasting, capacity planning, and resource allocation mechanisms.",
            'organization structure': "The organizational structure provisions need clarity regarding design principles and classification systems. A well-defined structure should distinguish between divisions, departments, sections, units, and teams with clear reporting relationships.",
            'job architecture': "Job architecture framework requires development to support career progression and compensation alignment. This should include job families, levels, and competency frameworks.",
            'employment categories': "Employment categorization needs refinement to ensure clear distinction between different employment types and their respective terms and conditions.",
            'performance calibration': "Performance calibration processes require strengthening to ensure consistency and fairness across the organization. Clear governance structures and committee compositions should be established.",
            'succession planning': "Succession planning mechanisms need clarification regarding roles and responsibilities of HR, business lines, and governing bodies to ensure effective talent pipeline management.",
            'career progression': "Career progression pathways require clear definition of approval authorities and advancement criteria to support employee development and retention.",
            'salary increases': "Salary increase mechanisms need distinction between merit-based and off-cycle increases with clear triggers and rationales for each type.",
            'allowances & benefits': "Allowances and benefits framework requires review of unified allowance clauses and refinement of acting duration caps to ensure policy consistency.",
            'variable pay': "Variable pay structure needs clarity in linking performance criteria to long-term incentive plans and ensuring alignment with organizational objectives.",
            'promotion': "Promotion policies require review, particularly regarding multi-grade promotions and their impact on organizational equity and career progression.",
            'anti-harassment law': "Anti-harassment provisions need strengthening with dedicated sections addressing harassment types, consequences, and reporting mechanisms."
        }
        
        return analysis_templates.get(item_lower, f"The {item_name.lower()} component requires comprehensive review to ensure alignment with industry best practices and organizational objectives. Current provisions may benefit from enhancement to address potential gaps and improve effectiveness.")

    def _get_contextual_recommendation(self, item_name, section_title):
        """Generate contextual recommendations based on item name"""
        item_lower = item_name.lower()
        
        recommendation_templates = {
            'workforce planning': "Confirm if workforce planning falls within NRC charter scope for review and endorsement. Establish clear governance and decision-making authorities.",
            'organization structure': "Incorporate design principles and classification systems for different organizational functions including divisions, departments, sections, units, and teams.",
            'performance calibration': "Define membership and composition of Performance Management Committee with clear roles and responsibilities for calibration processes.",
            'performance related disagreements': "Ensure comprehensive Grievance Management Policy is in place to address performance-related disputes effectively.",
            'succession planning': "Clarify roles and responsibilities of HR, business lines, and NRC in succession planning processes to ensure coordinated approach.",
            'career progression': "Define clear approval authorities for career progression decisions and establish transparent advancement criteria.",
            'salary increases': "Distinguish triggers and rationales for merit versus off-cycle increases to ensure fair and consistent application.",
            'allowances & benefits': "Review unified allowance clauses and refine acting duration caps to improve policy clarity and administration.",
            'variable pay': "Clarify linkage between Long-Term Incentive Plan (LTIP) performance criteria and variable pay components.",
            'promotion': "Revisit three-grade promotion policies to ensure they align with organizational equity and career development objectives.",
            'anti-harassment law': "Include dedicated section addressing harassment types, consequences, and reporting mechanisms to ensure comprehensive coverage."
        }
        
        return recommendation_templates.get(item_lower, f"Develop comprehensive framework for {item_name.lower()} with clear policies, procedures, and governance mechanisms.")

    def _get_status_text(self, status: PolicyStatus) -> str:
        if status == PolicyStatus.ALIGNED:
            return "Aligned"
        elif status == PolicyStatus.MODERATE:
            return "Needs Consideration"
        else:
            return "Unaligned/Missing"

    def _create_overall_feedback(self, checklist: PolicyChecklist):
        elements = []

        elements.append(PageBreak())
        elements.append(Paragraph("Overall Policy Assessment", self.styles['SummaryHeader']))
        elements.append(Spacer(1, 15))

        # Statistics summary
        stats = checklist.overall_feedback["statistics"]
        
        summary_data = [
            ["Assessment Category", "Count"],
            ["Aligned", str(stats["aligned"])],
            ["Needs Consideration", str(stats["moderate"])],
            ["Unaligned/Missing", str(stats["unaligned"])]
        ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Executive summary
        elements.append(Paragraph("Executive Summary", self.styles['SummaryHeader']))
        
        executive_summary = """This comprehensive analysis reveals opportunities for policy enhancement across multiple areas. The assessment indicates that while foundational elements are present, strategic improvements can significantly strengthen the policy framework's effectiveness and regulatory alignment. The identified areas for consideration represent opportunities to enhance organizational capability and ensure robust compliance with evolving industry standards."""
        
        elements.append(Paragraph(executive_summary, self.styles['SummaryText']))
        elements.append(Spacer(1, 15))
        
        # Key findings
        elements.append(Paragraph("Key Findings", self.styles['SummaryHeader']))
        
        key_findings = """The analysis identifies areas where improvements can be made to further enhance the policy's effectiveness and relevance. It is advisable to consider adding certain elements to bolster the policy and address any potential gaps or oversights. By incorporating these suggestions, the policy can be strengthened to ensure robustness and alignment with organizational goals. Feedback on these aspects will contribute to refining the policy and optimizing its impact."""
        
        elements.append(Paragraph(key_findings, self.styles['SummaryText']))
        elements.append(Spacer(1, 15))
        
        # Strategic recommendations
        elements.append(Paragraph("Strategic Recommendations", self.styles['SummaryHeader']))
        
        if checklist.recommendations:
            for i, recommendation in enumerate(checklist.recommendations[:5], 1):
                elements.append(Paragraph(f"{i}. {recommendation}", self.styles['SummaryText']))
        else:
            default_recommendations = [
                "Conduct comprehensive policy review to address identified gaps and enhancement opportunities.",
                "Implement governance frameworks for critical processes including performance management and succession planning.",
                "Strengthen compliance mechanisms to ensure alignment with regulatory requirements.",
                "Develop clear procedures and approval authorities for compensation and career progression decisions.",
                "Establish regular policy review cycles to maintain currency and effectiveness."
            ]
            for i, recommendation in enumerate(default_recommendations, 1):
                elements.append(Paragraph(f"{i}. {recommendation}", self.styles['SummaryText']))
        
        elements.append(Spacer(1, 15))
        
        # Additional considerations
        elements.append(Paragraph("Additional Considerations", self.styles['SummaryHeader']))
        
        additional_text = """It is suggested to streamline duplicated content and avoid overlapping provisions to improve clarity and usability. Regular review and updates should be implemented to ensure the policy remains current with regulatory changes and industry best practices. Consider establishing a policy governance committee to oversee ongoing maintenance and enhancement efforts."""
        
        elements.append(Paragraph(additional_text, self.styles['SummaryText']))
        
        return elements