"""Sanitize assistant text before it is stored, replayed, or shown in chat."""
import re

# ============================================================================
# Patrones de chain-of-thought
# ============================================================================

_THINK_BLOCK = re.compile(
    r"<\s*(thinking|think)\s*>.*?<\s*/\s*\1\s*>",
    re.DOTALL | re.IGNORECASE,
)
_UNCLOSED_THINK = re.compile(
    r"<\s*(thinking|think)\s*>.*",
    re.DOTALL | re.IGNORECASE,
)
_THINK_TAG = re.compile(r"<\s*/?\s*(thinking|think)\s*>", re.IGNORECASE)


# ============================================================================
# Sanitización de respuesta del asistente
# ============================================================================

def sanitize_assistant_reply(text: str) -> str:
    """Drop model chain-of-thought markup, keep the user-facing answer.

    Some models (DeepSeek, Qwen, and occasionally Claude) emit reasoning as
    ``<thinking>`` / ``<think>`` inside the Converse ``text`` block. If the
    entire reply lived inside those tags, keep the inner text without tags so
    the user still sees the answer.
    """
    if not text:
        return ""

    without_blocks = _THINK_BLOCK.sub("", text)
    without_unclosed = _UNCLOSED_THINK.sub("", without_blocks)
    cleaned = without_unclosed.strip()
    if cleaned:
        return cleaned
    return _THINK_TAG.sub("", text).strip()
