"""Ensure tool rounds preserve conversation prefix (user message first)."""


def test_tool_round_extends_messages_instead_of_replacing():
    """Regression: replacing messages dropped the opening user turn (Nova ValidationException)."""
    history = [{"role": "user", "content": [{"text": "Hola"}]}]
    messages = list(history)

    assistant_content = [{"toolUse": {"toolUseId": "t1", "name": "list_pdf_templates", "input": {}}}]
    tool_result_content = [{"toolResult": {"toolUseId": "t1", "content": [{"text": "{}"}], "status": "success"}}]

    messages.extend([
        {"role": "assistant", "content": assistant_content},
        {"role": "user", "content": tool_result_content},
    ])

    assert messages[0]["role"] == "user"
    assert messages[0]["content"][0]["text"] == "Hola"
    assert len(messages) == 3
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
