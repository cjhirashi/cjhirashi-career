from services.bedrock.converse_client import parse_converse_response
from services.bedrock.reply_text import sanitize_assistant_reply


def test_strips_thinking_block_and_keeps_visible_answer():
    raw = (
        "<thinking>Voy a revisar las vacantes.</thinking>\n\n"
        "No hay cambios recientes en las vacantes."
    )
    assert sanitize_assistant_reply(raw) == "No hay cambios recientes en las vacantes."


def test_keeps_inner_text_when_entire_reply_is_wrapped():
    raw = (
        "<thinking>Parece que actualmente no hay cambios recientes en las "
        "vacantes ni en el registro de carrera.</thinking>"
    )
    assert sanitize_assistant_reply(raw) == (
        "Parece que actualmente no hay cambios recientes en las "
        "vacantes ni en el registro de carrera."
    )


def test_strips_think_aliases_and_unclosed_blocks():
    assert sanitize_assistant_reply("<think>razon</think>\nListo.") == "Listo."
    assert sanitize_assistant_reply("Respuesta final.<thinking>corte") == "Respuesta final."


def test_parse_converse_response_drops_thinking_markup():
    parsed = parse_converse_response(
        {
            "output": {
                "message": {
                    "content": [
                        {"text": "<thinking>interno</thinking>\nHola."},
                        {"reasoningContent": {"reasoningText": {"text": "no mostrar"}}},
                    ]
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 1, "outputTokens": 2},
        }
    )
    assert parsed["text"] == "Hola."
    assert parsed["stop_reason"] == "end_turn"
