"""
PDF Export Module for Diabetes Report Generator
Exports reports to NHS-styled PDF format
"""

import io
from typing import Dict, Any, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import KeepTogether, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

class PDFExporter:
    """Export diabetes reports to PDF with NHS styling"""
    
    def __init__(self):
        """Initialize PDF exporter with NHS styles"""
        
        # NHS Colors
        self.nhs_blue = colors.HexColor('#005EB8')
        self.nhs_dark_blue = colors.HexColor('#003087')
        self.nhs_grey = colors.HexColor('#425563')
        self.nhs_light_grey = colors.HexColor('#E8EDEE')
        
        # Create custom styles
        self.styles = self._create_nhs_styles()
    
    def _create_nhs_styles(self) -> Dict:
        """Create NHS-compliant PDF styles"""
        
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='NHS_Title',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=self.nhs_dark_blue,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Heading styles
        styles.add(ParagraphStyle(
            name='NHS_H1',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.nhs_blue,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_H2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.nhs_blue,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_H3',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=self.nhs_grey,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='NHS_Body',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceBefore=3,
            spaceAfter=3
        ))
        
        # Alert style
        styles.add(ParagraphStyle(
            name='NHS_Alert',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#D4351C'),
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#D4351C'),
            borderWidth=1,
            borderPadding=6,
            backColor=colors.HexColor('#FFF0F0')
        ))
        
        # Reference style
        styles.add(ParagraphStyle(
            name='NHS_Reference',
            parent=styles['Normal'],
            fontSize=8,
            textColor=self.nhs_grey,
            leftIndent=12
        ))
        
        return styles
    
    def export_report(
        self,
        report_text: str,
        patient_data: Dict,
        labs_data: Dict,
        sources: Dict,
        filename: Optional[str] = None
    ) -> io.BytesIO:
        """
        Export report to PDF format
        
        Returns:
            BytesIO buffer containing PDF data
        """
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm
        )
        
        # Build content
        story = []
        
        # Add header
        story.extend(self._create_header(patient_data))
        
        # Add at-a-glance box
        story.append(self._create_at_glance_box(labs_data))
        story.append(Spacer(1, 0.5*inch))
        
        # Process report sections
        sections = report_text.split('\n## ')
        
        for section in sections:
            if not section.strip():
                continue
            
            # Handle red flag alerts specially
            if '⚠️ URGENT' in section:
                story.append(self._create_alert_box(section))
            else:
                story.extend(self._process_section(section))
        
        # Add footer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        
        # Return buffer
        buffer.seek(0)
        return buffer
    
    def _create_header(self, patient_data: Dict) -> list:
        """Create PDF header with patient details"""
        
        elements = []
        
        # Title
        title = Paragraph(
            "Personalised Diabetes Management Report",
            self.styles['NHS_Title']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Patient details table
        patient_info = [
            ['Patient Name:', patient_data.get('name', 'Not provided')],
            ['NHS Number:', patient_data.get('nhs_number', 'Not provided')],
            ['Date of Birth:', str(patient_data.get('dob', 'Not provided'))],
            ['Report Date:', datetime.now().strftime('%d %B %Y')],
            ['Prepared by:', 'Diabetes Specialist Team']
        ]
        
        table = Table(patient_info, colWidths=[3*cm, 10*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.nhs_blue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_at_glance_box(self, labs_data: Dict) -> Table:
        """Create at-a-glance summary box"""
        
        # Prepare data
        hba1c = labs_data.get('hba1c', '--')
        fpg = labs_data.get('fpg', '--')
        ppg = labs_data.get('ppg_2h', '--')
        bp_sys = labs_data.get('bp_systolic', '--')
        bp_dia = labs_data.get('bp_diastolic', '--')
        
        # Calculate BMI if possible
        weight = labs_data.get('weight')
        height = labs_data.get('height')
        bmi = '--'
        if weight and height:
            bmi = f"{weight / ((height/100) ** 2):.1f}"
        
        # Create table data
        data = [
            ['AT A GLANCE - Key Metrics', '', '', ''],
            ['HbA1c', f"{hba1c}%", 'FPG', f"{fpg} mmol/L"],
            ['2h-PPG', f"{ppg} mmol/L", 'BP', f"{bp_sys}/{bp_dia} mmHg"],
            ['BMI', f"{bmi} kg/m²", 'Last Labs', labs_data.get('lab_date', 'Recent')]
        ]
        
        # Create and style table
        table = Table(data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # Header row
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, 0), self.nhs_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), self.nhs_light_grey),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 1), (0, -1), 'Helvetica-Bold', 10),
            ('FONT', (2, 1), (2, -1), 'Helvetica-Bold', 10),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('BOX', (0, 0), (-1, -1), 2, self.nhs_blue),
        ]))
        
        return table
    
    def _create_alert_box(self, content: str) -> KeepTogether:
        """Create red flag alert box"""
        
        elements = []
        
        # Parse content
        lines = content.split('\n')
        
        # Title
        alert_title = Paragraph(
            "⚠️ URGENT CLINICAL REVIEW REQUIRED",
            self.styles['NHS_Alert']
        )
        elements.append(alert_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # Alert items
        for line in lines:
            if line.strip().startswith('- '):
                item = Paragraph(line, self.styles['NHS_Body'])
                elements.append(item)
        
        elements.append(Spacer(1, 0.2*inch))
        
        return KeepTogether(elements)
    
    def _process_section(self, section_text: str) -> list:
        """Process a report section for PDF"""
        
        elements = []
        lines = section_text.split('\n')
        
        if not lines:
            return elements
        
        # Section heading
        heading = lines[0].strip()
        if heading:
            # Remove section number if present
            if '. ' in heading:
                heading = heading.split('. ', 1)[1]
            
            para = Paragraph(heading, self.styles['NHS_H1'])
            elements.append(para)
            elements.append(Spacer(1, 0.1*inch))
        
        # Process content
        in_table = False
        table_data = []
        
        for line in lines[1:]:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Handle subsections
            if line.startswith('### '):
                subsection = line.replace('### ', '')
                para = Paragraph(subsection, self.styles['NHS_H3'])
                elements.append(para)
                elements.append(Spacer(1, 0.05*inch))
            
            # Handle table rows
            elif '|' in line and not line.startswith('|---'):
                # Parse table row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if cells:
                    table_data.append(cells)
                    in_table = True
            
            # End of table
            elif in_table and '|' not in line:
                if table_data:
                    elements.append(self._create_table(table_data))
                    elements.append(Spacer(1, 0.1*inch))
                table_data = []
                in_table = False
                
                # Process the line normally
                if line and not line.startswith('|---'):
                    para = Paragraph(line, self.styles['NHS_Body'])
                    elements.append(para)
            
            # Handle list items
            elif line.startswith('- ') or line.startswith('• '):
                bullet_text = '• ' + line[2:]
                para = Paragraph(bullet_text, self.styles['NHS_Body'])
                elements.append(para)
            
            # Regular paragraph
            elif line and not line.startswith('|---'):
                para = Paragraph(line, self.styles['NHS_Body'])
                elements.append(para)
        
        # Handle any remaining table
        if table_data:
            elements.append(self._create_table(table_data))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_table(self, data: list) -> Table:
        """Create a formatted table"""
        
        if not data:
            return None
        
        # Calculate column widths
        num_cols = len(data[0])
        col_width = 12*cm / num_cols
        
        table = Table(data, colWidths=[col_width] * num_cols)
        
        # Style the table
        style_commands = [
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.nhs_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.nhs_grey),
            ('BOX', (0, 0), (-1, -1), 1, self.nhs_blue),
        ]
        
        # Alternate row colors
        for i in range(2, len(data), 2):
            style_commands.append(
                ('BACKGROUND', (0, i), (-1, i), self.nhs_light_grey)
            )
        
        table.setStyle(TableStyle(style_commands))
        
        return table
    
    def _create_footer(self) -> list:
        """Create PDF footer"""
        
        elements = []
        
        elements.append(PageBreak())
        
        # Clinical disclaimer
        disclaimer = Paragraph(
            "<b>Clinical Disclaimer:</b> This report is generated as a clinical decision support tool "
            "and should be reviewed by a qualified healthcare professional before implementation. "
            "It does not replace clinical judgement.",
            self.styles['NHS_Reference']
        )
        elements.append(disclaimer)
        elements.append(Spacer(1, 0.1*inch))
        
        # Timestamp
        timestamp = Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}",
            self.styles['NHS_Reference']
        )
        elements.append(timestamp)
        
        return elements
