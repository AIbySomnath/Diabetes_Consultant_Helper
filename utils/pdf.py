"""
PDF export utility using ReportLab to render consultant-grade reports
"""
import os
from typing import Dict
from pathlib import Path
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from utils.formatters import render_text_report

class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbering"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for (page_num, page_state) in enumerate(self._saved_page_states):
            self.__dict__.update(page_state)
            self.draw_page_number(page_num + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_num, total_pages):
        self.setFont("Helvetica", 9)
        self.drawRightString(
            A4[0] - 0.75*inch, 0.5*inch,
            f"Page {page_num} of {total_pages}"
        )
        self.drawString(
            0.75*inch, 0.5*inch,
            f"NHS Diabetes Report - Generated {datetime.now().strftime('%d %b %Y')}"
        )

class PDFGenerator:
    """Generate PDF reports from text reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for NHS report formatting"""
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='ReportHeader',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#003087'),  # NHS Blue
            alignment=TA_CENTER
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=12,
            textColor=colors.HexColor('#003087'),
            alignment=TA_LEFT
        ))
        
        # Monospace style for ASCII tables
        self.styles.add(ParagraphStyle(
            name='Monospace',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=10,
            leftIndent=0
        ))
        
        # Clinical data style
        self.styles.add(ParagraphStyle(
            name='ClinicalData',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11,
            leftIndent=12
        ))
    
    def generate_pdf_report(self, patient_data: Dict, report_data: Dict, rules: Dict) -> bytes:
        """
        Generate PDF report from patient and report data
        
        Returns:
            PDF content as bytes
        """
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch,
            canvasmaker=NumberedCanvas
        )
        
        # Generate text report
        text_report = render_text_report(report_data, patient_data, rules)
        
        # Build PDF content
        story = self._build_pdf_story(text_report, patient_data, report_data)
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _build_pdf_story(self, text_report: str, patient_data: Dict, report_data: Dict) -> list:
        """Build the PDF story from text report"""
        story = []
        
        # Split text report into sections
        lines = text_report.split('\n')
        current_section = []
        
        for line in lines:
            # Check if this is a section boundary or special formatting
            if line.startswith('┌') or line.startswith('├') or line.startswith('└'):
                # ASCII table border - add current section and start table
                if current_section:
                    story.extend(self._process_section(current_section))
                    current_section = []
                
                # Find the complete table
                table_lines = [line]
                continue
            
            elif line.startswith('│'):
                # Table row
                current_section.append(line)
            
            elif line.startswith('Page ') and ('of' in line):
                # Page break indicator
                if current_section:
                    story.extend(self._process_section(current_section))
                    current_section = []
                story.append(PageBreak())
            
            else:
                current_section.append(line)
        
        # Add final section
        if current_section:
            story.extend(self._process_section(current_section))
        
        return story
    
    def _process_section(self, lines: list) -> list:
        """Process a section of text into PDF elements"""
        elements = []
        
        for line in lines:
            line = line.strip()
            if not line:
                elements.append(Spacer(1, 6))
                continue
            
            # Check for headers and special formatting
            if line.startswith('PERSONALISED DIABETES REPORT'):
                elements.append(Paragraph(line, self.styles['ReportHeader']))
            
            elif any(line.startswith(num) for num in ['1)', '2)', '3)', '4)', '5)', '6)', '7)']):
                # Section headers
                elements.append(Paragraph(line, self.styles['SectionHeader']))
            
            elif line.startswith('│') or '┌' in line or '├' in line or '└' in line:
                # ASCII table - render in monospace
                elements.append(Paragraph(line, self.styles['Monospace']))
            
            elif line.startswith('•'):
                # Bullet points
                elements.append(Paragraph(line, self.styles['ClinicalData']))
            
            else:
                # Regular text
                elements.append(Paragraph(line, self.styles['Normal']))
        
        return elements
    
    def _create_snapshot_table(self, patient_data: Dict, rules: Dict) -> Table:
        """Create the traffic light snapshot table"""
        from utils.formatters import create_clinical_snapshot
        
        snapshot = create_clinical_snapshot(patient_data, rules)
        
        # Table headers
        data = [['Metric', 'Current', 'Target', 'Status']]
        
        # Add rows from snapshot
        for key, info in snapshot.items():
            metric_name = {
                'hba1c': 'HbA1c',
                'bp': 'Blood Pressure', 
                'bmi': 'BMI',
                'ldl': 'LDL Cholesterol'
            }.get(key, key.upper())
            
            data.append([
                metric_name,
                info['value'],
                info['target'],
                info['traffic']['display']
            ])
        
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.8*inch, 1.2*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003087')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        return table
    
    def save_pdf_to_file(self, pdf_content: bytes, filepath: str) -> str:
        """Save PDF content to file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        
        return str(filepath)

if __name__ == "__main__":
    # Test PDF generation
    generator = PDFGenerator()
    
    # Sample data
    sample_patient = {
        "name": "Test Patient",
        "dob": "1980-05-15",
        "sex": "Male",
        "diabetes_type": "T1DM",
        "weight_kg": 78.5,
        "height_cm": 175.0,
        "bp_sys": 127,
        "bp_dia": 83,
        "labs": {
            "hba1c_pct": 8.3,
            "lipids": {"ldl": 3.2}
        }
    }
    
    sample_report = {
        "executive_summary": "Test summary",
        "emr_note": "Test EMR note"
    }
    
    from rules import load_rules
    rules = load_rules()
    
    pdf_content = generator.generate_pdf_report(sample_patient, sample_report, rules)
    
    # Save test PDF
    test_file = "test_report.pdf"
    generator.save_pdf_to_file(pdf_content, test_file)
    print(f"Test PDF saved as {test_file}")
    print(f"PDF size: {len(pdf_content)} bytes")
