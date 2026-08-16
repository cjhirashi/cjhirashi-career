"""PDF Generation endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.models import CVRequest, CoverLetterRequest
from src.services.cv_generator import CVGenerator
from src.services.cover_letter_generator import CoverLetterGenerator
from src.services.pdf_service import PDFService
from src.utils.validators import InputValidator
from src.utils.formatters import DataFormatter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["PDF Generation"])

# Initialize services
cv_generator = CVGenerator()
cover_letter_generator = CoverLetterGenerator()
pdf_service = PDFService()
validator = InputValidator()
formatter = DataFormatter()


@router.post("/cv")
async def generate_cv(request: CVRequest):
    """Generate CV PDF.

    Args:
        request: CV generation request

    Returns:
        StreamingResponse with PDF data
    """
    try:
        logger.info(f"Processing CV generation request for {request.name}")

        # Validate input
        validator.validate_cv_data(
            name=request.name,
            email=request.email,
            phone=request.phone,
            location=request.location,
            ikigai=request.ikigai,
            about=request.about,
            competencies=[c.dict() for c in request.competencies],
            experience=[e.dict() for e in request.experience],
            education=[edu.dict() for edu in request.education],
            projects=[p.dict() for p in request.projects],
        )

        # Format data
        competencies = formatter.format_competencies(
            [c.dict() for c in request.competencies]
        )
        experience = formatter.format_experience(
            [e.dict() for e in request.experience]
        )
        education = formatter.format_education(
            [edu.dict() for edu in request.education]
        )
        projects = formatter.format_projects(
            [p.dict() for p in request.projects]
        )

        # Generate PDF
        pdf_buffer = cv_generator.generate_cv(
            name=request.name,
            email=request.email,
            phone=request.phone,
            location=request.location,
            ikigai=request.ikigai,
            about=request.about,
            competencies=competencies,
            experience=experience,
            education=education,
            projects=projects,
        )

        # Get filename
        filename = cv_generator.get_cv_filename(request.name)
        pdf_size = pdf_service.get_pdf_size(pdf_buffer)

        logger.info(f"CV generated: {filename} ({pdf_size} bytes)")

        # Return PDF as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating CV")


@router.post("/cover-letter")
async def generate_cover_letter(request: CoverLetterRequest):
    """Generate Cover Letter PDF.

    Args:
        request: Cover Letter generation request

    Returns:
        StreamingResponse with PDF data
    """
    try:
        logger.info(
            f"Processing Cover Letter generation request for {request.name} at {request.company_name}"
        )

        # Validate input
        validator.validate_cover_letter_data(
            name=request.name,
            email=request.email,
            date=request.date,
            company_name=request.company_name,
            company_address=request.company_address,
            recipient_name=request.recipient_name,
            position=request.position,
            body=request.body,
            closing_statement=request.closing_statement,
            signature=request.signature,
        )

        # Generate PDF
        pdf_buffer = cover_letter_generator.generate_cover_letter(
            name=request.name,
            email=request.email,
            date=request.date,
            company_name=request.company_name,
            company_address=request.company_address,
            recipient_name=request.recipient_name,
            position=request.position,
            body=request.body,
            closing_statement=request.closing_statement,
            signature=request.signature,
        )

        # Get filename
        filename = cover_letter_generator.get_cover_letter_filename(
            request.name, request.company_name
        )
        pdf_size = pdf_service.get_pdf_size(pdf_buffer)

        logger.info(f"Cover Letter generated: {filename} ({pdf_size} bytes)")

        # Return PDF as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Cover Letter: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating Cover Letter")
