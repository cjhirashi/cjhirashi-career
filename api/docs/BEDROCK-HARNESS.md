# Bedrock Harness local — API

## Paquete

`src/services/bedrock/` — ver [README del paquete](../src/services/bedrock/README.md).

## Endpoint principal

`POST /bedrock/chat` — SSE events:

- `status` — progreso
- `delegation_start` / `delegation_end` — chat general
- `done` — `{ reply, affected_resources }`
- `error`

Body (`BedrockChatRequest`):

```json
{
  "session_id": "uuid",
  "message": "texto",
  "chat_surface": "contextual|general",
  "page_context": { "route": "/career/vacancies", "resource_key": "vacancies" },
  "model_id": "opcional",
  "agent_profile_id": "opcional"
}
```

## Otros

- `GET /bedrock/conversations?session_type=general|contextual&agent_profile_id=agent_professional_identity|agent_orchestrator|…`
- `GET /bedrock/knowledge/search?q=...` — búsqueda semántica Qdrant

Documentación HTTP completa: [sections/bedrock/README.md](sections/bedrock/README.md). Índice de docs API: [README.md](README.md).

---

## IAM {#iam}

El Harness local usa la API **Converse** de `bedrock-runtime` con el usuario IAM configurado en `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (típicamente `portafolio-bedrock-agent`).

### Permisos requeridos

| API | Acción IAM |
|-----|------------|
| `Converse` (default) | `bedrock:InvokeModel` |
| `ConverseStream` (opcional, `BEDROCK_USE_CONVERSE_STREAM=true`) | `bedrock:InvokeModelWithResponseStream` |
| Titan Embeddings | `bedrock:InvokeModel` |
| Titan Image | `bedrock:InvokeModel` |

**Importante:** Los modelos con prefijo `us.` (Claude, Nova Pro/Premier) usan **inference profiles** geográficos US y enrutan a `us-east-1`, `us-east-2` y `us-west-2`. Los demás (`amazon.nova-lite`, `meta.*`, etc.) usan **foundation model** directo en la región del cliente (`us-east-1`). La política IAM debe cubrir inference profiles **y** foundation models en las tres regiones US.

### Catálogo de modelos (`api/src/config.py`)

| Model ID | Tipo IAM | Notas |
|----------|----------|-------|
| `amazon.nova-micro-v1:0` | foundation | Solo `us-east-1` |
| `amazon.nova-lite-v1:0` | foundation | Solo `us-east-1` |
| `deepseek.v3.2` | foundation | |
| `meta.llama3-3-70b-instruct-v1:0` | foundation | |
| `mistral.mistral-large-2402-v1:0` | foundation | |
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | inference_profile | Requiere permiso en us-east-1/2 + us-west-2 |
| `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | inference_profile | Idem |
| `us.amazon.nova-pro-v1:0` | inference_profile | Idem |
| `us.amazon.nova-premier-v1:0` | inference_profile | Idem |

### Política IAM recomendada

Reemplaza `858838169216` por tu account ID si difiere.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockConverseInferenceProfiles",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1:858838169216:inference-profile/*"
    },
    {
      "Sid": "BedrockConverseFoundationModels",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/*",
        "arn:aws:bedrock:us-east-2::foundation-model/*",
        "arn:aws:bedrock:us-west-2::foundation-model/*"
      ]
    },
    {
      "Sid": "BedrockEmbeddingsAndImages",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-image-generator-v2:0"
      ]
    }
  ]
}
```

### Pasos en la consola AWS

1. **IAM → Users → `portafolio-bedrock-agent`**
2. **Add permissions → Create inline policy → JSON**
3. Pega la política de arriba → **Review → Create policy**
4. **Amazon Bedrock → Model access** (región `us-east-1`):
   - Habilita **Claude Haiku 4.5** y **Claude Sonnet 4.5** (Anthropic — requiere aceptar términos / Marketplace)
   - Habilita **Amazon Nova** (Lite, Pro, Premier, Micro según catálogo en `api/src/config.py`)
   - Habilita otros modelos del catálogo si los usarás (Llama, Mistral, Cohere, DeepSeek)
5. Espera 1–2 minutos y vuelve a probar el chat

### Errores frecuentes

| Error | Causa | Solución |
|-------|-------|----------|
| `not authorized to perform: bedrock:InvokeModel on inference-profile/...` | Falta permiso IAM en inference profiles | Añadir statement `inference-profile/*` |
| `not authorized to perform: bedrock:InvokeModelWithResponseStream` | Falta permiso streaming | Añadir acción o dejar `BEDROCK_USE_CONVERSE_STREAM=false` |
| `AccessDeniedException` con modelo Anthropic habilitado en Model access | Política solo en foundation-model, no inference-profile | Añadir inference profiles |
| `ValidationException: conversation must start with a user message` | Bug en historial del harness (rondas tool) o mensajes duplicados | Actualizar api_rest; no es Model access |
| Modelo no responde tras IAM correcto | Model access no habilitado | Primera invocación o Bedrock Model catalog |

### Variables relacionadas

```env
BEDROCK_REGION=us-east-1
BEDROCK_USE_CONVERSE_STREAM=false
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```
