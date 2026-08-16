"""CV PDF Template using ReportLab."""

from io import BytesIO
from typing import List, Dict, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class CVTemplate:
    """CV Template for PDF generation using ReportLab."""

    # Colors
    PRIMARY_COLOR = HexColor("#0891B2")  # Cyan
    TEXT_COLOR = HexColor("#000000")
    SECTION_COLOR = HexColor("#0891B2")
    LIGHT_GRAY = HexColor("#F3F4F6")

    # Fonts and sizes
    HEADER_FONT_SIZE = 24
    TITLE_FONT_SIZE = 14
    SECTION_FONT_SIZE = 12
    BODY_FONT_SIZE = 10
    SMALL_FONT_SIZE = 9

    def __init__(
        self,
        name: str,
        email: str,
        phone: str,
        location: str,
        ikigai: str,
        about: str,
    ):
        """Initialize CV template."""
        self.name = name
        self.email = email
        self.phone = phone
        self.location = location
        self.ikigai = ikigai
        self.about = about

    def generate(
        self,
        competencies: List[Dict],
        experience: List[Dict],
        education: List[Dict],
        projects: List[Dict],
    ) -> BytesIO:
        """Generate CV PDF and return as BytesIO.

        Args:
            competencies: List of competency dictionaries
            experience: List of experience dictionaries
            education: List of education dictionaries
            projects: List of project dictionaries

        Returns:
            BytesIO object with PDF data
        """
        # Create BytesIO buffer
        pdf_buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Build story (list of elements)
        story = []

        # Add header
        story.extend(self._build_header())

        # Add sections
        story.append(Spacer(1, 0.1 * inch))
        story.extend(self._build_ikigai_section())

        story.append(Spacer(1, 0.15 * inch))
        story.extend(self._build_competencies_section(competencies))

        if experience:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_experience_section(experience))

        if projects:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_projects_section(projects))

        if education:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_education_section(education))

        # Build PDF
        doc.build(story)

        # Rewind buffer position
        pdf_buffer.seek(0)

        return pdf_buffer

    def _build_header(self) -> List:
        """Build header section with name and contact info."""
        styles = getSampleStyleSheet()

        # Custom styles
        name_style = ParagraphStyle(
            "CustomName",
            parent=styles["Heading1"],
            fontSize=self.HEADER_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.05 * inch,
            fontName="Helvetica-Bold",
        )

        contact_style = ParagraphStyle(
            "Contact",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.1 * inch,
            fontName="Helvetica",
        )

        elements = [
            Paragraph(self.name, name_style),
            Paragraph(
                f"{self.email} | {self.phone} | {self.location}",
                contact_style,
            ),
        ]

        return elements

    def _build_ikigai_section(self) -> List:
        """Build IKIGAI / Professional Summary section."""
        styles = getSampleStyleSheet()

        section_style = self._get_section_header_style()
        body_style = ParagraphStyle(
            "SectionBody",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.1 * inch,
            alignment=0,
        )

        elements = [
            Paragraph("IKIGAI / PROFESSIONAL SUMMARY", section_style),
            Paragraph(self.ikigai, body_style),
            Paragraph(self.about, body_style),
        ]

        return elements

    def _build_competencies_section(self, competencies: List[Dict]) -> List:
        """Build Key Competencies section."""
        styles = getSampleStyleSheet()
        section_style = self._get_section_header_style()

        elements = [
            Paragraph("KEY COMPETENCIES", section_style),
        ]

        # Group by category
        categories = {}
        for comp in competencies:
            cat = comp.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(comp)

        body_style = ParagraphStyle(
            "CompBody",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.05 * inch,
            leftIndent=0.2 * inch,
        )

        for category, comps in categories.items():
            cat_style = ParagraphStyle(
                "Category",
                parent=styles["Normal"],
                fontSize=self.SMALL_FONT_SIZE,
                textColor=self.SECTION_COLOR,
                spaceAfter=0.03 * inch,
                fontName="Helvetica-Bold",
            )
            elements.append(Paragraph(f"<b>{category}</b>", cat_style))

            comp_names = [f"{c['name']} ({c['level']})" for c in comps]
            comp_text = " • ".join(comp_names)
            elements.append(Paragraph(comp_text, body_style))

        return elements

    def _build_experience_section(self, experience: List[Dict]) -> List:
        """Build Professional Experience section."""
        styles = getSampleStyleSheet()
        section_style = self._get_section_header_style()

        elements = [
            Paragraph("PROFESSIONAL EXPERIENCE", section_style),
        ]

        for exp in experience:
            elements.extend(self._build_experience_entry(exp))

        return elements

    def _build_experience_entry(self, exp: Dict) -> List:
        """Build a single experience entry."""
        styles = getSampleStyleSheet()

        # Position and company
        header_style = ParagraphStyle(
            "ExpHeader",
            parent=styles["Normal"],
            fontSize=self.SECTION_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.02 * inch,
            fontName="Helvetica-Bold",
        )

        # Dates
        date_style = ParagraphStyle(
            "ExpDates",
            parent=styles["Normal"],
            fontSize=self.SMALL_FONT_SIZE,
            textColor=HexColor("#6B7280"),
            spaceAfter=0.05 * inch,
            fontName="Helvetica-Oblique",
        )

        # Description
        desc_style = ParagraphStyle(
            "ExpDesc",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.08 * inch,
            leftIndent=0.2 * inch,
        )

        end_date = exp.get("end_date", "present")
        if end_date.lower() == "present":
            end_date = "Present"

        elements = [
            Paragraph(f"{exp['position']} at {exp['company']}", header_style),
            Paragraph(f"{exp['start_date']} - {end_date}", date_style),
            Paragraph(exp["description"], desc_style),
        ]

        return elements

    def _build_projects_section(self, projects: List[Dict]) -> List:
        """Build Projects section."""
        styles = getSampleStyleSheet()
        section_style = self._get_section_header_style()

        elements = [
            Paragraph("PROJECTS", section_style),
        ]

        for project in projects:
            elements.extend(self._build_project_entry(project))

        return elements

    def _build_project_entry(self, project: Dict) -> List:
        """Build a single project entry."""
        styles = getSampleStyleSheet()

        # Project name
        name_style = ParagraphStyle(
            "ProjName",
            parent=styles["Normal"],
            fontSize=self.SECTION_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.02 * inch,
            fontName="Helvetica-Bold",
        )

        # Description
        desc_style = ParagraphStyle(
            "ProjDesc",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.03 * inch,
            leftIndent=0.2 * inch,
        )

        # Technologies
        tech_style = ParagraphStyle(
            "ProjTech",
            parent=styles["Normal"],
            fontSize=self.SMALL_FONT_SIZE,
            textColor=HexColor("#6B7280"),
            spaceAfter=0.08 * inch,
            leftIndent=0.2 * inch,
            fontName="Helvetica-Oblique",
        )

        elements = [
            Paragraph(project["name"], name_style),
            Paragraph(project["description"], desc_style),
        ]

        if project.get("technologies"):
            tech_text = f"Technologies: {', '.join(project['technologies'])}"
            elements.append(Paragraph(tech_text, tech_style))

        if project.get("link"):
            link_style = ParagraphStyle(
                "Link",
                parent=styles["Normal"],
                fontSize=self.SMALL_FONT_SIZE,
                textColor=self.SECTION_COLOR,
                spaceAfter=0.08 * inch,
                leftIndent=0.2 * inch,
                textDecoration="underline",
            )
            elements.append(Paragraph(str(project["link"]), link_style))

        return elements

    def _build_education_section(self, education: List[Dict]) -> List:
        """Build Education section."""
        styles = getSampleStyleSheet()
        section_style = self._get_section_header_style()

        elements = [
            Paragraph("EDUCATION", section_style),
        ]

        for edu in education:
            elements.extend(self._build_education_entry(edu))

        return elements

    def _build_education_entry(self, edu: Dict) -> List:
        """Build a single education entry."""
        styles = getSampleStyleSheet()

        # Degree and school
        header_style = ParagraphStyle(
            "EduHeader",
            parent=styles["Normal"],
            fontSize=self.SECTION_FONT_SIZE,
            textColor=self.TEXT_COLOR,
            spaceAfter=0.02 * inch,
            fontName="Helvetica-Bold",
        )

        # Field and year
        details_style = ParagraphStyle(
            "EduDetails",
            parent=styles["Normal"],
            fontSize=self.BODY_FONT_SIZE,
            textColor=HexColor("#6B7280"),
            spaceAfter=0.08 * inch,
            leftIndent=0.2 * inch,
        )

        elements = [
            Paragraph(f"{edu['degree']} from {edu['school']}", header_style),
            Paragraph(f"{edu['field']} ({edu['year']})", details_style),
        ]

        return elements

    def _get_section_header_style(self) -> ParagraphStyle:
        """Get styled section header."""
        return ParagraphStyle(
            "SectionHeader",
            fontSize=self.SECTION_FONT_SIZE,
            textColor=self.SECTION_COLOR,
            spaceAfter=0.1 * inch,
            fontName="Helvetica-Bold",
            borderPadding=5,
        )
