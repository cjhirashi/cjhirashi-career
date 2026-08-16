"""Cover Letter PDF Template using ReportLab."""

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from typing import List


class CoverLetterTemplate:
    """Cover Letter Template for PDF generation using ReportLab."""

    # Colors
    TEXT_COLOR = HexColor("#000000")
    SECTION_COLOR = HexColor("#0891B2")

    # Fonts and sizes
    HEADER_FONT_SIZE = 12
    BODY_FONT_SIZE = 11
    SMALL_FONT_SIZE = 10

    def __init__(
        self,
        name: str,
        email: str,
    ):
        """Initialize Cover Letter template."""
        self.name = name
        self.email = email

    def generate(
        self,
        date: str,
        company_name: str,
        company_address: str,
        recipient_name: str,
        position: str,
        body: str,
        closing_statement: str,
        signature: str,
    ) -> BytesIO:
        """Generate Cover Letter PDF and return as BytesIO.

        Args:
            date: Letter date (YYYY-MM-DD format)
            company_name: Target company name
            company_address: Company address
            recipient_name: Recipient name
            position: Position applied for
            body: Letter body content
            closing_statement: Closing statement before signature
            signature: Sender signature

        Returns:
            BytesIO object with PDF data
        """
        # Create BytesIO buffer
        pdf_buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build story (list of elements)
        story = []

        # Add sender info
        story.extend(self._build_sender_info())

        # Add spacing
        story.append(Spacer(1, 0.3 * inch))

        # Add date
        story.extend(self._build_date(date))

        # Add spacing
        story.append(Spacer(1, 0.2 * inch))

        # Add recipient address
        story.extend(self._build_recipient_address(company_name, company_address))

        # Add spacing
        story.append(Spacer(1, 0.2 * inch))

        # Add salutation
        story.extend(self._build_salutation(recipient_name, position))

        # Add spacing
        story.append(Spacer(1, 0.15 * inch))

        # Add body
        story.extend(self._build_body(body))

        # Add closing
        story.append(Spacer(1, 0.15 * inch))
        story.extend(self._build_closing(closing_statement, signature))

        # Build PDF
        doc.build(story)

        # Rewind buffer position
        pdf_buffer.seek(0)

        return pdf_buffer

    def _build_sender_info(self) -> List:
        """Build sender contact information."""
        styles = getSampleStyleSheet()

        sender_style = ParagraphStyle(
            "Sender",
            parent=styles["Normal"],
            fontSize=self.HEADER_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.02 * inch,
            fontName="Helvetica-Bold",
        )

        email_style = ParagraphStyle(
            "Email",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.05 * inch,
            fontName="Helvetica",
        )

        elements = [
            Paragraph(self.name, sender_style),
            Paragraph(self.email, email_style),
        ]

        return elements

    def _build_date(self, date: str) -> List:
        """Build date section."""
        styles = getSampleStyleSheet()

        date_style = ParagraphStyle(
            "Date",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.05 * inch,
            fontName="Helvetica",
        )

        return [Paragraph(date, date_style)]

    def _build_recipient_address(self, company_name: str, address: str) -> List:
        """Build recipient address section."""
        styles = getSampleStyleSheet()

        address_style = ParagraphStyle(
            "Address",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.05 * inch,
            fontName="Helvetica",
        )

        elements = [
            Paragraph(company_name, address_style),
            Paragraph(address, address_style),
        ]

        return elements

    def _build_salutation(self, recipient_name: str, position: str) -> List:
        """Build letter salutation."""
        styles = getSampleStyleSheet()

        salutation_style = ParagraphStyle(
            "Salutation",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.1 * inch,
            fontName="Helvetica",
        )

        text = f"Dear {recipient_name},<br/><br/>I am writing to express my interest in the {position} position."
        return [Paragraph(text, salutation_style)]

    def _build_body(self, body_text: str) -> List:
        """Build letter body."""
        styles = getSampleStyleSheet()

        body_style = ParagraphStyle(
            "LetterBody",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.1 * inch,
            alignment=4,  # Justified
            fontName="Helvetica",
        )

        # Split body into paragraphs for better formatting
        paragraphs = body_text.split("\n\n")
        elements = []

        for para in paragraphs:
            if para.strip():
                # Replace newlines within paragraph with spaces
                para_text = " ".join(para.split("\n"))
                elements.append(Paragraph(para_text, body_style))

        return elements

    def _build_closing(self, closing_statement: str, signature: str) -> List:
        """Build letter closing and signature."""
        styles = getSampleStyleSheet()

        closing_style = ParagraphStyle(
            "Closing",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.3 * inch,
            fontName="Helvetica",
        )

        signature_style = ParagraphStyle(
            "Signature",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            fontName="Helvetica",
        )

        elements = [
            Paragraph(closing_statement, closing_style),
            Paragraph("Sincerely,<br/><br/>", closing_style),
            Paragraph(signature, signature_style),
        ]

        return elements
