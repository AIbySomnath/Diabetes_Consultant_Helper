"""
Enhanced PDF Generator for Diabetes Consultant Reports
Generates professional PDF reports with NHS styling and proper formatting
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import base64

# Register fonts - using default Arial for compatibility
# In production, you would register custom NHS fonts here

class EnhancedPDFGenerator:
    """Generates professional PDF reports with NHS styling"""
    
    def __init__(self):
        self.page_size = A4
        self.styles = self._create_styles()
        
    def _create_styles(self):
        """Create and return paragraph styles for the PDF"""
        styles = getSampleStyleSheet()
        
        # NHS Color Scheme
        nhs_blue = colors.HexColor("#005EB8")
        nhs_dark_blue = colors.HexColor("#003087")
        nhs_bright_blue = colors.HexColor("#0072CE")
        nhs_light_blue = colors.HexColor("#41B6E6")
        nhs_aqua_blue = colors.HexColor("#00A9CE")
        nhs_red = colors.HexColor("#DA291C")
        nhs_dark_pink = colors.HexColor("#9B4393")
        nhs_dark_grey = colors.HexColor("#425563")
        nhs_mid_grey = colors.HexColor("#768692")
        nhs_pale_grey = colors.HexColor("#E8EDEE")
        
        # Add custom styles
        styles.add(ParagraphStyle(
            name='NHS_Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=nhs_blue,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=nhs_dark_blue,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_Heading3',
            parent=styles['Heading3'],
            fontSize=12,
            leading=16,
            textColor=nhs_dark_blue,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_BodyText',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_SmallText',
            parent=styles['Italic'],
            fontSize=8,
            leading=10,
            textColor=nhs_mid_grey,
            spaceAfter=6,
            fontName='Helvetica-Oblique'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_Alert',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            textColor=nhs_red,
            backColor=colors.Color(0.95, 0.9, 0.9),
            borderWidth=1,
            borderColor=nhs_red,
            borderPadding=5,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='NHS_Footer',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=nhs_mid_grey,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        return styles
    
    def _header_footer(self, canvas, doc, patient_name: str):
        """Add header and footer to each page"""
        # Save the state of the canvas
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColorRGB(0, 0.37, 0.72)  # NHS Blue
        
        # NHS Logo and title
        canvas.drawString(2*cm, A4[1] - 2*cm, "NHS")
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 2*cm, 
                             f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Patient info in header
        canvas.setFont('Helvetica', 8)
        canvas.drawString(2*cm, A4[1] - 2.5*cm, f"Patient: {patient_name}")
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColorRGB(0.26, 0.34, 0.39)  # NHS Dark Grey
        canvas.drawCentredString(A4[0]/2, 1*cm, 
                               "Confidential - For clinical use only")
        canvas.drawCentredString(A4[0]/2, 0.5*cm, 
                               f"Page {doc.page}")
        
        # Reset the state
        canvas.restoreState()
    
    def generate_pdf(self, report_content: str, patient_name: str) -> bytes:
        """
        Generate a PDF from the report content
        
        Args:
            report_content: Markdown or text content of the report
            patient_name: Name of the patient for the header
            
        Returns:
            bytes: PDF file as bytes
        """
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2*cm
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add title
        title_style = self.styles['NHS_Heading1']
        elements.append(Paragraph("Diabetes Management Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Add patient info
        elements.append(Paragraph(f"Patient: {patient_name}", self.styles['NHS_BodyText']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}", self.styles['NHS_BodyText']))
        elements.append(Spacer(1, 12))
        
        # Add disclaimer
        disclaimer = """
        <b>Clinical Disclaimer:</b> This report is generated as a clinical decision 
        support tool and should be reviewed by a qualified healthcare professional 
        before implementation. It does not replace clinical judgement.
        """
        elements.append(Paragraph(disclaimer, self.styles['NHS_SmallText']))
        elements.append(Spacer(1, 24))
        
        # Process the report content
        # This is a simplified version - in a real app, you'd parse markdown properly
        sections = self._parse_markdown_sections(report_content)
        
        for section in sections:
            if section['level'] == 1:
                elements.append(Paragraph(section['title'], self.styles['NHS_Heading1']))
            elif section['level'] == 2:
                elements.append(Paragraph(section['title'], self.styles['NHS_Heading2']))
            elif section['level'] == 3:
                elements.append(Paragraph(section['title'], self.styles['NHS_Heading3']))
            else:
                elements.append(Paragraph(section['title'], self.styles['NHS_BodyText']))
            
            for content in section['content']:
                if content.startswith('!ALERT!'):
                    # Handle alert boxes
                    alert_text = content.replace('!ALERT!', '').strip()
                    elements.append(Paragraph(alert_text, self.styles['NHS_Alert']))
                else:
                    # Regular paragraph
                    elements.append(Paragraph(content, self.styles['NHS_BodyText']))
            
            elements.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(
            elements,
            onFirstPage=lambda c, d: self._header_footer(c, d, patient_name),
            onLaterPages=lambda c, d: self._header_footer(c, d, patient_name)
        )
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _parse_markdown_sections(self, markdown_text: str) -> List[Dict]:
        """
        Simple markdown parser that extracts sections and content
        
        This is a simplified version - in a real app, you'd use a proper markdown parser
        """
        sections = []
        current_section = None
        
        for line in markdown_text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for headings
            if line.startswith('### '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'level': 3,
                    'title': line[4:].strip(),
                    'content': []
                }
            elif line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'level': 2,
                    'title': line[3:].strip(),
                    'content': []
                }
            elif line.startswith('# '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'level': 1,
                    'title': line[2:].strip(),
                    'content': []
                }
            else:
                if current_section is None:
                    current_section = {'level': 1, 'title': 'Report', 'content': []}
                current_section['content'].append(line)
        
        # Add the last section
        if current_section:
            sections.append(current_section)
        
        return sections

# Example usage
if __name__ == "__main__":
    # Example report content
    sample_report = """
# Diabetes Management Report

## Summary
This is a sample diabetes management report.

## Key Findings
- HbA1c is above target
- Blood pressure well controlled
- Weight management recommended

!ALERT! Urgent: Patient requires medication review

## Recommendations
1. Increase physical activity
2. Follow dietary advice
3. Regular monitoring
"""
    
    # Generate PDF
    generator = EnhancedPDFGenerator()
    pdf_bytes = generator.generate_pdf(sample_report, "John Smith")
    
    # Save to file for testing
    with open("sample_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    print("PDF generated: sample_report.pdf")
