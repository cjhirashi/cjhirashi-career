"""
PDF generation — WeasyPrint in-process, isolated in a process pool.

Same public API the routes and Bedrock tools already call:
`generate_markdown_document` / `generate_html_template_pdf` → PDF bytes.
"""
import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor

from services.pdf.worker import render_html_template_pdf, render_markdown_document_pdf
from services.error_reporting import report_error

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 60.0
_pool: ProcessPoolExecutor | None = None


class PDFGeneratorError(Exception):
    pass


def _new_pool() -> ProcessPoolExecutor:
    # Default context is fork on Linux (our Docker image). Isolates
    # Cairo/Pango crashes from uvicorn.
    return ProcessPoolExecutor(max_workers=2)


def _get_pool() -> ProcessPoolExecutor:
    global _pool
    if _pool is None:
        _pool = _new_pool()
    return _pool


def _reset_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.shutdown(wait=False, cancel_futures=True)
        _pool = None
    _pool = _new_pool()


async def _run_in_pool(fn, *args) -> bytes:
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_get_pool(), fn, *args),
            timeout=_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as e:
        logger.error("PDF generation timed out after %ss", _TIMEOUT_SECONDS)
        report_error(
            f"PDF generation timed out after {_TIMEOUT_SECONDS}s",
            "service:pdf_service._run_in_pool", error_type="TimeoutError", exc=e,
            severity="error",
        )
        _reset_pool()
        raise
    except ValueError:
        raise
    except Exception:
        _reset_pool()
        raise


async def generate_markdown_document(title: str, content: str) -> bytes:
    """Render a title + Markdown body to PDF bytes."""
    try:
        return await _run_in_pool(render_markdown_document_pdf, title, content)
    except ValueError as e:
        logger.error("Markdown PDF validation failed: %s", e)
        raise PDFGeneratorError(str(e)) from e
    except Exception as e:
        logger.error("Markdown PDF generation failed: %s", e)
        report_error(
            str(e) or "Markdown PDF generation failed",
            "service:pdf_service.generate_markdown_document",
            error_type=type(e).__name__, exc=e, severity="error",
        )
        raise PDFGeneratorError("No se pudo generar el PDF") from e


async def generate_html_template_pdf(
    title: str, html_body: str, css_content: str | None = None
) -> bytes:
    """Render custom HTML + optional CSS to PDF bytes (WeasyPrint)."""
    try:
        return await _run_in_pool(render_html_template_pdf, title, html_body, css_content)
    except ValueError as e:
        logger.error("HTML template PDF validation failed: %s", e)
        raise PDFGeneratorError(str(e)) from e
    except Exception as e:
        logger.error("HTML template PDF generation failed: %s", e)
        report_error(
            str(e) or "HTML template PDF generation failed",
            "service:pdf_service.generate_html_template_pdf",
            error_type=type(e).__name__, exc=e, severity="error",
        )
        raise PDFGeneratorError("No se pudo generar el PDF") from e
