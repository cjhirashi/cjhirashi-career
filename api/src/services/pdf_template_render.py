"""Sustitución simple {{variable}} en plantillas HTML."""
import re
from typing import Any, Dict


def render_template_html(html_template: str, variables: Dict[str, Any]) -> str:
    """Reemplaza {{key}} por str(variables[key]); deja la clave si falta."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key not in variables:
            return match.group(0)
        value = variables[key]
        if value is None:
            return ""
        return str(value)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", repl, html_template)
