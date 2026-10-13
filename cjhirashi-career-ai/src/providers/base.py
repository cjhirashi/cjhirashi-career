"""
Interfaz de proveedor de modelos (spec 009, RF-005, D-05).

`ModelProvider` es la superficie que usa el bucle de agente: Converse (con y sin
streaming), generación de imágenes, catálogo de modelos y estimación de coste.
Los tipos son neutros: no mencionan ningún SDK. La única implementación es
`providers/bedrock/`, que es el único módulo que importa `boto3`/`botocore`.

Paridad (D-13): `messages` conserva la forma de bloques de contenido que ya
persiste el harness (`text`, `toolUse`, `toolResult`), porque es lo que guardan
las tablas `bedrock_*`; los tipos neutros cubren lo que cambia por proveedor.
"""
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Protocol, runtime_checkable


class ProviderError(Exception):
    """Fallo recuperable o de configuración del proveedor de modelos."""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class ToolCall:
    id: str
    name: str
    input: Dict[str, Any] = field(default_factory=dict)
    # Presente si el JSON de argumentos llegó inválido (streaming): el bucle lo devuelve al modelo.
    input_parse_error: Optional[str] = None


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass
class ModelRequest:
    model_id: str
    messages: List[Dict[str, Any]]
    system_prompt: str
    tools: List[ToolSpec] = field(default_factory=list)
    max_tokens: int = 4096
    force_tool_use: bool = False


@dataclass
class ModelResponse:
    text: str
    stop_reason: Optional[str]
    usage: Usage
    tool_calls: List[ToolCall] = field(default_factory=list)


@dataclass
class StreamEvent:
    kind: Literal["text", "tool_call", "usage", "stop"]
    text: str = ""
    tool_call: Optional[ToolCall] = None
    usage: Optional[Usage] = None
    stop_reason: Optional[str] = None


@dataclass(frozen=True)
class ImageOptions:
    aspect_ratio: str = "1:1"


@dataclass
class ImageResult:
    data: bytes


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    label: str
    tier: str
    invoke_via: str = "foundation"
    price_input_per_million: float = 0.0
    price_output_per_million: float = 0.0
    supports_prompt_cache: bool = False


@runtime_checkable
class ModelProvider(Protocol):
    async def converse(self, request: ModelRequest) -> ModelResponse: ...

    def converse_stream(self, request: ModelRequest) -> AsyncIterator[StreamEvent]: ...

    async def generate_image(self, prompt: str, options: ImageOptions) -> ImageResult: ...

    def list_models(self) -> List[ModelInfo]: ...

    def estimate_cost(self, model_id: str, usage: Usage) -> float: ...
