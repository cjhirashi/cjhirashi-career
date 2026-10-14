"""RF-022 / RF-001: servicio de memoria del agente (T-082). Sustituye a `local_memory` de la API.

Usa la fixture `pg_db` (Postgres desechable) y no dobles: lo que se valida es la composición
servicio + `memory_repo` (FTS `spanish_unaccent`) + `conversation_repo`, y el FTS necesita PG real.

Interfaz esperada de `services.memory_service` (a implementar en T-083), todas `async`, con
`db: AsyncSession` como primer argumento (mismos nombres que `local_memory.py` de la API, para
facilitar el traslado de `agent_loop`/`prompt`, T-085):
  MAX_LIMIT = 50                      # tope de `limit`/`top_k`/`max_results` (el de `top_k` de la ruta hoy: le=50)
  class MemoryServiceError(ValueError)  # texto vacío (equivale al `BedrockError` de la API)
  list_memory_events(db, user_id, session_id, max_results=50) -> list[dict]
      # [{"eventId": str, "eventTimestamp": iso|None,
      #   "payload": [{"conversational": {"role": "USER"|"ASSISTANT", "content": {"text": str}}}]}]
      # mensajes de `bedrock_conversation_messages`, orden cronológico; conversación ajena/inexistente -> []
  retrieve_memory_records(db, user_id, query, top_k=10) -> list[dict]
      # [{"memoryRecordId": "bam-N", "content": {"text": str}, "score": float,
      #   "namespaces": [kind, agent_profile_id or "global"], "createdAt": iso}]  (FTS, mejor primero)
  memory_source_ref(kind, text, profile_id=None) -> str      # PÚBLICA y síncrona (D-30); la usará también T-122
      # kind="note"   -> "note:<profile_id>:<h>"  (profile_id literal, obligatorio)
      # kind="manual" -> "manual:<h>"
      # h = primeros 40 hex de sha256(strip(text) sin NUL). Máximo 5+50+1+40 = 96 <= 100 (VARCHAR(100)).
      # Otro kind -> ValueError; kind="note" sin profile_id -> ValueError.
  create_manual_memory(db, user_id, text) -> dict | None
      # kind="manual", global, source_ref=memory_source_ref("manual", texto). IDEMPOTENTE (D-30): el mismo texto
      # (tras strip) del mismo usuario devuelve la fila existente (mismo id), sin error ni fila nueva.
      # Devuelve {"id", "text"} (la ruta responde igual {"status": "ok"}); vacío -> MemoryServiceError
  list_agent_notes(db, user_id, profile_id, limit=40) -> list[{"id": str, "text": str}]
      # solo kind="note" del perfil (no globales ni de otros perfiles)
  create_agent_note(db, user_id, profile_id, text) -> {"id": str, "text": str}   # text recortado; IDEMPOTENTE (D-30)
      # por (usuario, perfil, texto): reenvío -> el mismo id; otro perfil u otro usuario -> fila nueva
      # La dedup es por `source_ref` (no por `text`): una fila ya existente con esa clave (p. ej. importada
      # de Qdrant, source="qdrant_import") se devuelve. Carrera: si el INSERT lanza IntegrityError de
      # `uq_bedrock_agent_memory_user_source_ref`, se hace rollback y se devuelve la fila existente.
      # Las filas nuevas llevan source="harness", source_ref=memory_source_ref(...), kind "note"|"manual".
  delete_agent_note(db, user_id, note_id) -> bool            # solo la propia
Entrada: se recorta (`strip`) y se elimina el byte NUL (`\\x00`, que el driver rechaza con DBAPIError)
tanto en el texto como en la consulta. `limit` se acota a [1, MAX_LIMIT].
Frontera: no importa Qdrant ni embeddings.
"""
import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.requisito("RF-022")

SRC = Path(__file__).resolve().parents[3] / "src"


async def _msgs(pg_db, user_id, session_id, items):
    from repositories import conversation_repo as conv

    async with pg_db() as s:
        c = await conv.get_or_create_conversation(s, user_id, session_id, items[0][1])
        for role, content in items:
            await conv.append_message(s, c.id, role, content)


# ---- memory/events ----------------------------------------------------------------------------

@pytest.mark.requisito("RF-001")
async def test_events_desde_mensajes_con_forma_de_la_api(pg_db):
    from services import memory_service as svc

    await _msgs(pg_db, "usr-1", "s1", [("user", "hola"), ("assistant", "buenas")])
    async with pg_db() as s:
        ev = await svc.list_memory_events(s, "usr-1", "s1")
    assert [e["payload"][0]["conversational"] for e in ev] == [
        {"role": "USER", "content": {"text": "hola"}},
        {"role": "ASSISTANT", "content": {"text": "buenas"}},
    ]
    assert all(isinstance(e["eventId"], str) and e["eventId"] for e in ev)
    assert all(e["eventTimestamp"] for e in ev)
    assert set(ev[0]) == {"eventId", "eventTimestamp", "payload"}


@pytest.mark.requisito("RF-001")
async def test_events_aislados_por_usuario_e_inexistentes(pg_db):
    from services import memory_service as svc

    await _msgs(pg_db, "usr-1", "s1", [("user", "secreto")])
    async with pg_db() as s:
        assert await svc.list_memory_events(s, "usr-2", "s1") == []
        assert await svc.list_memory_events(s, "usr-1", "no-existe") == []


async def test_events_acota_max_results(pg_db):
    from services import memory_service as svc

    await _msgs(pg_db, "usr-1", "s1", [("user", f"m{i}") for i in range(60)])
    async with pg_db() as s:
        ev = await svc.list_memory_events(s, "usr-1", "s1")
        # los 50 MÁS ANTIGUOS, en orden cronológico (como la API)
        assert [e["payload"][0]["conversational"]["content"]["text"] for e in ev] == [f"m{i}" for i in range(50)]
        assert len(await svc.list_memory_events(s, "usr-1", "s1", max_results=5)) == 5
        assert len(await svc.list_memory_events(s, "usr-1", "s1", max_results=100000)) == svc.MAX_LIMIT
        assert len(await svc.list_memory_events(s, "usr-1", "s1", max_results=0)) == 1


# ---- memory/manual + memory/records -----------------------------------------------------------

@pytest.mark.requisito("RF-001")
async def test_manual_se_recupera_por_fts_con_forma_de_la_api(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        await svc.create_manual_memory(s, "usr-1", "  Prefiere vacantes remotas en fintech  ")
        recs = await svc.retrieve_memory_records(s, "usr-1", "vacante remota")
    assert len(recs) == 1
    r = recs[0]
    assert r["memoryRecordId"].startswith("bam-")
    assert r["content"] == {"text": "Prefiere vacantes remotas en fintech"}
    assert isinstance(r["score"], float) and r["score"] > 0
    assert r["namespaces"] == ["manual", "global"]
    assert r["createdAt"]


async def test_records_ignora_tildes_ordena_por_relevancia_y_aisla(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        await svc.create_manual_memory(s, "usr-1", "Trabajó en México")
        await svc.create_manual_memory(s, "usr-1", "México México México y más México")
        await svc.create_manual_memory(s, "usr-2", "Ajeno de Mexico")
        recs = await svc.retrieve_memory_records(s, "usr-1", "mexico")
    assert [r["content"]["text"] for r in recs] == ["México México México y más México", "Trabajó en México"]
    assert recs[0]["score"] > recs[1]["score"]
    assert all("Ajeno" not in r["content"]["text"] for r in recs)


async def test_records_incluye_notas_y_hechos_del_usuario(pg_db):
    from repositories import memory_repo
    from services import memory_service as svc

    async with pg_db() as s:
        await memory_repo.add_memory(s, "usr-1", "fact", "Habla francés", agent_profile_id="A")
        await svc.create_agent_note(s, "usr-1", "A", "Recordar francés avanzado")
        recs = await svc.retrieve_memory_records(s, "usr-1", "francés")
    assert {tuple(r["namespaces"]) for r in recs} == {("fact", "A"), ("note", "A")}


async def test_records_consulta_vacia_o_sin_coincidencias(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        await svc.create_manual_memory(s, "usr-1", "algo")
        assert await svc.retrieve_memory_records(s, "usr-1", "   ") == []
        assert await svc.retrieve_memory_records(s, "usr-1", "zzzinexistente") == []


async def test_records_acota_top_k(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        for i in range(60):
            await svc.create_manual_memory(s, "usr-1", f"dato común número {i}")
        assert len(await svc.retrieve_memory_records(s, "usr-1", "dato")) == 10
        assert len(await svc.retrieve_memory_records(s, "usr-1", "dato", top_k=100000)) == svc.MAX_LIMIT
        assert len(await svc.retrieve_memory_records(s, "usr-1", "dato", top_k=-3)) == 1


async def test_texto_vacio_se_rechaza(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        for bad in ("", "   \n", "\x00", " \x00 "):
            with pytest.raises(svc.MemoryServiceError):
                await svc.create_manual_memory(s, "usr-1", bad)
            with pytest.raises(svc.MemoryServiceError):
                await svc.create_agent_note(s, "usr-1", "A", bad)
        assert await svc.list_agent_notes(s, "usr-1", "A") == []


async def test_byte_nul_se_sanea_en_texto_y_consulta(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        await svc.create_manual_memory(s, "usr-1", "Sabe\x00 Python\x00")
        note = await svc.create_agent_note(s, "usr-1", "A", "nota\x00 con NUL")
        recs = await svc.retrieve_memory_records(s, "usr-1", "Pyt\x00hon")
    assert note["text"] == "nota con NUL"
    assert [r["content"]["text"] for r in recs] == ["Sabe Python"]
    async with pg_db() as s:
        assert await svc.retrieve_memory_records(s, "usr-1", "\x00 \x00") == []


# ---- notas del agente -------------------------------------------------------------------------

@pytest.mark.requisito("RF-001")
async def test_notas_crear_listar_borrar_con_forma_de_la_api(pg_db):
    from repositories import memory_repo
    from services import memory_service as svc

    async with pg_db() as s:
        n = await svc.create_agent_note(s, "usr-1", "A", "  El usuario odia las reuniones  ")
        assert set(n) == {"id", "text"} and n["text"] == "El usuario odia las reuniones"
        # no son notas del perfil A: otro perfil, global, otro kind, otro usuario
        await svc.create_agent_note(s, "usr-1", "B", "de B")
        await svc.create_manual_memory(s, "usr-1", "manual global")
        await memory_repo.add_memory(s, "usr-1", "fact", "hecho de A", agent_profile_id="A")
        await memory_repo.add_memory(s, "usr-1", "note", "nota global", )
        await svc.create_agent_note(s, "usr-2", "A", "de otro usuario")

        assert await svc.list_agent_notes(s, "usr-1", "A") == [n]

        assert await svc.delete_agent_note(s, "usr-2", n["id"]) is False  # ajena
        assert await svc.list_agent_notes(s, "usr-1", "A") == [n]
        assert await svc.delete_agent_note(s, "usr-1", n["id"]) is True
        assert await svc.delete_agent_note(s, "usr-1", n["id"]) is False
        assert await svc.list_agent_notes(s, "usr-1", "A") == []


async def test_notas_acota_limit_y_por_defecto_40(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        for i in range(60):
            await svc.create_agent_note(s, "usr-1", "A", f"nota {i}")
        assert len(await svc.list_agent_notes(s, "usr-1", "A")) == 40
        assert len(await svc.list_agent_notes(s, "usr-1", "A", limit=100000)) == svc.MAX_LIMIT
        assert len(await svc.list_agent_notes(s, "usr-1", "A", limit=3)) == 3


# ---- idempotencia (D-30) ----------------------------------------------------------------------

async def _count(pg_db):
    from sqlalchemy import func, select

    from models.bedrock_agent_memory import BedrockAgentMemory

    async with pg_db() as s:
        return (await s.execute(select(func.count()).select_from(BedrockAgentMemory))).scalar_one()


async def test_nota_repetida_no_duplica_y_devuelve_el_mismo_id(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        a = await svc.create_agent_note(s, "usr-1", "A", "Le gusta el café")
        b = await svc.create_agent_note(s, "usr-1", "A", "  Le gusta el café \n")
        c = await svc.create_agent_note(s, "usr-1", "A", "Le gus\x00ta el café")
        assert a == b == c
        assert await svc.list_agent_notes(s, "usr-1", "A") == [a]
    assert await _count(pg_db) == 1


async def test_misma_nota_en_perfiles_distintos_son_dos_filas(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        a = await svc.create_agent_note(s, "usr-1", "A", "mismo texto")
        b = await svc.create_agent_note(s, "usr-1", "B", "mismo texto")
    assert a["id"] != b["id"]
    assert await _count(pg_db) == 2


async def test_manual_repetida_no_duplica(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        a = await svc.create_manual_memory(s, "usr-1", "  Vive en Zapopan  ")
        b = await svc.create_manual_memory(s, "usr-1", "Vive en Zapopan")
        c = await svc.create_manual_memory(s, "usr-1", "Vive\x00 en Zapopan\x00 \n")
        assert set(a) == {"id", "text"} and a["text"] == "Vive en Zapopan"
        assert a == b == c
        assert len(await svc.retrieve_memory_records(s, "usr-1", "Zapopan")) == 1
    assert await _count(pg_db) == 1


async def test_mismo_texto_en_otro_usuario_es_otra_fila(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        await svc.create_manual_memory(s, "usr-1", "dato")
        await svc.create_manual_memory(s, "usr-2", "dato")
        a = await svc.create_agent_note(s, "usr-1", "A", "nota")
        b = await svc.create_agent_note(s, "usr-2", "A", "nota")
    assert a["id"] != b["id"]
    assert await _count(pg_db) == 4


def test_memory_source_ref_formato_exacto_y_determinista():
    import hashlib

    from services import memory_service as svc

    h = hashlib.sha256("hola".encode()).hexdigest()[:40]
    assert len(h) == 40
    assert svc.memory_source_ref("manual", "  hola ") == f"manual:{h}"
    assert svc.memory_source_ref("note", "hola\x00", profile_id="agent_support") == f"note:agent_support:{h}"
    assert re.fullmatch(r"manual:[0-9a-f]{40}", svc.memory_source_ref("manual", "x" * 10000))
    assert re.fullmatch(r"note:A:[0-9a-f]{40}", svc.memory_source_ref("note", "hola", "A"))
    assert svc.memory_source_ref("note", "hola", "A") == svc.memory_source_ref("note", "hola", "A")
    assert svc.memory_source_ref("note", "hola", "A") != svc.memory_source_ref("note", "hola", "B")
    assert svc.memory_source_ref("note", "hola", "A") != svc.memory_source_ref("note", "adios", "A")
    with pytest.raises(ValueError):
        svc.memory_source_ref("fact", "t")


def test_memory_source_ref_perfil_de_50_cabe_y_no_colisiona():
    from services import memory_service as svc

    with pytest.raises(ValueError):
        svc.memory_source_ref("note", "t")
    p1, p2 = "p" * 50, "p" * 49 + "q"
    r1, r2 = svc.memory_source_ref("note", "t", p1), svc.memory_source_ref("note", "t", p2)
    assert len(r1) == len(r2) == 96 <= 100
    assert r1.startswith(f"note:{p1}:") and r2.startswith(f"note:{p2}:")
    assert r1 != r2


async def test_nota_con_perfil_de_50_caracteres_se_guarda_y_deduplica(pg_db):
    from services import memory_service as svc

    prof = "p" * 50
    async with pg_db() as s:
        a = await svc.create_agent_note(s, "usr-1", prof, "texto")
        b = await svc.create_agent_note(s, "usr-1", prof, "texto")
    assert a == b and await _count(pg_db) == 1


async def _rows(pg_db):
    from sqlalchemy import select

    from models.bedrock_agent_memory import BedrockAgentMemory

    async with pg_db() as s:
        return list((await s.execute(select(BedrockAgentMemory).order_by(BedrockAgentMemory.id))).scalars())


async def test_fila_creada_lleva_source_ref_kind_perfil_y_source(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        n = await svc.create_agent_note(s, "usr-1", "A", "  una nota ")
        m = await svc.create_manual_memory(s, "usr-1", "un manual")
    rows = {r.id: r for r in await _rows(pg_db)}
    rn, rm = rows[n["id"]], rows[m["id"]]
    assert (rn.kind, rn.agent_profile_id, rn.source, rn.text) == ("note", "A", "harness", "una nota")
    assert rn.source_ref == svc.memory_source_ref("note", "una nota", "A")
    assert (rm.kind, rm.agent_profile_id, rm.source, rm.text) == ("manual", None, "harness", "un manual")
    assert rm.source_ref == svc.memory_source_ref("manual", "un manual")


async def test_dedup_contra_fila_importada_de_qdrant_devuelve_su_id(pg_db):
    from repositories import memory_repo
    from services import memory_service as svc

    async with pg_db() as s:
        nota = await memory_repo.add_memory(
            s, "usr-1", "note", "t", agent_profile_id="A", source="qdrant_import",
            source_ref=svc.memory_source_ref("note", "t", "A"))
        man = await memory_repo.add_memory(
            s, "usr-1", "manual", "m", agent_profile_id=None, source="qdrant_import",
            source_ref=svc.memory_source_ref("manual", "m"))
        a = await svc.create_agent_note(s, "usr-1", "A", " t ")
        b = await svc.create_manual_memory(s, "usr-1", "m")
    assert a["id"] == nota.id and b["id"] == man.id
    assert len(await _rows(pg_db)) == 2


async def test_nota_y_manual_con_el_mismo_texto_no_colisionan(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        n = await svc.create_agent_note(s, "usr-1", "A", "igual")
        m = await svc.create_manual_memory(s, "usr-1", "igual")
    assert n["id"] != m["id"]
    assert {r.kind for r in await _rows(pg_db)} == {"note", "manual"}


async def test_reenvio_concurrente_da_una_sola_fila_y_el_mismo_id(pg_db):
    import asyncio

    from services import memory_service as svc

    async def go():
        async with pg_db() as s:  # sesión propia por tarea
            return await svc.create_agent_note(s, "usr-1", "A", "carrera")

    res = await asyncio.gather(*[go() for _ in range(6)])
    assert all(r == res[0] for r in res)
    assert len(await _rows(pg_db)) == 1


async def test_carrera_integrity_error_devuelve_la_fila_existente(pg_db, monkeypatch):
    """Determinista: la fila rival se inserta tras el SELECT de existencia y antes del INSERT del servicio.
    Se envuelve `memory_repo.add_memory` (primera llamada) para que antes inserte la rival con otra sesión;
    el INSERT propio choca con la unicidad y el servicio debe devolver la existente."""
    from repositories import memory_repo
    from services import memory_service as svc

    real_add = memory_repo.add_memory
    state = {"done": False, "rival": None}

    async def add_con_rival(db, user_id, kind, text, **kw):
        if not state["done"]:
            state["done"] = True
            async with pg_db() as other:
                state["rival"] = await real_add(other, user_id, kind, text, **kw)
        return await real_add(db, user_id, kind, text, **kw)

    monkeypatch.setattr(memory_repo, "add_memory", add_con_rival)
    async with pg_db() as s:
        a = await svc.create_agent_note(s, "usr-1", "A", "carrera 2")
    assert a["id"] == state["rival"].id
    assert len(await _rows(pg_db)) == 1


@pytest.mark.requisito("RF-022")
async def test_delete_agent_note_solo_borra_kind_note(pg_db):
    from services import memory_service as svc

    async with pg_db() as s:
        m = await svc.create_manual_memory(s, "usr-1", "hola")
        n = await svc.create_agent_note(s, "usr-1", "A", "nota")
        assert await svc.delete_agent_note(s, "usr-1", m["id"]) is False
    assert m["id"] in {r.id for r in await _rows(pg_db)}
    async with pg_db() as s:
        assert await svc.delete_agent_note(s, "usr-1", n["id"]) is True


# ---- frontera ---------------------------------------------------------------------------------

def test_memory_service_no_importa_qdrant_ni_embeddings():
    path = SRC / "services" / "memory_service.py"
    assert path.is_file(), "falta src/services/memory_service.py"
    mods = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            mods.append(base)
            mods += [f"{base}.{a.name}" for a in node.names]
    banned = [m for m in mods if any(w in m.lower() for w in ("qdrant", "embedding"))]
    assert banned == []


def test_import_en_subproceso_no_carga_qdrant_ni_embeddings():
    """Complementa el AST (que no ve `importlib`/`__import__` ni nombres sin "qdrant"): importa el módulo
    en un intérprete limpio y revisa `sys.modules`."""
    import subprocess
    import sys

    code = (
        "import sys; sys.path.insert(0, %r); import services.memory_service; "
        "bad = sorted(m for m in sys.modules if 'qdrant' in m.lower() or 'embedding' in m.lower()); "
        "print('BAD:' + ','.join(bad)); sys.exit(1 if bad else 0)"
    ) % str(SRC)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-800:] + r.stdout[-300:]
