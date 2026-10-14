"""T-084a — `services/attachments.py` (RF-005): adjuntos de chat -> content blocks Converse.

Traslado de `cjhirashi-career-api/src/services/bedrock/attachments.py::build_user_content_blocks`
(la API no tenía tests de este módulo; los valores exactos salen del código).

Interfaz que T-084b debe cumplir
--------------------------------
    async def build_user_content_blocks(db, user_id, message, attachments) -> list[dict]

* Misma firma de 4 posicionales que usa el bucle (`agent_loop.build_user_content_blocks`, ver el docstring de
  `test_agent_loop.py`). `db` y `user_id` se conservan por compatibilidad y NO se usan: no hay BD de archivos
  en el harness (D-10). El dueño del archivo lo fija la credencial, no un filtro `user_id` (en la API era
  `FileUpload.user_id == user_id`; ahora lo impone la API REST al recibir el JWT del usuario).
* El archivo se lee por REST con `FilesClient(get_api_client())` (`clients/files.py`), creado en cada llamada
  (los tests sustituyen el cliente por proceso, `clients.api_client._default`). La credencial es la del
  contexto (`Principal`/`ServiceContext`, D-10): no se pasa ni se cachea. Peticiones:
    1. `GET /files/{file_id}`      metadatos: `original_filename`, `mime_type`, `file_size`, `download_url`
                                   (D-25; hoy la ruta no existe, la crea T-0xx de la API).
    2. `GET /files/{file_id}/raw`  bytes (sólo si el tamaño es admisible; lo ya rechazado no se descarga).
    3. `GET /files/{file_id}/download` -> `{"url": ...}` sólo para tipos no soportados sin `download_url`
                                   (sustituye a `storage_service.get_presigned_url`). `FilesClient` NO tiene
                                   método para ella: T-084b la añade (con su test) o usa `api.get_json`.
* Errores: `providers.base.ProviderError` (la API usaba `BedrockError`, que aquí es subclase de aquélla):
  - 404 de metadatos, o `file_id` con caracteres inseguros (nunca se envía petición) ->
    `Adjunto no encontrado: file_id=<id>`.
  - Otros fallos de la API (401/403/5xx/sin respuesta) o credencial ausente se PROPAGAN tal cual
    (`ApiError`/`MissingCredentialError`); no se disfrazan de "no encontrado".
* Divergencia a decidir en T-084b/API: la API filtraba `is_active`; la ruta REST `GET /files/{id}` debe
  devolver 404 para archivos inactivos (no hay forma de saberlo desde aquí). Se anota en tasks.md.
"""
import importlib

import httpx
import pytest

from clients import api_client
from clients.api_client import ApiError, MissingCredentialError
from middleware.principal import ServiceContext, service_scope
from providers.base import ProviderError
from tests.unit.clients._helpers import USER, as_user, make_api

pytestmark = pytest.mark.requisito("RF-005")

MB5 = 5 * 1024 * 1024


@pytest.fixture
def attachments():
    """Importa `services.attachments` de forma perezosa: rojo = ModuleNotFoundError en cada test (T-084b pendiente)."""
    return importlib.import_module("services.attachments")


class Db:
    """`db` ya no se usa: cualquier acceso falla."""


def meta(file_id="f1", name="foto.png", mime="image/png", size=3, download_url=None):
    return {
        "id": file_id, "user_id": "u1", "original_filename": name, "stored_filename": f"private/{name}",
        "file_type": "image", "mime_type": mime, "file_size": size, "is_public": False,
        "download_url": download_url,
    }


@pytest.fixture
def store(monkeypatch, attachments):
    """API simulada de `/files`: `store.add(meta, data)`; registra las peticiones."""
    class Store:
        files: dict = {}
        presigned = "https://signed.test/x?sig=1"

        def add(self, m, data=b"DATA"):
            self.files[m["id"]] = (m, data)

        def handler(self, req: httpx.Request) -> httpx.Response:
            parts = req.url.path.strip("/").split("/")
            if parts[0] != "files" or len(parts) < 2 or parts[1] not in self.files:
                return httpx.Response(404, json={"detail": "Archivo no encontrado"})
            m, data = self.files[parts[1]]
            if len(parts) == 2:
                return httpx.Response(200, json=m)
            if parts[2] == "raw":
                return httpx.Response(200, content=data, headers={"content-type": m["mime_type"] or ""})
            if parts[2] == "download":
                return httpx.Response(200, json={"url": self.presigned})
            return httpx.Response(404, json={"detail": "?"})

    s = Store()
    s.files = {}
    api, rec = make_api(s.handler)
    monkeypatch.setattr(api_client, "_default", api)
    s.rec = rec
    return s


async def build(message, attachments_):
    attachments = importlib.import_module("services.attachments")
    with as_user():
        return await attachments.build_user_content_blocks(Db(), "u1", message, attachments_)


# ---- sin adjuntos ----------------------------------------------------------------------------------

@pytest.mark.parametrize("atts", [None, []])
async def test_without_attachments_returns_only_the_text(store, atts):
    assert await build("hola", atts) == [{"text": "hola"}]
    assert store.rec.requests == []


async def test_message_is_stripped_when_there_are_text_parts(store):
    assert await build("  hola \n", None) == [{"text": "hola"}]


async def test_empty_or_blank_message_is_kept_verbatim_in_the_fallback_block(store):
    assert await build("", None) == [{"text": ""}]
    assert await build("   ", None) == [{"text": "   "}]
    assert await build(None, None) == [{"text": ""}]


@pytest.mark.parametrize("raw", [{}, {"file_id": None}, {"file_id": ""}, {"name": "x"}])
async def test_attachment_without_file_id_is_skipped_without_requests(store, raw):
    assert await build("hola", [raw]) == [{"text": "hola"}]
    assert store.rec.requests == []


async def test_blank_message_with_only_an_attachment_without_file_id_keeps_the_blank_text(store):
    assert await build("   ", [{"name": "x"}, {"file_id": ""}]) == [{"text": "   "}]
    assert store.rec.requests == []


# ---- inexistente / errores -------------------------------------------------------------------------

async def test_missing_attachment_raises_exact_error(store):
    with pytest.raises(ProviderError) as info:
        await build("mira", [{"file_id": "nope"}])
    assert str(info.value) == "Adjunto no encontrado: file_id=nope"
    assert [r.url.path for r in store.rec.requests] == ["/files/nope"]


async def test_unsafe_file_id_is_not_found_and_sends_no_request(store):
    with pytest.raises(ProviderError) as info:
        await build("mira", [{"file_id": "../admin/users"}])
    assert str(info.value) == "Adjunto no encontrado: file_id=../admin/users"
    assert store.rec.requests == []


async def test_error_on_a_later_attachment_aborts_the_whole_build(store):
    store.add(meta("f1"))
    with pytest.raises(ProviderError, match=r"^Adjunto no encontrado: file_id=f2$"):
        await build("mira", [{"file_id": "f1"}, {"file_id": "f2"}])


async def test_other_api_failures_propagate_unchanged(monkeypatch):
    api, _ = make_api(lambda r: httpx.Response(403, json={"detail": "prohibido"}))
    monkeypatch.setattr(api_client, "_default", api)
    with pytest.raises(ApiError) as info:
        await build("mira", [{"file_id": "f1"}])
    assert info.value.status == 403 and not isinstance(info.value, ProviderError)


async def test_without_any_credential_it_fails_instead_of_inventing_one(store, attachments):
    with pytest.raises(MissingCredentialError):
        await attachments.build_user_content_blocks(Db(), "u1", "mira", [{"file_id": "f1"}])
    assert store.rec.requests == []


# ---- límite de tamaño ------------------------------------------------------------------------------

async def test_size_exactly_at_the_5mb_limit_is_accepted(store):
    store.add(meta("f1", "grande.pdf", "application/pdf", MB5), b"X")
    blocks = await build("mira", [{"file_id": "f1"}])
    assert blocks[1]["document"]["name"] == "grande.pdf"


async def test_size_one_byte_over_the_limit_is_rejected_without_downloading(store):
    store.add(meta("f1", "grande.pdf", "application/pdf", MB5 + 1))
    with pytest.raises(ProviderError) as info:
        await build("mira", [{"file_id": "f1"}])
    assert str(info.value) == "Adjunto demasiado grande (máx 5 MB): grande.pdf"
    assert [r.url.path for r in store.rec.requests] == ["/files/f1"]  # nunca se pidió /raw


# ---- imagen ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("mime,fmt", [
    ("image/png", "png"), ("image/jpeg", "jpg"), ("image/gif", "gif"), ("image/webp", "webp"),
    ("IMAGE/PNG", "png"),
])
async def test_image_block_shape_and_formats(store, mime, fmt):
    store.add(meta("f1", "foto.x", mime, 3), b"\x89PNG")
    blocks = await build("mira", [{"file_id": "f1"}])
    assert blocks == [
        {"text": "mira\n\n[Adjunto: foto.x] (imagen incluida)"},
        {"image": {"format": fmt, "source": {"bytes": b"\x89PNG"}}},
    ]


async def test_image_with_empty_message_has_only_the_label_in_the_text(store):
    store.add(meta("f1", "foto.png", "image/png", 3), b"PNG")
    assert await build("", [{"file_id": "f1"}]) == [
        {"text": "[Adjunto: foto.png] (imagen incluida)"},
        {"image": {"format": "png", "source": {"bytes": b"PNG"}}},
    ]


# ---- documento -------------------------------------------------------------------------------------

@pytest.mark.parametrize("mime,fmt", [("application/pdf", "pdf"), ("text/plain", "txt"), ("text/markdown", "md")])
async def test_document_block_shape_and_formats(store, mime, fmt):
    store.add(meta("f1", "cv.doc", mime, 4), b"%PDF")
    assert await build("revisa", [{"file_id": "f1"}]) == [
        {"text": "revisa\n\n[Adjunto: cv.doc] (documento incluido)"},
        {"document": {"format": fmt, "name": "cv.doc", "source": {"bytes": b"%PDF"}}},
    ]


async def test_document_name_is_truncated_to_100_chars_but_label_keeps_the_full_name(store):
    name = "n" * 120 + ".pdf"
    store.add(meta("f1", name, "application/pdf", 4), b"%PDF")
    blocks = await build("x", [{"file_id": "f1"}])
    assert blocks[1]["document"]["name"] == name[:100] and len(blocks[1]["document"]["name"]) == 100
    assert blocks[0]["text"] == f"x\n\n[Adjunto: {name}] (documento incluido)"


# ---- texto inline y tipos no soportados --------------------------------------------------------------

@pytest.mark.parametrize("mime", ["text/csv", "application/json"])
async def test_other_text_types_are_inlined_as_text_without_blocks(store, mime):
    store.add(meta("f1", "d.csv", mime, 9), "a,b\ná,é".encode())
    assert await build("mira", [{"file_id": "f1"}]) == [{"text": "mira\n\n[Adjunto: d.csv]\na,b\ná,é"}]


async def test_inlined_text_is_cut_at_8000_chars_and_invalid_utf8_is_replaced(store):
    store.add(meta("f1", "d.csv", "text/csv", 9000), b"a" * 9000)
    text = (await build("", [{"file_id": "f1"}]))[0]["text"]
    assert text == "[Adjunto: d.csv]\n" + "a" * 8000
    store.add(meta("f2", "b.csv", "text/csv", 3), b"\xff\xfeA")
    assert (await build("", [{"file_id": "f2"}]))[0]["text"] == "[Adjunto: b.csv]\n��A"


async def test_unsupported_mime_uses_the_files_own_download_url_when_present(store):
    store.add(meta("f1", "a.zip", "application/zip", 9, download_url="https://pub.test/a.zip"))
    assert await build("mira", [{"file_id": "f1"}]) == [
        {"text": "mira\n\n[Adjunto: a.zip] URL: https://pub.test/a.zip"}
    ]
    assert not any(r.url.path.endswith("/download") for r in store.rec.requests)


@pytest.mark.parametrize("mime", ["application/zip", None, ""])
async def test_unsupported_or_missing_mime_without_download_url_asks_the_api_for_a_signed_url(store, mime):
    store.add(meta("f1", "a.bin", mime, 9))
    assert await build("mira", [{"file_id": "f1"}]) == [
        {"text": f"mira\n\n[Adjunto: a.bin] URL: {store.presigned}"}
    ]
    assert any(r.url.path == "/files/f1/download" for r in store.rec.requests)


# ---- varios adjuntos -------------------------------------------------------------------------------

async def test_multiple_attachments_keep_order_one_text_block_first(store):
    store.add(meta("f1", "a.png", "image/png", 1), b"I")
    store.add(meta("f2", "b.pdf", "application/pdf", 1), b"D")
    store.add(meta("f3", "c.csv", "text/csv", 1), b"x,y")
    out = await build(" hola ", [{"file_id": "f1"}, {"file_id": "f2"}, {"file_id": "f3"}])
    assert out == [
        {"text": "hola\n\n[Adjunto: a.png] (imagen incluida)\n\n[Adjunto: b.pdf] (documento incluido)"
                 "\n\n[Adjunto: c.csv]\nx,y"},
        {"image": {"format": "png", "source": {"bytes": b"I"}}},
        {"document": {"format": "pdf", "name": "b.pdf", "source": {"bytes": b"D"}}},
    ]


# ---- credencial (D-10) -----------------------------------------------------------------------------

async def test_user_jwt_travels_on_every_request_and_paths_are_the_files_routes(store):
    store.add(meta("f1", "a.png", "image/png", 1), b"I")
    store.add(meta("f2", "b.pdf", "application/pdf", 1))
    await build("x", [{"file_id": "f1"}, {"file_id": "f2"}])
    assert [(r.method, r.url.path) for r in store.rec.requests] == [
        ("GET", "/files/f1"), ("GET", "/files/f1/raw"), ("GET", "/files/f2"), ("GET", "/files/f2/raw"),
    ]
    assert {r.headers["authorization"] for r in store.rec.requests} == {f"Bearer {USER.token}"}


async def test_service_context_credential_is_also_honoured(store, attachments):
    store.add(meta("f1", "a.png", "image/png", 1), b"I")
    with service_scope(ServiceContext(token="svc-tok")):
        await attachments.build_user_content_blocks(Db(), "u1", "x", [{"file_id": "f1"}])
    assert {r.headers["authorization"] for r in store.rec.requests} == {"Bearer svc-tok"}


async def test_user_id_argument_is_not_sent_to_the_api(store, attachments):
    store.add(meta("f1", "a.png", "image/png", 1), b"I")
    with as_user():
        await attachments.build_user_content_blocks(Db(), "otro-usuario", "x", [{"file_id": "f1"}])
    assert all("otro-usuario" not in str(r.url) and not r.url.params for r in store.rec.requests)


async def test_download_request_for_the_signed_url_carries_the_user_jwt(store):
    store.add(meta("f1", "a.zip", "application/zip", 9))
    await build("x", [{"file_id": "f1"}])
    downloads = [r for r in store.rec.requests if r.url.path == "/files/f1/download"]
    assert len(downloads) == 1
    assert downloads[0].headers["authorization"] == f"Bearer {USER.token}"
