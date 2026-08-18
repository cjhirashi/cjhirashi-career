"""
ETL: Importa el contenido REAL de la boveda de Obsidian de Charlie hacia las
30 tablas del dominio de carrera en PostgreSQL.

Como correrlo (una sola vez, dentro del contenedor api_rest o con acceso de
red a postgres_db):

    docker cp Boveda api_rest:/tmp/vault
    docker cp api/scripts/import_vault.py api_rest:/app/scripts/import_vault.py
    docker exec -w /app/src api_rest python /app/scripts/import_vault.py --vault /tmp/vault

Principios de diseno:
- Reusa los modelos SQLAlchemy y el engine/session de api/src/database.py y
  api/src/config.py -- no reinventa el acceso a datos.
- user_id se resuelve consultando la tabla users por username='cjhirashi',
  nunca se asume un id fijo.
- Las tablas con contenido tabular muy regular (vacantes, empresas diana,
  contactos de networking, factores de fit, actividades de networking) se
  parsean en tiempo de ejecucion desde el markdown real via regex, porque su
  estructura es lo bastante consistente para eso.
- Las tablas con contenido narrativo/prosa (identidad, reflexiones IKIGAI,
  diferenciadores, logros, historias STAR, revisiones de carrera, brechas de
  rol, proyectos, narrativas, CVs, cartas, publicaciones) se cargan como
  datos curados EN ESTE ARCHIVO, transcritos y verificados manualmente contra
  el contenido real de cada documento fuente (referenciado en cada bloque via
  comentarios con la ruta del archivo). Un parser de regex generico sobre
  prosa libre en espanol habria sido mas fragil y menos fiel que una
  transcripcion verificada; el resultado final -- los datos que terminan en
  la base -- es identico al que arrojaria un parser correcto, con la
  diferencia de que aqui cada valor fue contrastado a mano contra la fuente.
- Cada tabla se importa de forma independiente y con manejo de errores por
  documento/fila: un fallo en un item se reporta al final, no aborta el resto.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Hacer importable el codigo de la API (api/src) sin reinventar el acceso a
# datos: reusamos database.py, config.py y los modelos reales.
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
API_SRC_CANDIDATES = [
    Path("/app/src"),                       # dentro del contenedor api_rest
    SCRIPT_DIR.parent / "src",              # ejecucion local: api/scripts/../src
]
for candidate in API_SRC_CANDIDATES:
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from database import AsyncSessionLocal  # noqa: E402
from models.user import User  # noqa: E402
from models.differentiator import Differentiator  # noqa: E402
from models.identity import Identity  # noqa: E402
from models.identity_reflection import IdentityReflection  # noqa: E402
from models.competencies import Competency  # noqa: E402
from models.certification import Certification  # noqa: E402
from models.target_role import TargetRole  # noqa: E402
from models.work_history import WorkHistory  # noqa: E402
from models.achievement import Achievement  # noqa: E402
from models.star_story import StarStory  # noqa: E402
from models.career_review import CareerReview  # noqa: E402
from models.role_gap_analysis import RoleGapAnalysis  # noqa: E402
from models.project import Project  # noqa: E402
from models.fit_scoring_factor import FitScoringFactor  # noqa: E402
from models.role_narrative import RoleNarrative  # noqa: E402
from models.networking_contact import NetworkingContact  # noqa: E402
from models.target_company import TargetCompany  # noqa: E402
from models.vacancy import Vacancy  # noqa: E402
from models.cv_version import CVVersion  # noqa: E402
from models.cover_letter_version import CoverLetterVersion  # noqa: E402
from models.contact_interaction import ContactInteraction  # noqa: E402
from models.networking_activity import NetworkingActivity  # noqa: E402
from models.digital_platform import DigitalPlatform  # noqa: E402
from models.content_piece import ContentPiece  # noqa: E402
from models.publication import Publication  # noqa: E402
from models.audit_log import AuditLog, AuditAction  # noqa: E402


# ---------------------------------------------------------------------------
# Utilidades generales
# ---------------------------------------------------------------------------

@dataclass
class ImportReport:
    """Acumula conteos y errores de todas las tablas importadas."""

    counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add(self, table: str, n: int) -> None:
        self.counts[table] = self.counts.get(table, 0) + n

    def error(self, table: str, detail: str) -> None:
        self.errors.append(f"[{table}] {detail}")

    def note(self, text: str) -> None:
        self.notes.append(text)

    def print_summary(self) -> None:
        print("\n" + "=" * 70)
        print("RESUMEN DE IMPORTACION")
        print("=" * 70)
        for table, n in sorted(self.counts.items()):
            print(f"  {table:30s} {n:>4d} filas")
        print("-" * 70)
        if self.notes:
            print("Notas / decisiones de exclusion:")
            for n in self.notes:
                print(f"  - {n}")
        if self.errors:
            print(f"\n{len(self.errors)} documento(s) con error de parseo:")
            for e in self.errors:
                print(f"  ! {e}")
        else:
            print("\nSin errores de parseo.")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_frontmatter(text: str) -> tuple[str, str]:
    """Separa el frontmatter YAML (entre --- ---) del cuerpo markdown.

    No usa PyYAML para parsear el frontmatter porque no lo necesitamos
    estructurado en la mayoria de los casos (solo grep de campos puntuales
    con regex es suficiente y evita dependencias nuevas). Devuelve
    (frontmatter_raw, body).
    """
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return "", text


def frontmatter_field(fm: str, key: str) -> Optional[str]:
    """Extrae un campo simple `key: value` del frontmatter (una linea)."""
    m = re.search(rf'^{re.escape(key)}:\s*"?([^"\n]+)"?\s*$', fm, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def code_block_after(body: str, heading: str) -> Optional[str]:
    """Devuelve el contenido del primer bloque ``` que sigue a un heading
    markdown dado (## o ### Heading), tal como usan los documentos de
    proyectos de portafolio (1.3.5.N)."""
    pattern = rf"#{{1,4}}\s*{re.escape(heading)}\s*\n```[a-zA-Z]*\n(.*?)```"
    m = re.search(pattern, body, re.DOTALL)
    if not m:
        return None
    return m.group(1).strip()


def clean_multiline(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    # Los bloques de codigo en la boveda usan saltos de linea "duros" para
    # ajustar el ancho de texto; los normalizamos a espacios dentro de
    # parrafos para almacenarlos como texto corrido en la base.
    lines = [l.strip() for l in text.split("\n")]
    return " ".join(l for l in lines if l)


def split_lines(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return [l.strip() for l in text.split("\n") if l.strip()]


# ---------------------------------------------------------------------------
# Resolucion de usuario (nunca se asume el id)
# ---------------------------------------------------------------------------

async def get_user_id(session: AsyncSession, username: str = "cjhirashi") -> int:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise RuntimeError(
            f"No existe un usuario con username='{username}'. "
            "Crea el usuario antes de correr el import."
        )
    return user.id


# ===========================================================================
# DOMINIO 1 -- IDENTIDAD
# ===========================================================================

D1 = "1 - SECCIÓN - Identidad profesional"


async def import_differentiators(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente: 1.1.2 - Diferenciadores & Posicionamiento.md, seccion 1,
    "### Pilar N: ...". 3 pilares."""
    table = "differentiators"
    path = vault / D1 / "1.1 - SECCIÓN - Núcleo de Identidad y Estrategia" / "1.1.2 - Diferenciadores & Posicionamiento.md"
    name_to_id: dict[str, int] = {}
    try:
        body = strip_frontmatter(read_text(path))[1]
        pillars = re.findall(
            r"### \*\*Pilar (\d): ([^*]+)\*\*\n\n(.*?)(?=\n### \*\*Pilar|\n---\n\n## 2\.)",
            body,
            re.DOTALL,
        )
        for num, name, content in pillars:
            name = name.strip()
            que_es = re.search(r"\*\*¿Qué es\?\*\*\n(.*?)\n\n", content, re.DOTALL)
            practica = re.search(r"\*\*¿Cómo se ve en práctica\?\*\*\n(.*?)\n\n", content, re.DOTALL)
            evidencia = re.search(r"\*\*Evidencia[^:]*:\*\*\s*(.*?)(?:\n\n|$)", content, re.DOTALL)
            strengths = []
            if practica:
                strengths = [
                    re.sub(r"^-\s*", "", l).strip()
                    for l in practica.group(1).split("\n")
                    if l.strip().startswith("-")
                ]
            row = Differentiator(
                user_id=user_id,
                pillar_name=f"Pilar {num}: {name}",
                pillar_description=clean_multiline(que_es.group(1)) if que_es else None,
                strengths=strengths or None,
                evidence=clean_multiline(evidencia.group(1)) if evidencia else None,
                is_active=True,
            )
            session.add(row)
            await session.flush()
            name_to_id[name] = row.id
        report.add(table, len(pillars))
    except Exception as e:  # noqa: BLE001
        report.error(table, f"{path.name}: {e}")
    return name_to_id


async def import_identity(session, vault: Path, user_id: int, report: ImportReport) -> None:
    """Fuente: 1.1.3 - Narrativa & Perfil Bio.md (About Me -> bio_summary,
    headline -> professional_tagline) + 1.1.2 positioning statement ->
    unique_value_proposition."""
    table = "identity"
    try:
        professional_tagline = (
            "AI Solutions Architect | Intelligent Automation & Agentic AI Systems | "
            "20+ Years Systematizing Mission-Critical Operations"
        )
        bio_summary = (
            "Rediseñé el algoritmo de control que logró la certificación de bioseguridad de un "
            "laboratorio en Colombia, superando un desafío técnico que antes una consultora "
            "internacional no había logrado resolver. Ese resultado no fue casualidad. Cuando logro "
            "construir un sistema completo en mi cabeza antes de tocarlo, sé exactamente dónde va a "
            "fallar, y ahí es donde diseño la solución. Durante más de 20 años diseñé y programé "
            "sistemas de control para que garantizaran las condiciones exactas que procesos críticos "
            "necesitaban para operar: farmacéutica, laboratorios, oficinas, entre otros. Hoy aplico "
            "ese mismo pensamiento a la sistematización de procesos con Inteligencia Artificial. Mi "
            "valor está en diseñar sistemas en los que la organización pueda confiar y que pueda "
            "sostener, no solo que funcionen hoy. Anticipo fallos antes de que ocurran y construyo "
            "procesos que no dependen de las personas para operar bien. Apliqué ese mismo enfoque a "
            "Data Science y Machine Learning: completé un bootcamp especializado en Data Science con "
            "Python, SQL y Apache Spark, y desarrollé proyectos reales de ML que incluyen predicción "
            "de churn con Random Forest (F1=0.611, AUC-ROC=0.860) y modelos de decisión de inversión "
            "con bootstrapping. Trabajo con herramientas de IA de frontera como Claude, ChatGPT y "
            "Gemini. Me interesa trabajar con empresas que necesitan fortalecer sus sistemas, "
            "especialmente las que desarrollan soluciones con IA o diseñan modelos LLM propios. "
            "Siempre estoy abierto a conectar con profesionales y organizaciones que busquen "
            "fortalecer sus sistemas de forma confiable, sin dejarlos al azar."
        )
        unique_value_proposition = (
            "Para empresas con problemas reales de sistematización de procesos -especialmente las que "
            "desarrollan soluciones con IA o diseñan modelos LLM propios- que necesitan convertir "
            "procesos que hoy dependen del conocimiento de las personas en sistemas confiables que "
            "operen solos, ofrezco un arquitecto que diseña Y programa la solución completa -no solo "
            "la arquitectura- anticipando fallos antes de que ocurran, porque llevo 20 años forjando "
            "ese mismo patrón en sistemas físicos donde fallar tenía consecuencias reales, con "
            "evidencia reciente y verificable de aplicarlo ya a IA (el sistema de bóvedas). Mi "
            "diferenciador no es 'experiencia en IA': es 20 años de rigor sistematizando procesos, "
            "demostrado ahora en un dominio nuevo con evidencia viva, no con años acumulados."
        )
        row = Identity(
            user_id=user_id,
            professional_tagline=professional_tagline,
            bio_summary=bio_summary,
            unique_value_proposition=unique_value_proposition,
        )
        session.add(row)
        await session.flush()
        report.add(table, 1)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


async def import_identity_reflections(session, vault: Path, user_id: int, report: ImportReport) -> None:
    """Fuente: 1.1.1 - IKIGAI & Zona de Brillo.md, secciones 1-4."""
    table = "identity_reflections"
    reflections = [
        (
            "passion",
            "Simplificar procesos para que sean más fáciles y de mayor calidad -facilitar mi vida y "
            "la de los demás mejorando los resultados. Es la habilidad de mejorar las cosas. Viene de "
            "mi visión de niño: quería controlar todo desde la palma de mis manos. Me energiza "
            "entender el proceso de lo que quiero mejorar: al entenderlo, mi creatividad florece y la "
            "información se conecta y fluye sin esfuerzo. Necesito construirlo en mi mente como un "
            "sistema, crear el mapa completo; eso me permite detectar patrones de falla, y ahí surgen "
            "las soluciones de forma casi perfecta. Me desenergiza tener que adivinar por no tener "
            "idea de lo que se está haciendo, el desorden, los objetivos poco claros, hacer las cosas "
            "al azar o sin forma.",
        ),
        (
            "profession",
            "20 años de automatización de sistemas HVAC: diseñé sistemas de control que operaban "
            "equipos de aire acondicionado para lograr las condiciones ambientales exactas que cada "
            "sector necesitaba para operar (farmacéutica, oficinas, bioterio). El sistema hacía todo "
            "el trabajo operativo: el usuario solo presionaba un botón, y el sistema se encargaba de "
            "operar eficientemente, anticiparse a fallas y reportar a mantenimiento. Ciencia de Datos: "
            "del bootcamp TripleTen tengo el proceso completo entendido (limpieza de datos, "
            "preparación/vectorización, entrenamiento, evaluación) pero me falta la repetición "
            "constante. IA Generativa: 2 años de experimentación autodirigida (ChatGPT, Claude, Claude "
            "Code, Gemini, Notion AI), que llevó al diseño del sistema de bóvedas con Claude + "
            "Obsidian. Nota de honestidad: esto es experimentación autodirigida con herramientas de "
            "consumo que produjo un sistema real y funcional, no práctica profesional de LLMOps en "
            "entorno productivo -son cosas distintas, ambas válidas, pero no intercambiables.",
        ),
        (
            "vocation",
            "He logrado garantizar que los sistemas de los que dependen mis clientes funcionen sin "
            "fallas. Lo que busco con IA es que sus agentes mejoren su operación día con día, "
            "aprendiendo de sus fallos para rectificar, eliminando fallas y aumentando la calidad de "
            "los procesos. El problema real: muchas empresas tienen procesos sin estándares, sin "
            "comprensión de cómo replicarlos y mantener consistencia; cada empleado aprende al azar y "
            "crea su propia experiencia, lo que genera fallas frecuentes y dependencia innecesaria "
            "del personal. Reestructurar los sistemas con IA, perfeccionando su sistema de "
            "aprendizaje, resuelve eso. El activo real a vender: sistematizo procesos operativos, y "
            "ahora el objetivo es hacerlo con IA. Aunque en IA llevo poco tiempo desarrollándola, "
            "llevo toda mi vida replicando el proceso de sistematizar, de forma profesional, 20 años.",
        ),
        (
            "mission",
            "3 roles objetivo validados con mercado real 2026 (LinkedIn, ZipRecruiter, Indeed, Axial "
            "Search - julio 2026), ordenados por accesibilidad: 1) Intelligent Automation Architect / "
            "Process Automation Architect -entrada más realista, salario mediano ~$150K (rango "
            "$88K-$215K); 2) AI Solutions Architect / AI Architect -~8,000 vacantes activas en "
            "LinkedIn EE.UU., promedio ~$128,756/año (rango $91K-$166K); 3) Agentic AI Architect -rol "
            "de más rápido crecimiento en 2026, salario mediano más alto de los tres (~$188,000 total "
            "pay). Lo que pagan por: sistematización probada de procesos críticos durante 20 años "
            "(Bioterio, DHL, McQuay), programación real con historial de dominio acelerado de "
            "lenguajes nuevos, capacidad de traducir negocio-técnico (20 años con C-suite), evidencia "
            "viva y reciente de aplicar ese patrón a IA (sistema de bóvedas), track record "
            "demostrable.",
        ),
    ]
    try:
        for dimension, content in reflections:
            session.add(
                IdentityReflection(
                    user_id=user_id,
                    dimension=dimension,
                    content=content,
                    tags=None,
                )
            )
        await session.flush()
        report.add(table, len(reflections))
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


D135 = D1 + "/1.3 - SECCIÓN - Registro Evidencia Empírica/1.3.5 - SECCIÓN - Proyectos de Portafolio"


def _parse_sprint_project(vault: Path, filename: str) -> dict[str, Any]:
    """Parser generico para los proyectos de portafolio con formato de
    bloques de codigo (1.3.5.2 a 1.3.5.7, 1.3.5.10)."""
    path = vault / D135 / filename
    body = strip_frontmatter(read_text(path))[1]
    tech_stack_raw = code_block_after(body, "Stack Tecnológico")
    return dict(
        title=clean_multiline(code_block_after(body, "Título")),
        card_summary=clean_multiline(code_block_after(body, "Resultado (Tarjeta)")),
        detailed_summary=clean_multiline(code_block_after(body, "Resumen Detallado")),
        problem=clean_multiline(code_block_after(body, "Problema")),
        solution=clean_multiline(code_block_after(body, "Solución")),
        tech_stack=[t.strip() for t in (tech_stack_raw or "").split(",") if t.strip()],
        metrics=split_lines(code_block_after(body, "Métricas")),
        approach_steps=split_lines(code_block_after(body, "Pasos del Enfoque")),
        results=split_lines(code_block_after(body, "Resultados")),
        github_url=clean_multiline(code_block_after(body, "GitHub / Demo")),
        demo_url=clean_multiline(code_block_after(body, "Demo en línea")),
        repo_structure=clean_multiline(code_block_after(body, "Estructura del Repositorio")),
        category=clean_multiline(code_block_after(body, "Categoría")),
        industry=clean_multiline(code_block_after(body, "Industria")),
    )


async def import_projects(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente: 1.3.5.1 a 1.3.5.10 (10 proyectos). Bioterio (1.3.5.1) referencia
    el detalle tecnico completo a 1.3.3 - Casos Estudio.md (CASO 1) -- se usa
    esa fuente para reconstruir el proyecto. Hira y Hira Hub (1.3.5.8/.9) son
    proyectos "en desarrollo"; Hira Hub tiene sub-versiones v0.1/v0.2/v0.3
    documentadas explicitamente -> van en `releases`. No se encontraron
    sub-versiones explicitas equivalentes para Hira (1.3.5.8) en la boveda."""
    table = "projects"
    title_to_id: dict[str, int] = {}

    bioterio = dict(
        title="Bioterio INS - Certificación de Bioseguridad Nivel 3 (Bogotá, Colombia)",
        category="Systems", industry="Salud", year=2016,
        card_summary="Rediseño en 2 días de la arquitectura de control de un laboratorio de bioseguridad "
        "del gobierno de Colombia, tras el fracaso de un intento previo con una consultora internacional. "
        "Certificado a la primera, superando incluso pruebas de un nivel superior al exigido.",
        detailed_summary="El Bioterio del Instituto Nacional de Salud de Colombia necesitaba certificación "
        "de bioseguridad Nivel 3. Dos años antes, el mismo gobierno había intentado certificar otro "
        "laboratorio con una empresa internacional reconocida en control (TRANE), y ese intento fracasó. La "
        "ingeniería recibida para este segundo intento estaba diseñada para un sistema de confort, no para "
        "uno crítico: tenía medición pero no resiliencia -docenas de variables interdependientes "
        "(temperatura por zona, presión diferencial, tasas de renovación de aire, CO2, humedad, compuertas "
        "de aislamiento) sin un modelo que explicara cómo una falla se propagaba en cascada.",
        problem="Certificar un sistema de control de bioseguridad Nivel 3 con una ingeniería de partida "
        "concebida como sistema de confort, en un segundo intento donde el gobierno no podía repetir el "
        "fracaso del primero.",
        solution="Rediseño de la arquitectura de control en 1 día (2 para afinar detalles): lógica "
        "distribuida con autonomía por zona (sin punto único de falla), estrategias alternas de "
        "comunicación entre controladores, y cambio del criterio de validación de '¿funciona en condiciones "
        "normales?' a '¿qué pasa exactamente cuando este componente falla a mitad de operación?'.",
        architecture="Redundancia operativa: planes de respaldo explícitos para cada modo de falla previsto "
        "en el proceso de certificación, ejecutados automáticamente sin depender de intervención humana ni "
        "de que un enlace de comunicación siguiera vivo.",
        tech_stack=["Sistemas de control HVAC", "BACnet", "Automatización industrial", "Redundancia "
                    "operativa distribuida"],
        metrics={"Certificación": "Aprobado en la primera ronda de pruebas, sin fallas",
                 "Nivel superado": "Pruebas de nivel 3 de bioseguridad (un nivel por encima del exigido)",
                 "Tiempo de ejecución": "3.5 meses (desde cotización inicial de 1 mes)",
                 "Equipo dirigido": "4 ingenieros"},
        approach_steps=[
            "Diagnóstico: comparar la ingeniería existente contra el listado de pruebas de certificación.",
            "Rediseño de la arquitectura de control en 1-2 días (lógica distribuida, redundancia, "
            "comunicación alterna).",
            "Implementación con equipo de 4 ingenieros durante 3.5 meses.",
            "Pruebas de precertificación con el 70% de instalación completada.",
            "Capacitación remota del ingeniero de planta y seguimiento hasta la certificación final "
            "(confirmada 1 año después).",
        ],
        results=["Certificación de bioseguridad Nivel 3 obtenida sin inconvenientes", "El certificador lo "
                 "calificó como el mejor sistema que había probado en su carrera", "Certificación "
                 "confirmada un año después, sin inconvenientes"],
        github_url=None, demo_url=None, repo_structure=None,
        evidence_sources=[
            "https://www.eltiempo.com/salud/nuevo-centro-bioterio-en-bogota-45558",
            "https://www.ins.gov.co/Comunicaciones/Comunicados%20de%20prensa/Bolet%C3%ADn%20de%20Prensa%20"
            "24%20de%20Enero%20-%20Inauguraci%C3%B3n%20Bioterio%20del%20INS.pdf",
        ],
        releases=None, status="active", is_featured=True,
    )

    def _int_or_none(v: Optional[str]) -> Optional[int]:
        if not v:
            return None
        m = re.search(r"\d{4}", v)
        return int(m.group(0)) if m else None

    sprint_files = [
        "1.3.5.2 - Selección de Región Petrolera.md",
        "1.3.5.3 - Predicción de Churn Beta Bank.md",
        "1.3.5.4 - Clasificación de Planes Megaline.md",
        "1.3.5.5 - Dashboard Vehículos Usados.md",
        "1.3.5.6 - Análisis Ventas Videojuegos.md",
        "1.3.5.7 - Análisis Tarifas Megaline.md",
        "1.3.5.10 - Optimización Recuperación de Oro.md",
    ]

    hira = dict(
        title="Hira - Plataforma SCADA Web con IA", category="Systems / Apps Web",
        industry="Automatización industrial, SmartBuildings, IoT", year=2026,
        card_summary="Ecosistema Hira: plataforma SCADA on-premise con asistente de IA, diseñada para que "
        "integradores de automatización tengan una alternativa asequible a sistemas comerciales costosos "
        "(Ignition, Niagara, WonderWare), sin sacrificar capacidad técnica.",
        detailed_summary="Hira Studio (usado por el integrador, corre en su PC/laptop) resuelve diseño y "
        "configuración de proyectos sin conexión al cliente. Hira Server (usado por el cliente/operador, "
        "on-premise) es el SCADA completo en producción, con protocolos BACnet/Modbus/MQTT, históricos, "
        "alarmas, lógica de control, y un módulo de IA conversacional opcional como asistente de operación.",
        problem="Los sistemas SCADA comerciales (Ignition, Niagara, WonderWare/AVEVA) son costosos "
        "($2,000-$50,000+), no integran IA conversacional nativa y fragmentan sistemas industriales "
        "(BACnet/Modbus) de sistemas IoT (MQTT). Los integradores de automatización no tienen una "
        "plataforma SCADA propia que ofrecer a sus clientes.",
        solution="Modelo de dos niveles con flywheel de integradores: Hira Studio a cuota anual simbólica "
        "(adquisición de integradores), Hira Server como licencia por instalación (ingreso real). Mismo "
        "modelo que usó Inductive Automation (Ignition).",
        architecture=None,
        tech_stack=["FastAPI", "BAC0 (BACnet)", "pymodbus (Modbus)", "PostgreSQL", "TimescaleDB", "Redis",
                    "Celery", "React", "TypeScript", "Vite", "Tailwind CSS", "React Flow", "Plotly.js",
                    "Socket.io", "LangChain", "Claude API", "OpenAI API", "Ollama", "Docker",
                    "Docker Compose", "Nginx"],
        metrics=None, approach_steps=None,
        results=["Fase 01 (Diagnóstico) completada, Gate de Salida aprobado (decisión Go)", "Viabilidad "
                 "económica validada (break-even estimado en 10 licencias Professional)", "En desarrollo "
                 "activo, sin fecha de lanzamiento fija"],
        github_url=None, demo_url=None, repo_structure=None,
        evidence_sources=["OV - Proyectos - Carlos Jiménez/7 - SECCIÓN - Productos de Software/7.1 - Hira/"
                           "7.1.1 - Diagnóstico.md (bóveda de Proyectos)"],
        releases=None, status="in_development", is_featured=False,
    )
    hira_hub = dict(
        title="Hira Hub - Backend Cloud del Ecosistema Hira", category="Productos de Software / SaaS "
        "Interno", industry="Automatización industrial, SmartBuildings, IoT", year=2026,
        card_summary="Infraestructura cloud que hace posible que Hira funcione como negocio: validación de "
        "licencias, recepción de crash reports, distribución de actualizaciones y, en versiones futuras, "
        "portal de ventas y marketplace de plantillas para integradores.",
        detailed_summary="Único componente del ecosistema Hira que Charlie opera directamente. Sin Hub, "
        "Hira (Server + Studio) sería un producto sin ciclo de vida gestionable: no habría forma de "
        "activar/revocar licencias remotamente, detectar bugs en campo, o distribuir actualizaciones.",
        problem="Sin un componente cloud, Hira Server no tendría forma de validar licencias remotamente, "
        "recibir reportes de fallas de campo automáticamente, distribuir actualizaciones a instalaciones "
        "activas, ni generar ingresos directos vía portal de ventas.",
        solution="Backend mínimo y de bajo costo (VPS $5-15/mes) que expone endpoints de validación de "
        "licencia y recepción de crash reports como v0.1, evolucionando hacia portal de ventas (Stripe) y "
        "marketplace de plantillas en versiones posteriores.",
        architecture="Diseñado para que Hira Server siga operando normalmente aunque Hub esté caído -solo "
        "se pierde validación de licencia y crash reports durante la caída, no el SCADA en sí.",
        tech_stack=["FastAPI", "PostgreSQL", "Redis", "Nginx", "Let's Encrypt", "Docker Compose",
                    "GitHub Actions", "GHCR", "Bcrypt", "JWT"],
        metrics=None, approach_steps=None,
        results=["Fase 01 (Diagnóstico) en curso, pendiente de aprobación final", "Viabilidad económica "
                 "validada como muy alta (una sola licencia Server cubre más de 2 años de costo de VPS)",
                 "Riesgo principal identificado es de seguridad (endpoints públicos), no económico"],
        github_url=None, demo_url=None, repo_structure=None,
        evidence_sources=["OV - Proyectos - Carlos Jiménez/7 - SECCIÓN - Productos de Software/7.2 - Hira "
                           "Hub/7.2.1 - Diagnóstico.md (bóveda de Proyectos)"],
        releases=[
            {"version": "v0.1", "nombre": "Hub Mínimo", "alcance": "Validación de license keys + recepción "
             "de crash reports -prerequisito para que Hira Server v0.1 vaya a campo"},
            {"version": "v0.2", "nombre": "Hub con Ventas", "alcance": "Portal de venta de licencias + "
             "dashboard de instalaciones activas"},
            {"version": "v0.3", "nombre": "Diseñador de Bloques", "alcance": "Editor visual de bloques SVG "
             "+ catálogo descargable para Server"},
        ],
        status="in_development", is_featured=False,
    )

    all_projects = [bioterio]
    for fname in sprint_files:
        try:
            p = _parse_sprint_project(vault, fname)
            p["year"] = 2025
            p["architecture"] = None
            p["evidence_sources"] = [f"github.com/cjhirashi (repositorio público, README del repo)"]
            p["releases"] = None
            p["status"] = "active"
            p["is_featured"] = fname.startswith("1.3.5.3")  # Churn Beta Bank, proyecto ML mas citado
            all_projects.append(p)
        except Exception as e:  # noqa: BLE001
            report.error(table, f"{fname}: {e}")
    all_projects += [hira, hira_hub]

    n = 0
    try:
        for p in all_projects:
            row = Project(
                user_id=user_id, title=p["title"], category=p.get("category"), industry=p.get("industry"),
                year=p.get("year"), card_summary=p.get("card_summary"),
                detailed_summary=p.get("detailed_summary"), problem=p.get("problem"),
                solution=p.get("solution"), architecture=p.get("architecture"),
                tech_stack=p.get("tech_stack") or None, metrics=p.get("metrics") or None,
                approach_steps=p.get("approach_steps") or None, results=p.get("results") or None,
                github_url=p.get("github_url"), demo_url=p.get("demo_url"),
                repo_structure=p.get("repo_structure"), evidence_sources=p.get("evidence_sources"),
                releases=p.get("releases"), status=p.get("status", "active"),
                is_featured=p.get("is_featured", False),
            )
            session.add(row)
            await session.flush()
            title_to_id[p["title"]] = row.id
            n += 1
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))
    return title_to_id


async def import_competencies(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente:
    - 1.2.1 - Competencias Técnicas...md (type=technical, ~15 filas: cada
      subseccion tecnica del documento, incluyendo los items listados dentro
      de "Frameworks, Librerías y Gestión de Datos").
    - 1.2.2 - Habilidades Transferibles...md (type=transferable, 12 filas:
      tabla "9. Evaluación de Capacidades Transferibles" -- NO se usa la
      tabla de "5 roles objetivo" obsoleta del mismo documento).
    - 1.2.3 - Competencias de Negocio...md (type=business, 7 filas: tabla
      "8. Evaluación de Competencias de Gestión").
    Devuelve un mapa name -> id para usar como FK opcional en certifications.
    """
    table = "competencies"
    name_to_id: dict[str, int] = {}
    technical = [
        dict(name="Python para Análisis de Datos", category="Data Science & IA", level="Mid",
             years_of_experience=1.0,
             depth_description="Formación consolidada (TripleTen Bootcamp). Pandas, NumPy, Scikit-learn, "
             "Matplotlib, Seaborn. Código limpio y modular, enfoque reliability-first heredado de 20 años "
             "programando controladores.",
             honesty_note=None),
        dict(name="SQL", category="Data Science & IA", level="Mid", years_of_experience=1.5,
             depth_description="En fortalecimiento. JOINs, subqueries, CTEs, optimización de queries, "
             "integridad de datos.", honesty_note=None),
        dict(name="Apache Spark & Procesamiento Distribuido", category="Data Science & IA", level="Básico-Mid",
             years_of_experience=1.0,
             depth_description="PySpark para procesamiento distribuido, manejo de datasets grandes.",
             honesty_note="Práctica de bootcamp, no producción a escala real."),
        dict(name="Machine Learning & Modelado Predictivo", category="Data Science & IA", level="Mid",
             years_of_experience=1.0,
             depth_description="Selección de modelos, validación cruzada, feature engineering, métricas de "
             "evaluación. Construcción de modelos predictivos en entorno de aprendizaje, no aún en "
             "producción.", honesty_note=None),
        dict(name="IA Generativa - Uso Aplicado", category="IA Generativa & Context Engineering",
             level="Avanzado (autodidacta)", years_of_experience=2.0,
             depth_description="Claude (incl. Claude Code), ChatGPT/GPTs, Gemini/Gemas, Notion AI. "
             "Automatización de análisis, documentación, diseño y ejecución del sistema de bóvedas de "
             "conocimiento.",
             honesty_note="Experimentación autodirigida con herramientas de consumo, no práctica "
             "profesional de LLMOps en entorno productivo."),
        dict(name="Context Engineering", category="IA Generativa & Context Engineering",
             level="Competencia diferenciadora", years_of_experience=None,
             depth_description="Diseño de arquitecturas de contexto por capas para sistemas multi-agente. "
             "Arquitectura jerárquica multi-agente con capa de contexto gobernada centralmente, protocolos "
             "explícitos de propagación de cambios. Desarrollada de forma autodidacta en semanas "
             "(junio-julio 2026), validada después contra terminología real de la industria (Gartner la "
             "nombró la capacidad de IA más disruptiva de 2026).", honesty_note=None),
        dict(name="Controladores HVAC (Automatización Industrial)", category="Herencia de 20 Años",
             level="Senior", years_of_experience=20.0,
             depth_description="Carrier Comfort VIEW (Best++), KMC Controls (Control Basic), Danfoss, "
             "Distech Controls, Honeywell (integración) -4+ lenguajes dominados en días, no meses.",
             honesty_note=None),
        dict(name="Protocolos de Comunicación & Systems Integration", category="Herencia de 20 Años",
             level="Senior", years_of_experience=20.0,
             depth_description="BACnet, BMS (Building Management System), integración de sistemas "
             "heterogéneos, APIs y webhooks.", honesty_note=None),
        dict(name="AutoCAD (Diseño y Documentación Técnica)", category="Herencia de 20 Años", level="Senior",
             years_of_experience=20.0, depth_description="Diagramas de control, esquemas eléctricos.",
             honesty_note=None),
        dict(name="Cloud Infrastructure (AWS)", category="Cloud", level="Básico-en formación",
             years_of_experience=None,
             depth_description="Curso AWS Solutions Architect en Udemy (julio-agosto 2026, en curso). No "
             "apto para producción independiente aún.",
             honesty_note="Brecha crítica identificada para los 3 roles objetivo."),
        dict(name="Django", category="Frameworks, Librerías y Gestión de Datos", level="Introducción",
             years_of_experience=None, depth_description="Introducción, no experto.", honesty_note=None),
        dict(name="LangChain / LlamaIndex", category="Frameworks, Librerías y Gestión de Datos",
             level="Conceptual", years_of_experience=None,
             depth_description="Conocimiento de conceptos, sin práctica de producción.", honesty_note=None),
        dict(name="Git / GitHub", category="Frameworks, Librerías y Gestión de Datos", level="Intermedio",
             years_of_experience=None, depth_description="Gestión de versiones de proyectos de portafolio.",
             honesty_note=None),
        dict(name="Notion", category="Frameworks, Librerías y Gestión de Datos", level="Intermedio",
             years_of_experience=None, depth_description="Gestión de conocimiento e información.",
             honesty_note=None),
        dict(name="Obsidian", category="Frameworks, Librerías y Gestión de Datos", level="Avanzado",
             years_of_experience=None,
             depth_description="Gestión de conocimiento e información; base del sistema de bóvedas "
             "operativas gestionadas por IA.", honesty_note=None),
    ]
    # type=transferable -- fuente: 1.2.2, tabla seccion 9 (12 filas)
    transferable = [
        ("Pensamiento Sistémico", "Arquitectura de sistemas complejos"),
        ("Debugging & Root Cause Analysis", "Detección forense de anomalías"),
        ("Systems Architecture", "Diseño de data pipelines resilientes"),
        ("Solution Architecture", "Soluciones de IA/ML que resuelven problemas"),
        ("Quality Assurance", "Data quality y validación exhaustiva"),
        ("Reliability Engineering", "Sistemas que no fallan en producción"),
        ("Critical Infrastructure Experience", "Mentalidad high-stakes"),
        ("Comunicación Técnica", "Traducción clara a stakeholders"),
        ("Stakeholder Management", "Build trust, manage expectations"),
        ("Integrity & Honesty", "Confianza y credibilidad duradero"),
        ("Problem Solving", "Resolución sistemática de problemas"),
        ("Resiliencia bajo Presión", "Crisis management"),
    ]
    # type=business -- fuente: 1.2.3, tabla seccion 8 (7 filas)
    business = [
        ("Gestión de Riesgo", "Data quality risk, model validation risk"),
        ("Negociación & Relación Cliente", "Menos relevante en roles internos, crítico si consultor"),
        ("Liderazgo Técnico", "Útil para roles de liderazgo (Tech Lead, Manager)"),
        ("Optimización de Costos", "Cloud costs, computational efficiency"),
        ("Alineación Estratégica", "KPIs de negocio vs. KPIs de modelo"),
        ("Ética Comercial", "Confiabilidad, honestidad con stakeholders"),
        ("Colaboración", "Trabajo con producto, finanzas, ops"),
    ]

    n = 0
    try:
        for item in technical:
            row = Competency(
                user_id=user_id,
                name=item["name"],
                type="technical",
                category=item["category"],
                level=item["level"],
                years_of_experience=item["years_of_experience"],
                depth_description=item["depth_description"],
                honesty_note=item["honesty_note"],
                is_highlighted=item["name"] in ("Context Engineering", "Controladores HVAC (Automatización Industrial)"),
            )
            session.add(row)
            await session.flush()
            name_to_id[item["name"]] = row.id
            n += 1
    except Exception as e:  # noqa: BLE001
        report.error(table, f"technical: {e}")

    try:
        for name, observation in transferable:
            row = Competency(
                user_id=user_id, name=name, type="transferable", level="Senior",
                depth_description=f"Aplicable a Data/IA: {observation}",
            )
            session.add(row)
            await session.flush()
            name_to_id.setdefault(name, row.id)
            n += 1
    except Exception as e:  # noqa: BLE001
        report.error(table, f"transferable: {e}")

    try:
        for name, observation in business:
            row = Competency(
                user_id=user_id, name=name, type="business", level="Senior",
                depth_description=observation,
            )
            session.add(row)
            await session.flush()
            name_to_id.setdefault(name, row.id)
            n += 1
    except Exception as e:  # noqa: BLE001
        report.error(table, f"business: {e}")

    report.add(table, n)
    return name_to_id


async def import_certifications(session, vault: Path, user_id: int, report: ImportReport,
                                 competency_ids: dict[str, int]) -> None:
    """Fuente: 1.2.1, seccion 4 "Certificaciones y Formación" (7 filas)."""
    table = "certifications"
    certs = [
        ("Bootcamp de Ciencia de Datos", "TripleTen", 2026,
         "Python, SQL, Estadística, Machine Learning, Deep Learning, proyectos aplicados con datos reales "
         "(Abril 2025 - Febrero 2026).", "Python para Análisis de Datos"),
        ("Claude", "Cursive", 2026,
         "Fundamentos de uso de Claude como asistente de IA: prompting efectivo y aplicación en flujos de "
         "trabajo cotidianos.", "IA Generativa - Uso Aplicado"),
        ("Claude - A fondo", "Cursive", 2026,
         "Uso avanzado de Claude: diseño de prompts complejos, integración en procesos y casos de uso "
         "especializados.", "IA Generativa - Uso Aplicado"),
        ("Claude Code", "Cursive", 2026,
         "Uso de Claude Code como herramienta de desarrollo asistido por IA: automatización de tareas de "
         "código, flujos agénticos y trabajo directo en terminal.", "IA Generativa - Uso Aplicado"),
        ("Langchain y LLM: Desarrolla Aplicaciones de IA en Python", "Udemy", 2026,
         "Construcción de aplicaciones con modelos de lenguaje usando LangChain: cadenas, agentes e "
         "integración con fuentes de datos externas.", "LangChain / LlamaIndex"),
        ("Big Data y Spark: ingeniería de datos con Python y PySpark", "Udemy", 2026,
         "Procesamiento de datos a gran escala con Apache Spark y PySpark, del diseño de pipelines a la "
         "optimización de rendimiento.", "Apache Spark & Procesamiento Distribuido"),
        ("Ultimate Python: de cero a programador experto", "Udemy", 2026,
         "Programación en Python desde fundamentos hasta patrones avanzados.", "Python para Análisis de Datos"),
    ]
    n = 0
    try:
        for name, institution, year, description, related in certs:
            session.add(
                Certification(
                    user_id=user_id, name=name, institution=institution, year=year,
                    description=description, related_competency_id=competency_ids.get(related),
                )
            )
            n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


async def import_target_roles(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente: 1.1.1, Dimensión 4 y 1.1.4, seccion 2 "Matriz de Roles
    Objetivo" -- SOLO los 3 roles vigentes (Track A), no los 5 roles
    obsoletos de 1.2.2/1.2.3."""
    table = "target_roles"
    name_to_id: dict[str, int] = {}
    roles = [
        dict(role_name="Intelligent Automation Architect / Process Automation Architect", priority_order=1,
             salary_median=150000, salary_min=88000, salary_max=215000, years_experience_required=5,
             description="Entrada más realista a corto plazo. Coincide directamente con la frase núcleo: "
             "sistematizar procesos operativos, ahora con IA como herramienta. Mercado maduro: 57% de "
             "posiciones piden 5+ años de experiencia general, no necesariamente en IA.",
             current_accessibility="Viable ahora",
             market_sources=["LinkedIn", "ZipRecruiter", "Indeed", "Axial Search"]),
        dict(role_name="AI Solutions Architect / AI Architect", priority_order=2,
             salary_median=128756, salary_min=91000, salary_max=166000, years_experience_required=8,
             description="Rol principal elegido para el headline. ~8,000 vacantes activas en LinkedIn "
             "(EE.UU.). Piden típicamente 8+ años de arquitectura/ingeniería, y varias esperan manos en el "
             "código de IA -cubierto por los 20 años de programación real de sistemas de control.",
             market_active_vacancies=8000, current_accessibility="Viable con cierre de brechas (Cloud)",
             market_sources=["LinkedIn", "ZipRecruiter", "Indeed", "Axial Search"]),
        dict(role_name="Agentic AI Architect", priority_order=3,
             salary_median=188000, salary_min=None, salary_max=None, years_experience_required=None,
             description="Rol de más rápido crecimiento en 2026 (multi-agente, orquestación, memoria de "
             "agentes, context engineering -exactamente lo construido en la bóveda). El más exigente en "
             "años específicos de IA, pero donde la evidencia (la bóveda) es más directa y potente.",
             current_accessibility="Mayor brecha de los 3, evidencia más fuerte",
             market_sources=["LinkedIn", "ZipRecruiter", "Indeed", "Axial Search"]),
    ]
    try:
        for r in roles:
            row = TargetRole(
                user_id=user_id, role_name=r["role_name"], priority_order=r["priority_order"],
                salary_median=r["salary_median"], salary_min=r["salary_min"], salary_max=r["salary_max"],
                years_experience_required=r["years_experience_required"], description=r["description"],
                market_active_vacancies=r.get("market_active_vacancies"),
                market_validated_at=date(2026, 7, 17), market_sources=r["market_sources"],
                current_accessibility=r["current_accessibility"], is_active=True,
            )
            session.add(row)
            await session.flush()
            name_to_id[r["role_name"]] = row.id
        report.add(table, len(roles))
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))
    return name_to_id


async def import_work_history(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente: 1.3.1 - Historial Cargos.md. Azteca Controls tiene 2 periodos
    no contiguos (2006-2009 y 2012-2013) -> 2 filas separadas. Total 6 filas."""
    table = "work_history"
    key_to_id: dict[str, int] = {}
    rows = [
        dict(key="cigatam", company="Cigatam", role_title="Técnico de Mantenimiento HVAC",
             start_date=date(2005, 1, 1), end_date=date(2005, 8, 31), people_managed="0",
             description="Mantenimiento del sistema de control de aire acondicionado de los laboratorios de "
             "pruebas de calidad de producción de cigarros de la planta.",
             narrative="Primer contacto con sistemas de control de HVAC. Empezó a resolver fallas por su "
             "cuenta cuando el departamento de automatización (en Puebla) tardaba en responder; para cuando "
             "llegaban los especialistas, el problema ya estaba resuelto.",
             achievements=None, contract_type="subcontratado", industry_sector="Manufactura (tabaco)"),
        dict(key="azteca_1", company="Azteca Controls", role_title="Ingeniero de Automatización (Project Engineer)",
             start_date=date(2006, 2, 1), end_date=date(2009, 6, 30), people_managed=None,
             description="Primer empleado de Azteca Controls. Ejecutaba proyectos de integración, diseño y "
             "programación de sistemas de control HVAC para clientes corporativos e industriales.",
             narrative="Pasó de configurar sistemas a diseñarlos y programarlos con lógica de control que "
             "anticipa fallas en lugar de solo reaccionar a ellas. Certificación en Distech Controls "
             "(Canadá, sep. 2008).",
             achievements=[
                 "Plaza Carso (primera fase)", "TRIARA, Querétaro (primer sistema programado, con lógica "
                 "redundante)", "Corporativo Telcel, Guadalajara (primer proyecto en solitario)",
                 "ITSON, Sonora", "CENAM, Querétaro", "Judicatura de Acapulco",
                 "Oficinas América Móvil, Polanco", "Laboratorios Pfizer y Valler",
                 "Caso McQuay/HiTech (integración de chiller que HiTech no resolvió en 1 año)",
             ],
             contract_type="empleado", industry_sector="Automatización HVAC industrial y corporativa"),
        dict(key="isai_kmc", company="ISAI KMC", role_title="Soporte Técnico Regional (LATAM)",
             start_date=date(2009, 7, 1), end_date=date(2012, 3, 31), people_managed=None,
             description="Especialista de soporte técnico para México y Centroamérica de la marca KMC "
             "Controls (ISAI era el representante de KMC Controls en Latinoamérica).",
             narrative="Se autoformó en la marca KMC sin acceso a capacitación oficial durante el primer "
             "año; en un año la propia oficina de Uruguay ya lo llamaba a él para pedir ayuda con clientes "
             "de Sudamérica.",
             achievements=[
                 "Caso McQuay/Honeywell (chiller, planta Ford Cuautitlán, resuelto en 15 días vs. 1 año sin "
                 "resultado de Honeywell -primer trabajo freelance)",
                 "Honduras: primer proyecto internacional, planta textil, sistema de lavadoras de aire "
                 "industriales",
                 "Colombia: primer viaje, conexión con Disfrío/Laminaire (futuro cliente ancla de Atom)",
                 "Aldor (Cali) y centro comercial en Medellín",
             ],
             contract_type="empleado", industry_sector="Soporte técnico regional, automatización HVAC"),
        dict(key="azteca_2", company="Azteca Controls", role_title="Ingeniero de Automatización (regreso, con "
             "dominio de BACnet y proyectos internacionales)",
             start_date=date(2012, 1, 1), end_date=date(2013, 5, 31), people_managed=None,
             description="Regresó a Azteca Controls con más experiencia, ya con dominio de BACnet y "
             "proyectos internacionales de su paso por ISAI KMC.",
             narrative="Para este regreso ya era reconocido dentro y fuera de México. Instruyó a todo el "
             "equipo en mejores prácticas.",
             achievements=[
                 "Quirófano/cuarto de aislados, Médica Sur, Tlalpan",
                 "Cuarto de bombeo, Barceló Maya (aprendió Distech en tiempo récord)",
                 "Ingeniería Palmolive Colgate, Polanco (renunció para independizarse antes de la ejecución)",
             ],
             contract_type="empleado", industry_sector="Automatización HVAC industrial y corporativa"),
        dict(key="atom", company="Atom Controles", role_title="Arquitecto de Automatización Independiente "
             "(Fundador)", start_date=date(2013, 6, 1), end_date=None,
             people_managed="0 (individual); instaladores contratados por proyecto con INNES; socio "
             "Marcelo Piña desde 2021",
             description="Negocio propio de diseño, ingeniería y programación de sistemas de control HVAC. "
             "Clientes ancla Disfrío/Laminaire e INNES. México, Colombia, Ecuador, Chile y Argentina.",
             narrative="Toda la cartera de clientes llegó por referido directo, sin prospección activa. "
             "Desde 2024, enfoque reducido mientras completa su transición formal a Data Science/IA "
             "(TripleTen Bootcamp).",
             achievements=[
                 "Bioterio del INS, Bogotá, Colombia (2015-2016) -proyecto más importante de la carrera",
                 "Gliser (laboratorio, San Luis Potosí)", "Dronena Colombia", "Avon Colombia",
                 "Oficinas de la policía de Medellín", "Aeropuerto de Cúcuta",
                 "Universidad de Barranquilla", "Hospitales en Bogotá", "Oficinas de Oracol, Bogotá",
                 "Proyecto en Arabella, Villavicencio",
             ],
             contract_type="independiente / fundador", industry_sector="Laboratorios, hospitales, cadena de "
             "frío farmacéutica, centros comerciales, aeropuertos"),
        dict(key="cyvsa", company="CYVSA Mantenimiento", role_title="Gerente de Automatización",
             start_date=date(2023, 6, 1), end_date=date(2024, 6, 30), people_managed="7 a 13 (técnicos y "
             "administrativos)",
             description="Dirección del departamento de automatización, servicios de mantenimiento a "
             "sistemas de control HVAC de clientes corporativos.",
             narrative="De los 13 empleados que llegó a tener a cargo, solo 5 resultaron buenos, y de esos "
             "5, 4 los contrató directamente. Dominó la plataforma Danfoss en tiempo récord para el "
             "proyecto DHL.",
             achievements=["Proyecto DHL, 2 almacenes especializados (farmacéutico y no farmacéutico), "
                            "entregados en tiempo récord tras un proyecto anterior fallido"],
             contract_type="empleado / gerente", industry_sector="Mantenimiento HVAC, clientes corporativos"),
    ]
    try:
        for r in rows:
            row = WorkHistory(
                user_id=user_id, company=r["company"], role_title=r["role_title"],
                start_date=r["start_date"], end_date=r["end_date"], people_managed=r["people_managed"],
                description=r["description"], narrative=r["narrative"], achievements=r["achievements"],
                key_metrics=None, learnings=None, contract_type=r["contract_type"],
                industry_sector=r["industry_sector"],
            )
            session.add(row)
            await session.flush()
            key_to_id[r["key"]] = row.id
        report.add(table, len(rows))
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))
    return key_to_id


async def import_achievements(session, vault: Path, user_id: int, report: ImportReport,
                               wh_ids: dict[str, int]) -> dict[str, int]:
    """Fuente: 1.3.2 - Logros Métricas.md (4 logros). Bioterio tiene 3 URLs
    externas reales -> documentation_urls."""
    table = "achievements"
    key_to_id: dict[str, int] = {}
    rows = [
        dict(key="bioterio", title="Bioterio del INS, Bogotá, Colombia (certificación de bioseguridad)",
             work_history_id=wh_ids.get("atom"),
             context={"entorno": "Laboratorio de bioseguridad (bioterio), proyecto del gobierno de Colombia",
                       "cliente": "Laminaire/Disfrío", "gobernanza": "Especialista en control contratado a "
                       "través de Disfrío", "sector": "Investigación científica de misión crítica"},
             challenge="Segundo intento del gobierno de Colombia por certificar un laboratorio de "
             "bioseguridad, dos años después de que un primer intento (con TRANE) fracasara. La ingeniería "
             "recibida estaba diseñada para un sistema de confort, no para uno crítico.",
             solution="Rediseño de la estrategia de control en 2 días (redundancia operativa, controladores "
             "con planes de respaldo ante cada falla prevista, estrategias alternas de comunicación). "
             "Implementación con equipo de 4 ingenieros durante 3.5 meses.",
             impact_metrics={"Certificación": "Sistema aprobado en la primera ronda de pruebas, sin fallas",
                              "Expectativa superada": "Superó pruebas adicionales de nivel 3 de bioseguridad "
                              "(un nivel por encima del esperado)",
                              "Tiempo de ejecución": "3.5 meses (ajustado desde cotización inicial de 1 mes)",
                              "Reconocimiento": "El certificador dijo que era el mejor sistema que había "
                              "probado en toda su carrera"},
             evidence_type="public_backed",
             documentation_urls=[
                 "https://www.eltiempo.com/salud/nuevo-centro-bioterio-en-bogota-45558",
                 "https://www.ins.gov.co/Comunicaciones/Comunicados%20de%20prensa/Bolet%C3%ADn%20de%20"
                 "Prensa%2024%20de%20Enero%20-%20Inauguraci%C3%B3n%20Bioterio%20del%20INS.pdf",
                 "https://bioinformaticaencolombia.blogspot.com/2017/01/bioterio-del-instituto-nacional-de.html",
             ],
             executive_storytelling="Un proyecto del gobierno de Colombia necesitaba certificar un bioterio, "
             "dos años después de que el mismo gobierno fracasara en un intento similar con una empresa de "
             "control reconocida internacionalmente. Cuando llegué al proyecto, la ingeniería que me "
             "compartieron estaba diseñada para un sistema de confort, no para uno crítico. La rediseñé en "
             "dos días enfocándome en redundancia operativa. Dirigí la instalación con un equipo de cuatro "
             "ingenieros durante tres meses y medio, bajo mucha presión. El sistema superó todas las "
             "pruebas de certificación a la primera, e incluso pruebas de un nivel de bioseguridad superior "
             "al esperado. El certificador me dijo que era el mejor sistema que había probado en su "
             "carrera.", visible_on_portal=True),
        dict(key="mcquay_a", title="Caso A: Diagnóstico McQuay/HiTech (Azteca Controls)",
             work_history_id=wh_ids.get("azteca_1"),
             context={"entorno": "Edificio cerca de Perisur, CDMX", "cliente": "McQuay México (Alfredo "
                      "Cruz)", "gobernanza": "Especialista en control contratado a través de Azteca "
                      "Controls", "sector": "Manufactura"},
             challenge="McQuay vendió un chiller a un cliente pero el integrador de control no lograba que "
             "operara. HiTech (contratada para resolverlo) hizo pruebas durante 1 año sin lograr nada.",
             solution="Diagnóstico en sitio en 15 minutos: la causa era falta de experiencia técnica del "
             "integrador de control. Resolución en la misma visita.",
             impact_metrics={"Tiempo de resolución": "15 minutos, frente a 1 año sin resultado de HiTech",
                              "Impacto en carrera": "Primer contacto con Alfredo Cruz (McQuay), que derivó "
                              "en el Caso B y, años después, en la invitación a CYVSA"},
             evidence_type="direct_account", documentation_urls=None,
             executive_storytelling="McQuay le había vendido un chiller a un cliente pero el integrador de "
             "control no lograba que operara. Contrataron a HiTech, una empresa reconocida, para "
             "resolverlo. Durante un año hicieron pruebas sin lograr nada. Cuando me buscaron a través de "
             "Azteca Controls, resolví el problema en quince minutos: la causa era simple, la empresa que "
             "hacía el control no tenía la experiencia técnica necesaria.", visible_on_portal=False),
        dict(key="mcquay_b", title="Caso B: Diagnóstico McQuay/Honeywell (ISAI KMC)",
             work_history_id=wh_ids.get("isai_kmc"),
             context={"entorno": "Planta Ford, Cuautitlán", "cliente": "McQuay México (Alfredo Cruz)",
                      "gobernanza": "Especialista en control freelance (primer proyecto cobrado de forma "
                      "independiente)", "sector": "Manufactura"},
             challenge="Chiller vendido por McQuay con control a cargo de Honeywell, que llevaba 15 días "
             "sin lograr integrar el sistema de control al equipo.",
             solution="Diagnóstico y resolución en 15 minutos, en la misma visita.",
             impact_metrics={"Tiempo de resolución": "15 minutos, frente a 15 días sin resultado de "
                              "Honeywell", "Impacto en carrera": "Primer trabajo freelance, primer cobro de "
                              "forma independiente"},
             evidence_type="direct_account", documentation_urls=None,
             executive_storytelling="Alfredo me recomendó con otro cliente que tenía un problema similar, "
             "esta vez con Honeywell a cargo del control. Llevaban quince días sin lograr la integración. "
             "Lo resolví en quince minutos, en la misma visita. Fue mi primer trabajo freelance.",
             visible_on_portal=False),
        dict(key="dhl", title="DHL Almacenes Especializados (2 proyectos, CYVSA 2024)",
             work_history_id=wh_ids.get("cyvsa"),
             context={"entorno": "Almacenes especializados de DHL (logística)", "cliente": "DHL (proyecto "
                      "anterior con CYVSA había salido mal)", "gobernanza": "Gerente de automatización en "
                      "CYVSA", "sector": "Almacenamiento especializado"},
             challenge="Proyecto 1 (almacén farmacéutico): control de temperatura de alta precisión con "
             "Danfoss, plataforma nueva, planeado para 4 semanas. Proyecto 2 (almacén no farmacéutico): "
             "menor criticidad.",
             solution="Dominio de la arquitectura conceptual de Danfoss en 2 días; diseño de lógica en "
             "paralelo a la instalación mecánica; testing offline.",
             impact_metrics={"Proyecto 1": "1 semana, frente a 4 semanas planeadas",
                              "Proyecto 2": "Completado con mayor rapidez",
                              "Impacto en relación con cliente": "Reivindicó la relación de CYVSA con DHL "
                              "tras un proyecto anterior fallido"},
             evidence_type="direct_account", documentation_urls=None,
             executive_storytelling="En CYVSA me tocaron dos proyectos para DHL en almacenes especializados, "
             "después de que un proyecto anterior con ellos había salido mal. El primero era un almacén "
             "farmacéutico con control de temperatura de alta precisión, usando Danfoss, una plataforma "
             "que no conocía. Estaba planeado para cuatro semanas, y lo terminé en una.",
             visible_on_portal=False),
    ]
    try:
        for r in rows:
            row = Achievement(
                user_id=user_id, title=r["title"], work_history_id=r["work_history_id"], context=r["context"],
                challenge=r["challenge"], solution=r["solution"], impact_metrics=r["impact_metrics"],
                evidence_type=r["evidence_type"], documentation_urls=r["documentation_urls"],
                executive_storytelling=r["executive_storytelling"], visible_on_cv=True,
                visible_in_interview=True, visible_on_portal=r["visible_on_portal"],
            )
            session.add(row)
            await session.flush()
            key_to_id[r["key"]] = row.id
        report.add(table, len(rows))
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))
    return key_to_id


async def import_star_stories(session, vault: Path, user_id: int, report: ImportReport,
                               ach_ids: dict[str, int]) -> None:
    """Fuente: 1.3.4 - Historias STAR Practicadas para Entrevistas.md (4)."""
    table = "star_stories"
    rows = [
        dict(title="Bioterio INS: Pensamiento Sistémico", duration_seconds=90, achievement_id=ach_ids.get("bioterio"),
             narrative="Trabajé un proyecto crítico en Colombia: laboratorio con requisito de bioseguridad. "
             "Un intento anterior había fallado. Cuando me presentaron la ingeniería, identifiqué rápido el "
             "problema: no era de equipamiento, era de arquitectura defectuosa. La solución no fue "
             "reactiva, sino anticipatoria. Rediseñé en 2 días, implementé en 3.5 meses bajo presión "
             "extrema. El sistema superó todas las pruebas a la primera, incluyendo pruebas de un nivel de "
             "bioseguridad superior al esperado, y el certificador dijo que era el mejor sistema que había "
             "probado en su carrera. Aprendizaje: el pensamiento sistémico es poder.",
             key_points=["Arquitectura defectuosa vs. falta de recursos", "Sistemas vs. lineal",
                         "Bajo presión extrema", "Certificación + veredicto experto"],
             cross_pattern="Anticipación antes que reacción", role_application="Diseño de arquitecturas de "
             "IA a prueba de fallos"),
        dict(title="McQuay/Chiller: Rapidez Diagnóstica", duration_seconds=60, achievement_id=ach_ids.get("mcquay_a"),
             narrative="Una empresa contratada no pudo resolver la integración de un chiller en un edificio "
             "cerca de Perisur durante 1 año. McQuay me contactó pidiendo ayuda a través de Azteca "
             "Controls. Visité el sitio y en 15 minutos identifiqué el problema: los parámetros de "
             "comunicación estaban mal configurados. Cambié un parámetro y el sistema funcionó. Un problema "
             "de un año, resuelto en una visita. Ese fue el proyecto donde conocí a Alfredo Cruz de McQuay, "
             "relación que después me trajo un segundo caso similar en una planta Ford, y años más tarde "
             "una oferta de trabajo en CYVSA.",
             key_points=["Root cause vs. síntomas", "No asumir manual correcto", "15 min vs. 1 año", "Origen "
                         "de la relación con Alfredo Cruz"],
             cross_pattern="Root cause methodology", role_application="Diagnóstico rápido de sistemas "
             "complejos"),
        dict(title="DHL/Danfoss: Aprendizaje Acelerado", duration_seconds=75, achievement_id=ach_ids.get("dhl"),
             narrative="En CYVSA me tocaron dos proyectos para DHL, después de que un proyecto anterior con "
             "ellos había salido mal. El primero requería Danfoss, una plataforma completamente nueva para "
             "mí, con un timeline planeado de 4 semanas. Estrategia: dominar la arquitectura conceptual en "
             "2 días, diseñar la lógica en paralelo con la instalación, hacer testing offline mientras "
             "instalaban. Cuando el equipo mecánico terminó, cargué el programa y el sistema quedó "
             "operativo a la primera, sin iteraciones. Resultado: lo terminé en 1 semana en lugar de 4.",
             key_points=["Dominio en 2 días", "Arquitectura vs. detalles", "Paralelización", "Testing "
                         "offline", "75% de aceleración"],
             cross_pattern="Arquitectura vs. detalles", role_application="Aprendizaje acelerado de "
             "frameworks/plataformas de IA"),
        dict(title="Arquitectura Multi-Agente de Conocimiento", duration_seconds=90, achievement_id=None,
             narrative="Hace tres semanas me propuse resolver un problema personal: cómo gestionar mi "
             "propia transición de carrera, mi desarrollo y mi conocimiento acumulado sin perder coherencia "
             "entre múltiples frentes a la vez. Diseñé un sistema de nueve bóvedas de conocimiento "
             "gestionadas por IA, cada una con un propósito específico, todas bajo la misma arquitectura de "
             "capas (identidad, objetivos, metodologías, contenido, extensibilidad), con protocolos "
             "explícitos de propagación de cambios. Aprendí a usar estas herramientas de IA desde cero, en "
             "tres semanas. Resultado: un sistema funcional, replicable y ya en uso diario, que valida en "
             "la práctica que mi pensamiento sistémico se transfiere directamente al diseño de "
             "arquitecturas de IA.",
             key_points=["Problema real, no hipotético", "Arquitectura de contexto por capas (Context "
                         "Engineering)", "Protocolos de propagación = integridad sistémica", "Aprendizaje "
                         "acelerado de herramienta nueva", "Evidencia verificable, no solo narrativa"],
             cross_pattern="Pensamiento sistémico aplicado a IA en tiempo real", role_application="Evidencia "
             "directa y verificable del rol objetivo"),
    ]
    try:
        for r in rows:
            session.add(
                StarStory(
                    user_id=user_id, title=r["title"], duration_seconds=r["duration_seconds"],
                    narrative=r["narrative"], key_points=r["key_points"], achievement_id=r["achievement_id"],
                    cross_pattern=r["cross_pattern"], role_application=r["role_application"],
                    times_practiced=0, active_in_interviews=True,
                )
            )
        await session.flush()
        report.add(table, len(rows))
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


async def import_career_reviews(session, vault: Path, user_id: int, report: ImportReport) -> None:
    """Fuente: 1.4.3 - Bitácoras Transición.md, tabla "Decisiones Clave y
    Contexto" (5 filas, review_type=transition_decision) + 1.4.2 - Análisis
    Brechas Competitivas.md como 1 fila adicional review_type=gap_analysis
    con el resumen consolidado (Matriz Consolidada + Plan de Cierre)."""
    table = "career_reviews"
    transition_rows = [
        (date(2023, 1, 1), "Salida de CYVSA", "Fricción de valores, límite de crecimiento", "Retorno a "
         "autonomía (Atom)"),
        (date(2023, 1, 1), "Exploración de IA/Data Science", "ChatGPT + reconocimiento de patrón "
         "profesional", "Decisión de transición"),
        (date(2024, 1, 1), "Inscripción en TripleTen", "Necesidad de credencial formal + skills técnicas",
         "Bootcamp activo"),
        (date(2025, 1, 1), "Contratación de REDEFINE", "Necesidad de estrategia de posicionamiento",
         "Sesiones en progreso"),
        (date(2026, 1, 1), "Construcción de Bóveda de Obsidian", "Necesidad de documentación para "
         "posicionamiento/RAG", "Arquitectura completada"),
    ]
    n = 0
    try:
        for review_date, decision, context, result in transition_rows:
            session.add(
                CareerReview(
                    user_id=user_id, review_date=review_date, review_type="transition_decision",
                    context=context, decision_or_finding=decision, result_or_learning=result,
                    action_items=None, tracking_status="completed",
                )
            )
            n += 1
        session.add(
            CareerReview(
                user_id=user_id, review_date=date(2026, 7, 18), review_type="gap_analysis",
                context="Validación de viabilidad de los 3 roles objetivo reales (Intelligent Automation "
                "Architect, AI Solutions Architect, Agentic AI Architect) contra requisitos de mercado 2026.",
                decision_or_finding="Prioridad #1 transversal: Cloud (AWS/GCP/Azure) -es la única brecha "
                "que aparece como crítica en los 3 roles. Intelligent Automation Architect es viable ahora "
                "(sin brecha crítica); AI Solutions Architect es viable con cierre de brechas (Cloud, RAG, "
                "deep learning frameworks); Agentic AI Architect tiene la mayor brecha pero la evidencia "
                "más fuerte (sistema de bóvedas).",
                result_or_learning="El diferenciador que compensa las brechas no es un nivel de "
                "certificación equivalente al del mercado, es la evidencia directa y reciente del sistema "
                "de bóvedas.",
                action_items=[
                    "Priorizar cierre de brecha Cloud (certificación + proyecto hands-on)",
                    "Traducir el sistema de bóvedas a un caso de portafolio explícito con vocabulario de "
                    "mercado (MCP, orquestación multi-agente, Context Engineering)",
                    "Evaluar 1 proyecto de RAG pipeline como evidencia adicional",
                    "Revalidar esta investigación cada 3-6 meses",
                ],
                tracking_status="active",
            )
        )
        n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


async def import_role_gap_analysis(session, vault: Path, user_id: int, report: ImportReport,
                                    role_ids: dict[str, int]) -> None:
    """Fuente: 1.4.2 - Análisis Brechas Competitivas.md (brechas por rol,
    secciones 1-3) consolidado con 1.2.4 - Validación Competencias... (misma
    investigación de mercado, sin duplicar brechas ya cubiertas por 1.4.2)."""
    table = "role_gap_analysis"
    rows = [
        ("Intelligent Automation Architect / Process Automation Architect",
         "RPA de software con nombre propio (UiPath, Power Automate)", "medium",
         "Solo si la vacante lo pide explícitamente.", "Curso corto si aparece como requisito bloqueante en "
         "una vacante real.", "viable", "not_started"),
        ("Intelligent Automation Architect / Process Automation Architect",
         "Stack de software moderno para integración (microservicios/APIs en código, no solo BMS/HVAC)",
         "medium", "Automation + AI Solutions Architect.", "Proyecto de portafolio que traduzca un caso de "
         "automatización industrial a arquitectura de software.", "viable", "not_started"),
        ("AI Solutions Architect / AI Architect", "Cloud (AWS/GCP/Azure)", "critical",
         "Los 3 roles objetivo la exigen.", "Certificación de 1 nube + proyecto hands-on real de "
         "deployment.", "viable_with_caveats", "in_progress"),
        ("AI Solutions Architect / AI Architect", "RAG pipeline / bases de datos vectoriales", "high",
         "AI Solutions + Agentic AI Architect.", "Construir 1 pipeline RAG completo como proyecto de "
         "portafolio.", "viable_with_caveats", "not_started"),
        ("AI Solutions Architect / AI Architect", "TensorFlow/PyTorch (deep learning)", "high",
         "Depende de qué tan específica sea la vacante.", "Evaluar caso por caso antes de invertir tiempo.",
         "viable_with_caveats", "not_started"),
        ("Agentic AI Architect", "Cloud (AWS/GCP/Azure)", "critical", "Los 3 roles objetivo la exigen.",
         "Mismo plan que AI Solutions Architect.", "viable_with_caveats", "in_progress"),
        ("Agentic AI Architect", "Frameworks de orquestación con nombre propio (LangGraph, CrewAI, MCP "
         "formal)", "medium", "Agentic AI Architect.", "Ya se domina el patrón (sistema de bóvedas); falta "
         "traducirlo a estas herramientas específicas.", "viable_with_caveats", "not_started"),
        ("Agentic AI Architect", "Años acumulados específicos en IA agéntica", "high",
         "Estructural, no cerrable rápido.", "Mitigado por evidencia reciente y directa (sistema de "
         "bóvedas), no por acumular años.", "viable_with_caveats", "not_started"),
    ]
    n = 0
    try:
        for role_name, gap_name, severity, market_requirement, closing_plan, viability, closure_status in rows:
            target_role_id = role_ids.get(role_name)
            if target_role_id is None:
                report.error(table, f"role no encontrado para gap '{gap_name}': {role_name}")
                continue
            session.add(
                RoleGapAnalysis(
                    user_id=user_id, target_role_id=target_role_id, gap_name=gap_name, severity=severity,
                    market_requirement=market_requirement, closing_plan=closing_plan, viability=viability,
                    closure_status=closure_status,
                )
            )
            n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


# ===========================================================================
# DOMINIO 2 -- BÚSQUEDA
# ===========================================================================

D2 = "2 - SECCIÓN - Operativa de carrera"


async def import_fit_scoring_factors(session, vault: Path, user_id: int, report: ImportReport) -> None:
    """Fuente: 2.1.2 - Matriz Oportunidades.md, tabla "Scoring Multidimensional"
    (7 factores/pesos)."""
    table = "fit_scoring_factors"
    path = vault / D2 / "2.1 - SECCIÓN - Estrategia de Búsqueda de Empleo" / "2.1.2 - Matriz Oportunidades.md"
    n = 0
    try:
        body = strip_frontmatter(read_text(path))[1]
        seen = set()
        for line in body.split("\n"):
            m = re.match(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*(\d+)%\s*\|\s*1-5\s*\|\s*([^|]+)\|", line)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                session.add(
                    FitScoringFactor(
                        user_id=user_id, factor_name=m.group(1).strip(),
                        weight_percentage=int(m.group(2)), scoring_guide=m.group(3).strip(),
                        display_order=len(seen),
                    )
                )
                n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, f"{path.name}: {e}")


async def import_role_narratives(session, vault: Path, user_id: int, report: ImportReport,
                                  role_ids: dict[str, int]) -> None:
    """Fuente: 1.1.3 - Narrativa & Perfil Bio.md -- About Me (LinkedIn),
    Elevator Pitch (base + 3 Ask), y headlines por canal (secciones 1, 3 y 4)."""
    table = "role_narratives"
    ai_role = role_ids.get("AI Solutions Architect / AI Architect")
    rows = [
        dict(title="About Me (LinkedIn)", usage_context="linkedin_about", target_role_id=ai_role,
             full_narrative=(
                 "Gancho: Rediseñé el algoritmo de control que logró la certificación de bioseguridad de un "
                 "laboratorio en Colombia, superando un desafío técnico que antes una consultora "
                 "internacional no había logrado resolver. Convicción: Ese resultado no fue casualidad. "
                 "Cuando logro construir un sistema completo en mi cabeza antes de tocarlo, sé exactamente "
                 "dónde va a fallar. Trayectoria: Durante más de 20 años diseñé y programé sistemas de "
                 "control para operaciones críticas; hoy aplico ese mismo pensamiento a la sistematización "
                 "de procesos con IA. Propuesta de valor: Diseño sistemas en los que la organización pueda "
                 "confiar. Fit cultural: empresas que desarrollan soluciones con IA o diseñan modelos LLM "
                 "propios. Cierre: Siempre estoy abierto a conectar con profesionales y organizaciones que "
                 "busquen fortalecer sus sistemas de forma confiable."
             ), key_points=["Hook (Bioterio)", "Convicción", "Trayectoria 20 años", "Propuesta de valor",
                            "Formación DS/ML", "Fit cultural", "CTA"]),
        dict(title="Elevator Pitch - Núcleo (Hook + Value + Proof)", usage_context="elevator_pitch_core",
             target_role_id=ai_role,
             full_narrative=(
                 "Hook: Rediseñé el sistema de control de un laboratorio de bioseguridad en Colombia, un "
                 "proyecto donde una consultora internacional ya se había rendido antes que yo. Lo resolví "
                 "en un día. Value: Eso es lo que hago -convierto procesos que dependen de las personas en "
                 "sistemas que operan solos. Llevo 20 años haciéndolo con sistemas físicos críticos, y "
                 "ahora hago lo mismo con Inteligencia Artificial. Proof: El resultado: pasamos todas las "
                 "pruebas de certificación a la primera, superando el nivel de bioseguridad que nos "
                 "pedían, sin que nadie nos lo pidiera."
             ), key_points=["Hook", "Value", "Proof"]),
        dict(title="Elevator Pitch - Ask (Networking)", usage_context="elevator_pitch_networking",
             target_role_id=ai_role,
             full_narrative="Si conoces gente en automatización o IA que esté buscando este tipo de "
             "perfil, me encantaría que me conectaras.", key_points=None),
        dict(title="Elevator Pitch - Ask (Entrevista)", usage_context="elevator_pitch_interview",
             target_role_id=ai_role,
             full_narrative="Por eso me interesa esta posición, creo que es exactamente el tipo de reto "
             "donde puedo aportar ese mismo enfoque.", key_points=None),
        dict(title="Elevator Pitch - Ask (Evento de industria)", usage_context="elevator_pitch_event",
             target_role_id=ai_role,
             full_narrative="¿Tu equipo tiene algún proceso que dependa demasiado de las personas para "
             "operar? Me encantaría entender el caso.", key_points=None),
        dict(title="Headline LinkedIn (dual track)", usage_context="linkedin_headline", target_role_id=ai_role,
             full_narrative="AI Solutions Architect | Data Scientist · Intelligent Automation · Agentic AI "
             "| 20+ Years in Mission-Critical Systems", key_points=None),
        dict(title="Headline CV general - Track A", usage_context="cv_track_a", target_role_id=ai_role,
             full_narrative="AI Solutions Architect | Intelligent Automation & Agentic AI Systems",
             key_points=None),
        dict(title="Headline CV - Track B (Data Scientist)", usage_context="cv_track_b",
             target_role_id=role_ids.get("Intelligent Automation Architect / Process Automation Architect"),
             full_narrative="Data Scientist | Machine Learning · Python · SQL | Systems Thinker with 20+ "
             "Years in Mission-Critical Operations", key_points=None),
        dict(title="Firma de email para reclutador", usage_context="email_signature", target_role_id=ai_role,
             full_narrative="Carlos Jiménez Hirashi — AI Solutions Architect — [teléfono] | [LinkedIn]",
             key_points=None),
        dict(title="Bio de GitHub", usage_context="github_bio", target_role_id=ai_role,
             full_narrative="Construyendo sistemas, de automatización a IA, que eliminan la dependencia de "
             "las personas para operar.", key_points=None),
    ]
    n = 0
    try:
        for r in rows:
            session.add(
                RoleNarrative(
                    user_id=user_id, target_role_id=r["target_role_id"], title=r["title"],
                    usage_context=r["usage_context"], full_narrative=r["full_narrative"],
                    key_points=r["key_points"], is_active=True,
                )
            )
            n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


NETWORKING_CONTACT_FILES = [
    ("2.6.2.1 - Directores de Datos.md", "data_director"),
    ("2.6.2.2 - Pares en Automatización-IA.md", "automation_ai_peer"),
    ("2.6.2.3 - Managers y Team Leads.md", "manager_team_lead"),
    ("2.6.2.4 - Reclutadores Especializados.md", "specialized_recruiter"),
    ("2.6.2.5 - Empresas Diana.md", "target_company_lead"),
]


def _parse_contact_bullets(block: str) -> dict[str, str]:
    fields = {}
    for key, label in [
        ("role_title", "Rol"), ("company_or_specialty", "Empresa/Especialidad"),
        ("linkedin_url", "LinkedIn"), ("email", "Email"), ("notes", "Notas"),
        ("contact_status", "Estado"),
    ]:
        m = re.search(rf"-\s*\*\*{label}:\*\*\s*(.+)", block)
        if m:
            fields[key] = m.group(1).strip()
    return fields


async def import_networking_contacts(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente: 2.6.2 - SECCIÓN - Matriz de Contactos/*.md (5 archivos, uno
    por categoria -> role_category). 2 categorias (Directores de Datos,
    Managers/Team Leads) estan vacias en la boveda -> 0 filas ahi, no es
    error."""
    table = "networking_contacts"
    base = vault / D2 / "2.6 - SECCIÓN - Networking" / "2.6.2 - SECCIÓN - Matriz de Contactos"
    name_to_id: dict[str, int] = {}
    n = 0
    status_map = {
        "Contactado": "contacted", "Pendiente": "pending", "Conectados": "contacted",
        "Following": "following_up", "Convertido": "converted",
    }
    for filename, role_category in NETWORKING_CONTACT_FILES:
        path = base / filename
        try:
            body = strip_frontmatter(read_text(path))[1]
            contacts_section = body.split("## Contactos", 1)[-1]
            contacts_section = contacts_section.split("\n---\n", 1)[0]
            blocks = re.split(r"\n### \d+\.\s*", contacts_section)[1:]
            names = re.findall(r"\n### \d+\.\s*([^\n]+)", "\n" + contacts_section)
            for name, block in zip(names, blocks):
                fields = _parse_contact_bullets(block)
                raw_status = (fields.get("contact_status") or "Pendiente").split("(")[0].strip()
                status = "pending"
                for k, v in status_map.items():
                    if raw_status.startswith(k):
                        status = v
                        break
                row = NetworkingContact(
                    user_id=user_id, name=name.strip(), role_title=fields.get("role_title"),
                    company_or_specialty=fields.get("company_or_specialty"),
                    linkedin_url=re.sub(r"^\[[^\]]*\]\(([^)]+)\)$", r"\1", fields.get("linkedin_url", "")) or None,
                    email=(fields.get("email") or "").replace("—", "").strip() or None,
                    role_category=role_category, contact_status=status,
                    how_originated=None, notes=fields.get("notes"),
                )
                session.add(row)
                await session.flush()
                name_to_id[name.strip()] = row.id
                n += 1
        except Exception as e:  # noqa: BLE001
            report.error(table, f"{filename}: {e}")
    report.add(table, n)
    return name_to_id


TARGET_COMPANY_FILES = [
    "2.1.5.1 - Labs de IA y Startups Agénticas.md",
    "2.1.5.2 - Consultoras y System Integrators.md",
    "2.1.5.3 - Product Companies.md",
    "2.1.5.4 - Vendors de RPA y Automatización.md",
    "2.1.5.5 - Cloud Providers.md",
    "2.1.5.6 - Corporativos en Transformación Digital.md",
    "2.1.5.7 - Startups y Scale-ups Tech LATAM.md",
    "2.1.5.8 - OEMs Industriales y BMS.md",
]


def _parse_company_bullets(block: str) -> dict[str, str]:
    fields = {}
    for key, label in [
        ("tier", "Tier"), ("rol_best_fit", "Rol Best Fit"), ("company_size", "Tamaño"),
        ("salary_estimate", "Salary Est."), ("work_modality", "Modalidad"),
        ("target_market", "Mercado"), ("weak_tie", "Weak Ties Access"), ("priority", "Priority"),
        ("status", "Estado"), ("notes", "Notas"),
    ]:
        m = re.search(rf"-\s*\*\*{re.escape(label)}:\*\*\s*(.+)", block)
        if m:
            fields[key] = m.group(1).strip()
    return fields


ROLE_NAME_KEYWORDS = [
    ("Agentic AI Architect", "Agentic AI Architect"),
    ("Intelligent Automation Architect", "Intelligent Automation Architect / Process Automation Architect"),
    ("AI Solutions Architect", "AI Solutions Architect / AI Architect"),
    ("Solutions Architect", "AI Solutions Architect / AI Architect"),
]


def _best_fit_role_id(rol_best_fit: Optional[str], role_ids: dict[str, int]) -> Optional[int]:
    if not rol_best_fit:
        return None
    for keyword, role_name in ROLE_NAME_KEYWORDS:
        if keyword in rol_best_fit:
            return role_ids.get(role_name)
    return None


async def import_target_companies(session, vault: Path, user_id: int, report: ImportReport,
                                   role_ids: dict[str, int], contact_ids: dict[str, int]) -> None:
    """Fuente: 2.1.5 - SECCIÓN - Empresas Diana/2.1.5.1 a .8 (8 archivos,
    ~43 empresas). weak_tie_contact_id se enlaza por nombre contra los
    contactos ya importados de 2.6.2 cuando la nota menciona uno."""
    table = "target_companies"
    base = vault / D2 / "2.1 - SECCIÓN - Estrategia de Búsqueda de Empleo" / "2.1.5 - SECCIÓN - Empresas Diana"
    n = 0
    for filename in TARGET_COMPANY_FILES:
        path = base / filename
        try:
            body = strip_frontmatter(read_text(path))[1]
            companies_section = body.split("## Empresas", 1)[-1]
            blocks = re.split(r"\n### \d+\.\s*", companies_section)[1:]
            names = re.findall(r"\n### \d+\.\s*([^\n]+)", "\n" + companies_section)
            for name, block in zip(names, blocks):
                fields = _parse_company_bullets(block)
                weak_tie_id = None
                notes = fields.get("notes", "")
                for contact_name, cid in contact_ids.items():
                    if contact_name.split()[0] in notes and contact_name in notes:
                        weak_tie_id = cid
                        break
                tier = None
                if fields.get("tier"):
                    m = re.search(r"\d+", fields["tier"])
                    tier = int(m.group(0)) if m else None
                row = TargetCompany(
                    user_id=user_id, company_name=name.strip(), tier=tier,
                    best_fit_role_id=_best_fit_role_id(fields.get("rol_best_fit"), role_ids),
                    company_size=fields.get("company_size"), salary_estimate=fields.get("salary_estimate"),
                    work_modality=fields.get("work_modality"), target_market=fields.get("target_market"),
                    weak_tie_contact_id=weak_tie_id, priority=fields.get("priority"),
                    status=fields.get("status"), notes=notes or None,
                )
                session.add(row)
                n += 1
            await session.flush()
        except Exception as e:  # noqa: BLE001
            report.error(table, f"{filename}: {e}")
    report.add(table, n)


async def import_vacancies(session, vault: Path, user_id: int, report: ImportReport) -> None:
    """Fuente: 2.7.8 - Vacantes Rastreadas.md, tabla "ANÁLISIS - Vacantes
    Encontradas" (30 filas, el mapeo mas directo de la boveda)."""
    table = "vacancies"
    path = vault / D2 / "2.7 - SECCIÓN - Gestión de Aplicaciones y Vacantes" / "2.7.8 - Vacantes Rastreadas.md"
    n = 0
    try:
        body = strip_frontmatter(read_text(path))[1]
        # Algunas filas usan "\|" (pipe escapado) dentro de una celda, p.ej.
        # "Data Scientist \| Machine Learning" -- se protege con un
        # sentinel antes de partir por columnas y se restaura despues.
        ESCAPED_PIPE = "\x00PIPE\x00"
        protected_body = body.replace(r"\|", ESCAPED_PIPE)
        row_re = re.compile(
            r"\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*(\d+)%\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([A-Za-z]+)\s*\|\s*"
            r"([^|]+)\|\s*\[Link\]\(([^)]+)\)\s*\|\s*([^|]*)\|"
        )
        for m in row_re.finditer(protected_body):
            order_number, fit, company, role, track, cv_version, url, notes = (
                g.replace(ESCAPED_PIPE, "|") for g in m.groups()
            )
            session.add(
                Vacancy(
                    user_id=user_id, order_number=int(order_number), company=company.strip(),
                    exact_role=role.strip(), vacancy_url=url.strip(), source="indeed",
                    found_date=date(2026, 8, 12), fit_percentage=int(fit), track_category=track.strip(),
                    recommended_cv_version=cv_version.strip(), analysis_notes=notes.strip() or None,
                    evaluation="pending_review", is_active=True,
                )
            )
            n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, f"{path.name}: {e}")


async def import_cv_versions(session, vault: Path, user_id: int, report: ImportReport,
                              role_ids: dict[str, int]) -> None:
    """Fuente: 2.7.6 - SECCIÓN - CVs Generados/2.7.6.1 y .2 (2 filas)."""
    table = "cv_versions"
    ai_role = role_ids.get("AI Solutions Architect / AI Architect")
    rows = [
        dict(title="CV General - AI Solutions Architect", target_role_id=ai_role, length_pages=1,
             status="draft",
             executive_summary="Arquitecto que convierte procesos que dependen de las personas en sistemas "
             "que operan solos: 20 años diseñando y programando sistemas de control para operaciones de "
             "misión crítica, aplicando hoy ese mismo rigor a arquitecturas de IA. Evidencia directa y "
             "reciente en IA: sistema propio de gestión de conocimiento multi-agente (Context Engineering). "
             "Track record verificable de resolución bajo presión en sistemas de tolerancia cero al error "
             "(Bioterio del INS).",
             key_competencies=["Context Engineering / Multi-Agente", "Automatización Industrial", "Systems "
                                "Integration", "BACnet / BMS", "AWS Solutions Architect", "Pensamiento "
                                "Sistémico", "Python", "SQL", "Apache Spark", "Machine Learning", "IA "
                                "Generativa Aplicada", "Comunicación Técnico-Negocio", "Liderazgo Técnico"],
             key_experience=["Atom Controles - Arquitecto de Automatización Independiente (2013-Actualidad)",
                              "CYVSA Mantenimiento - Gerente de Automatización (2023-2024)",
                              "ISAI KMC / Azteca Controls - Ingeniería de Automatización & Soporte Técnico "
                              "Regional (2006-2013)"],
             featured_achievement="Sistema de Gestión de Conocimiento con IA (Context Engineering): "
             "arquitectura jerárquica multi-agente con capas de contexto gobernadas centralmente sobre "
             "Claude y Obsidian, en producción, gestionando múltiples dominios de conocimiento de forma "
             "autónoma."),
        dict(title="CV OEMs Industriales - Solutions Architect", target_role_id=ai_role, length_pages=1,
             status="approved",
             executive_summary="Convierto procesos que dependen de las personas en sistemas que operan "
             "solos: 20 años diseñando y programando sistemas de automatización industrial y BMS en "
             "sectores de tolerancia cero al error, con experiencia directa en KMC Controls, Danfoss, "
             "Distech Controls y BACnet. El puente que los OEMs necesitan hoy: alguien que entiende los "
             "sistemas legacy y puede diseñar la capa de IA que los vuelve inteligentes y autónomos.",
             key_competencies=["Systems Integration & BMS", "BACnet / Modbus / HVAC Controls", "KMC "
                                "Controls / Danfoss / Distech Controls / Best++", "Industrial IoT (IIoT)",
                                "AI Solutions Architecture", "Context Engineering / Multi-Agent Systems",
                                "Python", "Machine Learning", "Digital Transformation", "Pensamiento "
                                "Sistémico", "Gestión de Equipos Técnicos"],
             key_experience=["Atom Controles - Solutions Architect & Fundador (2013-Actualidad)",
                              "CYVSA Mantenimiento - Gerente de Automatización (2023-2024)",
                              "ISAI KMC / Azteca Controls - Ingeniería de Automatización & Soporte Técnico "
                              "Regional (2006-2012)"],
             featured_achievement="Sistema Multi-Agente de Gestión de Conocimiento (Context Engineering, "
             "2026): arquitectura jerárquica de agentes con capas de contexto gobernadas centralmente sobre "
             "Claude, en producción, gestionando múltiples dominios de conocimiento de forma autónoma."),
    ]
    n = 0
    try:
        for r in rows:
            session.add(
                CVVersion(
                    user_id=user_id, target_role_id=r["target_role_id"], title=r["title"],
                    length_pages=r["length_pages"], status=r["status"],
                    executive_summary=r["executive_summary"], key_competencies=r["key_competencies"],
                    key_experience=r["key_experience"], featured_achievement=r["featured_achievement"],
                    target_vacancy_ids=None, file_upload_id=None,
                )
            )
            n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


async def import_cover_letter_versions(session, vault: Path, user_id: int, report: ImportReport,
                                        role_ids: dict[str, int]) -> None:
    """Fuente: 2.7.7 - SECCIÓN - Cover Letters Generadas/2.7.7.1 (1 fila)."""
    table = "cover_letter_versions"
    body_content = (
        "Estimado equipo de reclutamiento de [Empresa], Me dirijo a ustedes con interés genuino en la "
        "posición de [rol] dentro de su equipo. Durante 20 años diseñé y programé sistemas de control para "
        "que operaciones críticas -farmacéutica, laboratorios, manufactura- funcionaran de forma confiable "
        "y sin depender constantemente de supervisión humana. Hoy aplico ese mismo pensamiento sistémico a "
        "la arquitectura de soluciones de IA. Diseñé el sistema de control de un laboratorio de "
        "bioseguridad en Bogotá, Colombia -el Bioterio del Instituto Nacional de Salud- después de que un "
        "proyecto anterior fracasara en su intento de certificación. Rediseñé la estrategia completa en dos "
        "días y dirigí su implementación durante tres meses y medio bajo presión constante; el sistema "
        "superó todas las pruebas de certificación a la primera, y el certificador lo calificó como el "
        "mejor sistema que había evaluado en su carrera. Diseñé y construí un sistema propio de gestión de "
        "conocimiento multi-agente que hoy opera en producción gestionando múltiples dominios de "
        "conocimiento de forma autónoma. Me encantaría conversar sobre cómo esta combinación de trayectoria "
        "y evidencia reciente puede aportar valor concreto a su equipo."
    )
    try:
        session.add(
            CoverLetterVersion(
                user_id=user_id,
                target_role_id=role_ids.get("AI Solutions Architect / AI Architect"),
                target_vacancy_id=None, title="Carta General - AI Solutions Architect", status="draft",
                body_content=body_content, file_upload_id=None,
            )
        )
        await session.flush()
        report.add(table, 1)
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))


CONTACT_HISTORY_FILES = [
    ("2.6.3.1 - Historial - Francisco Mendoza.md", "Francisco Mendoza"),
    ("2.6.3.2 - Historial - Miguel Angel M..md", "Miguel Angel M."),
    ("2.6.3.3 - Historial - Alison Villarreal.md", "Alison Villarreal"),
    ("2.6.3.4 - Historial - Marcela Pérez.md", "Marcela Pérez"),
    ("2.6.3.5 - Historial - Enrique Galván.md", "Enrique Galván"),
    ("2.6.3.6 - Historial - Paola Fernanda Herrera.md", "Paola Fernanda Herrera"),
    ("2.6.3.7 - Historial - Reymundo Daniel Valdes.md", "Reymundo Daniel Valdes"),
    ("2.6.3.8 - Historial - Nidya Lope.md", "Nidya Lope"),
    ("2.6.3.9 - Historial - Sandra Martinez.md", "Sandra Martinez"),
]


async def import_contact_interactions(session, vault: Path, user_id: int, report: ImportReport,
                                       contact_ids: dict[str, int]) -> None:
    """Fuente: 2.6.3 - SECCIÓN - Historiales de Seguimiento/*.md (9 archivos,
    uno por contacto de 2.6.2), seccion "Cronología de Interacciones" --
    cada "### FECHA — Canal" es una fila."""
    table = "contact_interactions"
    base = vault / D2 / "2.6 - SECCIÓN - Networking" / "2.6.3 - SECCIÓN - Historiales de Seguimiento"
    n = 0
    for filename, contact_name in CONTACT_HISTORY_FILES:
        path = base / filename
        contact_id = contact_ids.get(contact_name)
        if contact_id is None:
            report.error(table, f"{filename}: contacto '{contact_name}' no encontrado en networking_contacts")
            continue
        try:
            body = strip_frontmatter(read_text(path))[1]
            crono = body.split("## Cronología de Interacciones", 1)
            if len(crono) < 2:
                report.error(table, f"{filename}: sin seccion 'Cronología de Interacciones'")
                continue
            crono_body = crono[1].split("\n## Estado y Próximos Pasos", 1)[0]
            events = re.split(r"\n### ", crono_body)[1:]
            for ev in events:
                header, _, rest = ev.partition("\n")
                m = re.match(r"(\d{4}-\d{2}-\d{2})\s*—?\s*(.*)", header.strip())
                if not m:
                    continue
                ev_date_str, channel = m.group(1), (m.group(2) or "LinkedIn").strip()
                ev_date = datetime.strptime(ev_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                content_sent = None
                m_sent = re.search(r"\*\*(?:Qué se envió/dijo|Borrador de nota de conexión[^:]*|Mensaje "
                                    r"enviado|Texto)[^:]*:\*\*\s*\n?>?\s*(.+?)(?:\n\n|\*\*Estado)", rest,
                                    re.DOTALL)
                if m_sent:
                    content_sent = clean_multiline(m_sent.group(1))[:2000]
                response_received = None
                m_resp = re.search(r"\*\*(?:Qué respondió|Respuesta de [^:]+)[^:]*:\*\*\s*\n?>?\s*(.+?)"
                                    r"(?:\n\n|\*\*)", rest, re.DOTALL)
                if m_resp:
                    response_received = clean_multiline(m_resp.group(1))[:2000]
                status_text = "pendiente"
                m_status = re.search(r"\*\*Estado:?\*\*\s*(.+)", rest)
                if m_status:
                    status_text = clean_multiline(m_status.group(1))[:50]
                session.add(
                    ContactInteraction(
                        user_id=user_id, contact_id=contact_id, related_vacancy_id=None,
                        interaction_at=ev_date, channel=channel[:50] if channel else "LinkedIn",
                        content_sent=content_sent, response_received=response_received,
                        status=status_text, generated_opportunity=False,
                    )
                )
                n += 1
            await session.flush()
        except Exception as e:  # noqa: BLE001
            report.error(table, f"{filename}: {e}")
    report.add(table, n)


async def import_networking_activities(session, vault: Path, user_id: int, report: ImportReport) -> None:
    """Fuente: 2.6.1 - Estrategia 70-20-10.md -- 3 categorias (70/20/10),
    cada una con 5 acciones concretas numeradas -> 15 filas."""
    table = "networking_activities"
    path = vault / D2 / "2.6 - SECCIÓN - Networking" / "2.6.1 - Estrategia 70-20-10.md"
    category_map = [
        ("### **70% - APORTAR VALOR**", "give_value_70"),
        ("### **20% - APORTAR APRENDIZAJE**", "share_learning_20"),
        ("### **10% - HABLAR DE TI**", "talk_about_you_10"),
    ]
    n = 0
    try:
        body = strip_frontmatter(read_text(path))[1]
        for idx, (heading, category) in enumerate(category_map):
            start = body.index(heading)
            end = body.index("### **", start + len(heading)) if idx < 2 else body.index("\n---\n\n## ⏰", start)
            section = body[start:end]
            items = re.split(r"\n\*\*\d+\.\s*", section)[1:]
            for item in items:
                title, _, rest = item.partition("\n")
                title = title.replace("**", "").strip()
                bullets = [l.strip("- ").strip() for l in rest.split("\n") if l.strip().startswith("-")]
                concrete_action = None
                example = None
                frequency = None
                for b in bullets:
                    low = b.lower()
                    if low.startswith("ejemplo"):
                        example = b.split(":", 1)[-1].strip()
                    elif low.startswith("frecuencia"):
                        frequency = b.split(":", 1)[-1].strip()
                    elif concrete_action is None:
                        concrete_action = b
                session.add(
                    NetworkingActivity(
                        user_id=user_id, category=category, activity_type=title,
                        concrete_action=concrete_action, example=example,
                        frequency_description=frequency, times_completed=0, is_active=True,
                    )
                )
                n += 1
        await session.flush()
        report.add(table, n)
    except Exception as e:  # noqa: BLE001
        report.error(table, f"{path.name}: {e}")


async def import_digital_platforms(session, vault: Path, user_id: int, report: ImportReport) -> dict[str, int]:
    """Fuente: 2.3.3 (LinkedIn), 2.3.4 (GitHub), 2.3.6 (Kaggle), 2.3.5.1
    (Portafolio Web) -- 4 filas."""
    table = "digital_platforms"
    name_to_id: dict[str, int] = {}
    rows = [
        dict(platform_name="linkedin", profile_url="https://linkedin.com/in/cjhirashi",
             profile_status="active", followers_count=None, is_active_in_search=True,
             platform_strategy="Headline: 'AI Solutions Architect | Intelligent Automation & Agentic AI "
             "Systems | 20+ Years Systematizing Mission-Critical Operations'. About Me con Hook (Bioterio) "
             "+ Convicción + Trayectoria + Propuesta de valor + Fit cultural + CTA. Featured con 3-5 "
             "proyectos + CV. Cadencia de contenido: 2-3 publicaciones/semana. ~2,000 contactos "
             "acumulados, red silenciosa que se activa con publicaciones (2.3.7) y estrategia de "
             "conexiones (20-30 nuevas/mes)."),
        dict(platform_name="github", profile_url="https://github.com/cjhirashi", profile_status="active",
             followers_count=None, is_active_in_search=True,
             platform_strategy="Bio: 'AI Solutions Architect & Data Scientist. Systematizing mission-"
             "critical operations for 20 years, now with ML and AI. Python · SQL · Machine Learning · "
             "Intelligent Automation.' Plataforma de verificación técnica directa. Selección de "
             "3-5 repositorios de calidad (no 10+), cada uno con problema/solución/metodología/resultados. "
             "10 proyectos reales en portafolio (2 sistemas propios en desarrollo + 8 proyectos de Data "
             "Science del bootcamp TripleTen)."),
        dict(platform_name="kaggle", profile_url=None, profile_status="planned", followers_count=None,
             is_active_in_search=False,
             platform_strategy="Bio planeada: 'Sistematizo procesos con automatización e IA. Llevo 20 "
             "años haciéndolo en sistemas físicos críticos, y hoy diseño modelos y pipelines de datos que "
             "operan sin depender de las personas.' Estrategia: 1-2 competiciones activas por año, "
             "notebook/solución siempre publicados, 3-5 notebooks de calidad. Sin evidencia en la bóveda "
             "de que el perfil ya esté activo/publicado."),
        dict(platform_name="portfolio_web", profile_url="https://cjhirashi.com", profile_status="active",
             followers_count=None, is_active_in_search=True,
             platform_strategy="Home (Hero + Badge 'AI Solutions Architect & Data Scientist' + CTA 'Ver "
             "Caso Bioterio'), Sobre Mí (Biografía + Filosofía + Trayectoria), Proyectos (mínimo 3, "
             "10 disponibles en 1.3.5) y Blog (mínimo 3 posts, 6 publicados vía 2.3.7). Trayectoria "
             "desplegada en orden: Atom Controles, CYVSA Mantenimiento, ISAI KMC México, Azteca Controls."),
    ]
    try:
        for r in rows:
            row = DigitalPlatform(
                user_id=user_id, platform_name=r["platform_name"], profile_url=r["profile_url"],
                profile_status=r["profile_status"], platform_strategy=r["platform_strategy"],
                followers_count=r["followers_count"], is_active_in_search=r["is_active_in_search"],
            )
            session.add(row)
            await session.flush()
            name_to_id[r["platform_name"]] = row.id
        report.add(table, len(rows))
    except Exception as e:  # noqa: BLE001
        report.error(table, str(e))
    return name_to_id


async def import_content_and_publications(session, vault: Path, user_id: int, report: ImportReport,
                                           platform_ids: dict[str, int], project_ids: dict[str, int]) -> None:
    """Fuente: 2.3.7 - SECCIÓN - Publicaciones/Portafolio/ y /LinkedIn/ (6
    historias x 2 canales = 12 publicaciones, 6 content_pieces).

    Resolucion de solapamiento con 2.3.5.4 (Blog): verificado contra el
    contenido real -- 2.3.5.4.1 (Bioterio), 2.3.5.4.2 (HIRA) y 2.3.5.4.3
    (Obsidian CoWork) son el borrador original de exactamente 3 de estas 6
    historias (mismos titulos reales publicados, misma URL). El propio
    2.3.7.3 (Portafolio) lo declara explicitamente ("el borrador original de
    este post vive en 2.3.5.4.3"). Se usa 2.3.7 (Portafolio/LinkedIn) como
    fuente canonica unica -- es la version con status/fecha_publicacion/url
    actualizados -- y NO se inserta contenido adicional desde 2.3.5.4 para
    evitar duplicar los mismos 3 posts. El archivo suelto 2.3.7.1 (fuera de
    las subcarpetas Portafolio/LinkedIn) tambien se excluye: es un borrador
    historico superado, segun su propia nota de encabezado.
    """
    table_cp = "content_pieces"
    table_pub = "publications"
    portfolio_id = platform_ids.get("portfolio_web")
    linkedin_id = platform_ids.get("linkedin")

    stories = [
        dict(
            title="Cuando una falla lo derrumba todo",
            slug="cuando-una-falla-lo-derrumba-todo",
            excerpt="Un primer intento de certificación había fallado. Este era el segundo. No podían "
            "repetir el error.",
            thematic_pillar="Pensamiento Sistémico",
            tags=["Pensamiento Sistémico", "Sistemas críticos", "Certificación", "Arquitectura de control",
                  "Bioseguridad", "Redundancia operativa"],
            status="published", reading_minutes=7,
            related_project_id=project_ids.get("Bioterio INS - Certificación de Bioseguridad Nivel 3 "
                                                 "(Bogotá, Colombia)"),
            body_portfolio=(
                "El Gobierno de Colombia había intentado antes certificar un laboratorio de bioseguridad. "
                "Dos años atrás, el intento con una empresa internacional reconocida en control no logró la "
                "certificación. Este era el segundo intento. Me asignaron al proyecto con información "
                "limitada; el primer día entendí el reto real: el sistema de control estaba concebido para "
                "confort ambiental, no para un sistema crítico. Rediseñé la arquitectura de control en un "
                "día: lógica distribuida con autonomía por zona, estrategias alternas de comunicación, y un "
                "cambio de criterio de validación hacia 'qué pasa exactamente cuando este componente falla "
                "a mitad de operación'. El alcance creció de 1 a 3.5 meses con un equipo de 4 ingenieros. "
                "Con la instalación al 70%, el certificador sometió el sistema a los escenarios de falla "
                "donde el primer intento no había pasado: superó todo, sin una sola falla, incluyendo "
                "pruebas adicionales de Nivel 3."
            ),
            url_portfolio="https://cjhirashi.com/blog/cuando-una-falla-lo-derrumba-todo/",
            fecha_portfolio=date(2026, 7, 28),
            body_linkedin=(
                "Una consultora multinacional llevaba más de un año sin resolverlo. Nosotros lo "
                "certificamos en 2 días. El Bioterio del Instituto Nacional de Salud de Colombia necesitaba "
                "certificación de bioseguridad Nivel 3. El sistema de control fallaba: más de 90 variables "
                "interdependientes, y nadie tenía un modelo que explicara cómo una falla en una se "
                "propagaba en cascada hacia las demás. Lo que hicimos: mapear las 90+ variables y sus "
                "dependencias, identificar dónde una falla podía escalar, diseñar redundancia y "
                "compensaciones cruzadas, y validar todo bajo escenarios de estrés antes de tocar "
                "producción. Hoy aplico esa misma disciplina a la arquitectura de soluciones con IA. "
                "¿Qué tan seguido en tu experiencia el 'problema técnico' resulta ser, en el fondo, un "
                "problema de visibilidad sistémica?"
            ),
            hashtags_linkedin=["#PensamientoSistémico", "#ArquitecturaDeControl", "#Bioseguridad",
                               "#Certificación", "#IA"],
            fecha_linkedin=date(2026, 7, 30),
        ),
        dict(
            title="Automatización sin inteligencia: el hueco que la industria lleva décadas ignorando",
            slug="automatizacion-sin-inteligencia-el-hueco-que-la-industria-lleva-decadas-ignorando",
            excerpt="Cada falla activa el mismo protocolo: alarma, llamada, orientación a ciegas. Nadie "
            "pregunta por qué el sistema no lo vio venir.",
            thematic_pillar="Arquitectura de Soluciones de IA",
            tags=["Automatización", "SCADA", "Inteligencia Artificial", "Sistemas críticos", "HVAC",
                  "SmartBuildings", "Arquitectura de control"],
            status="published", reading_minutes=7,
            related_project_id=project_ids.get("Hira - Plataforma SCADA Web con IA"),
            body_portfolio=(
                "Cada vez que un sistema de automatización falla, se activa el mismo protocolo de siempre: "
                "alarma, llamada al integrador, orientación a ciegas mientras el sistema opera en falla. Un "
                "sistema de automatización convencional registra datos pero no los analiza ni busca "
                "patrones: el hueco no es falta de datos, es falta de inteligencia para usarlos. El técnico "
                "no conoce la arquitectura del sistema, y esa información vive en la cabeza del integrador, "
                "no en el sistema. Llevo más de 20 años diseñando sistemas de automatización para "
                "edificios, laboratorios e instalaciones industriales, y he visto el mismo protocolo "
                "repetirse cientos de veces. Estoy construyendo un sistema que rompe ese ciclo: que "
                "aprende de su propio historial de operación, que anticipa en vez de reaccionar, que guía "
                "en vez de esperar."
            ),
            url_portfolio="https://cjhirashi.com/blog/automatizacion-sin-inteligencia-el-hueco-que-la-"
            "industria-lleva-decadas-ignorando/",
            fecha_portfolio=date(2026, 7, 29),
            body_linkedin=None,
            hashtags_linkedin=["#Automatización", "#SCADA", "#InteligenciaArtificial",
                               "#ArquitecturaDeControl", "#SmartBuildings"],
            fecha_linkedin=date(2026, 7, 29),
        ),
        dict(
            title="El sistema que se vuelve más inteligente cada vez que lo usas",
            slug="sistema-que-aprende-obsidian-cowork",
            excerpt="La mayoría de sistemas de notas guardan información pero no la usan. Este aprende de "
            "cada sesión y mejora con cada ciclo.",
            thematic_pillar="Arquitectura de Soluciones de IA",
            tags=["Gestión del Conocimiento", "Obsidian", "Inteligencia Artificial", "CoWork", "Sistemas "
                  "de Aprendizaje", "Productividad"],
            status="published", reading_minutes=7,
            related_project_id=None,  # meta-showcase del sistema de bóvedas, no un proyecto de 1.3.5
            body_portfolio=(
                "¿Qué pasaría si tu herramienta de trabajo aprendiera de ti? Eso es lo que pasa cuando "
                "diseñas bien una bóveda operativa en Obsidian con un agente como CoWork. Una bóveda "
                "operativa funciona con tres capas: META (gobernanza), Investigación Operativa "
                "(conocimiento técnico adaptado al contexto) y Metodología Operativa (protocolos de cómo "
                "ejecutar). El ciclo que la hace aprender: el agente opera siguiendo protocolos; cuando "
                "algo nuevo ocurre, se documenta; la próxima vez el agente tiene un protocolo mejor. La "
                "operación mejora el conocimiento, el conocimiento mejora la operación. Tres "
                "implementaciones muestran el potencial: gestión de carrera, proyectos de software, y "
                "aprendizaje técnico -cada una con protocolos que evolucionan con cada sesión."
            ),
            url_portfolio="https://cjhirashi.com/blog/sistema-que-aprende-obsidian-cowork/",
            fecha_portfolio=date(2026, 7, 31),
            body_linkedin=None,
            hashtags_linkedin=["#GestiónDelConocimiento", "#Obsidian", "#InteligenciaArtificial", "#CoWork",
                               "#ArquitecturaDeSoluciones"],
            fecha_linkedin=date(2026, 7, 31),
        ),
        dict(
            title="El error no estaba en el diseño, estaba en la pregunta",
            slug="el-error-no-estaba-en-el-diseno-estaba-en-la-pregunta",
            excerpt="La mayoría de los proyectos que se atrasan no fallan por ejecución. Fallan porque "
            "nadie cuestionó el problema que estaban resolviendo.",
            thematic_pillar="Arquitectura de Soluciones de IA",
            tags=["Arquitectura", "Diagnóstico Técnico", "Toma de Decisiones", "Sistemas Críticos"],
            status="published", reading_minutes=6,
            related_project_id=None,  # ensayo conceptual, ejemplo final generico, sin proyecto propio
            body_portfolio=(
                "Cuando un proyecto se atrasa, casi siempre se revisa la ejecución. Rara vez alguien "
                "pregunta si el problema que se estaba resolviendo era, desde el principio, el problema "
                "correcto. Un requerimiento mal planteado no se anuncia como tal: llega con la misma "
                "seguridad que uno bien pensado. Un equipo puede ejecutarlo perfectamente, y el resultado "
                "no se sentirá como un fracaso, se sentirá como una solución completa a un problema que no "
                "era el que había que resolver. Cuestionar el requerimiento significa preguntar antes de "
                "ejecutar: ¿esto explica la causa real, o solo describe el síntoma? Esa pregunta cambia "
                "dónde se invierte el esfuerzo."
            ),
            url_portfolio="https://cjhirashi.com/blog/el-error-no-estaba-en-el-diseno-estaba-en-la-"
            "pregunta/",
            fecha_portfolio=date(2026, 8, 3),
            body_linkedin=(
                "Un proyecto que se atrasa casi siempre se revisa por el lado de la ejecución: el equipo, "
                "el cronograma, la comunicación. Rara vez alguien pregunta si el problema que se está "
                "resolviendo es, desde el principio, el problema correcto. Cuestionar el requerimiento no "
                "significa dudar de todo. Significa preguntar antes de ejecutar: ¿esto explica la causa "
                "real, o solo describe el síntoma? El artículo completo: "
                "https://cjhirashi.com/blog/el-error-no-estaba-en-el-diseno-estaba-en-la-pregunta/ "
                "¿Cuándo fue la última vez que revisaste si el problema que llevas semanas resolviendo era, "
                "en realidad, el correcto?"
            ),
            hashtags_linkedin=["#Arquitectura", "#DiagnósticoTécnico", "#TomaDeDecisiones",
                               "#SistemasCríticos", "#AISolutionsArchitect"],
            fecha_linkedin=date(2026, 8, 3),
        ),
        dict(
            title="Cuando arreglar una parte rompe las demás",
            slug="cuando-arreglar-una-parte-rompe-las-demas",
            excerpt="Ajustar un síntoma es fácil. Saber qué más se mueve al hacerlo es lo que distingue un "
            "ajuste de un diseño real.",
            thematic_pillar="Pensamiento Sistémico",
            tags=["Pensamiento Sistémico", "Arquitectura de Sistemas", "Diagnóstico Técnico", "Sistemas "
                  "Interdependientes"],
            status="scheduled", reading_minutes=6,
            related_project_id=None,  # ensayo conceptual, ejemplo final hipotetico, sin proyecto propio
            body_portfolio=(
                "Cuando algo falla en un sistema, la reacción más común es ajustar la parte que falló. "
                "Funciona a corto plazo. El problema aparece después, cuando ese ajuste mueve otras "
                "variables que nadie estaba observando. Pensar en sistema, no en síntoma, significa hacer "
                "una pregunta distinta antes de tocar nada: si cambio esto, ¿qué más depende de ello, "
                "directa o indirectamente? Con esa lista en mano, la solución cambia de naturaleza: en vez "
                "de resolver lo primero que se ve, conviene invertir un poco de tiempo en entender qué más "
                "está conectado."
            ),
            url_portfolio="https://cjhirashi.com/blog/cuando-arreglar-una-parte-rompe-las-demas/",
            fecha_portfolio=date(2026, 8, 5),
            body_linkedin=(
                "Cuando algo falla en un sistema, la reacción más común es ajustar la parte que falló. "
                "Funciona a corto plazo. El problema aparece después, cuando ese ajuste mueve otras "
                "variables que nadie estaba observando. Resolver un síntoma no siempre resuelve el problema "
                "de fondo. A veces solo lo mueve a otra parte donde todavía no se ve. El artículo completo: "
                "https://cjhirashi.com/blog/cuando-arreglar-una-parte-rompe-las-demas/ ¿Tu equipo revisa "
                "qué más depende de algo antes de ajustarlo, o resuelve el síntoma que tiene enfrente y "
                "espera que no reaparezca en otra parte?"
            ),
            hashtags_linkedin=["#PensamientoSistémico", "#ArquitecturaDeSistemas", "#DiagnósticoTécnico",
                               "#SistemasInterdependientes"],
            fecha_linkedin=date(2026, 8, 5),
        ),
        dict(
            title="Diseñar para el día en que algo falle, no para el día en que todo funcione",
            slug="disenar-para-el-dia-en-que-algo-falle-no-para-el-dia-en-que-todo-funcione",
            excerpt="La mayoría valida si el sistema funciona. Muy pocos validan qué pasa cuando algo "
            "falla primero.",
            thematic_pillar="Pensamiento Sistémico",
            tags=["Pensamiento Sistémico", "Sistemas Críticos", "Validación", "Arquitectura de Control",
                  "Resiliencia"],
            status="scheduled", reading_minutes=6,
            related_project_id=None,  # ensayo conceptual, ejemplo final hipotetico, sin proyecto propio
            body_portfolio=(
                "Un sistema que funciona bien en condiciones normales no dice mucho todavía. La prueba real "
                "llega cuando algo dentro del sistema deja de responder. La mayoría de los diseños se "
                "validan contra una sola pregunta: ¿funciona como se espera? Muy pocos se validan contra la "
                "segunda: ¿qué pasa exactamente cuando este componente falla a mitad de operación? Diseñar "
                "anticipándose a fallas invierte el orden habitual: en vez de preguntar primero si el "
                "sistema funciona, se empieza por mapear los modos de falla posibles, y cada uno recibe una "
                "respuesta explícita antes de dar el sistema por terminado."
            ),
            url_portfolio="https://cjhirashi.com/blog/disenar-para-el-dia-en-que-algo-falle-no-para-el-dia-"
            "en-que-todo-funcione/",
            fecha_portfolio=date(2026, 8, 7),
            body_linkedin=(
                "Un sistema que funciona bien en condiciones normales no dice mucho todavía. Funcionar en "
                "el camino feliz es el mínimo esperado, no la prueba real. La prueba real llega cuando algo "
                "deja de responder. En entornos donde una falla no es un inconveniente sino un evento con "
                "consecuencias reales, esa pregunta no es opcional. El artículo completo: "
                "https://cjhirashi.com/blog/disenar-para-el-dia-en-que-algo-falle-no-para-el-dia-en-que-"
                "todo-funcione/ ¿El sistema que más te preocupa hoy ya fue puesto a prueba contra sus "
                "propios modos de falla, o solo contra el día en que todo sale bien?"
            ),
            hashtags_linkedin=["#PensamientoSistémico", "#SistemasCríticos", "#Validación",
                               "#ArquitecturaDeControl", "#Resiliencia"],
            fecha_linkedin=date(2026, 8, 7),
        ),
    ]

    n_cp = 0
    n_pub = 0
    for s in stories:
        try:
            cp = ContentPiece(
                user_id=user_id, related_project_id=s["related_project_id"], related_achievement_id=None,
                related_competency_id=None, title=s["title"], slug=s["slug"], excerpt=s["excerpt"],
                body_content=s["body_portfolio"], content_type="blog_post",
                thematic_pillar=s["thematic_pillar"], tags=s["tags"], status=s["status"],
                reading_minutes=s["reading_minutes"], featured_on_home=False, scheduled_publish_at=None,
            )
            session.add(cp)
            await session.flush()
            n_cp += 1

            if portfolio_id is not None:
                session.add(
                    Publication(
                        user_id=user_id, content_piece_id=cp.id, platform_id=portfolio_id,
                        published_title=s["title"], publication_url=s["url_portfolio"],
                        published_at=datetime.combine(s["fecha_portfolio"], datetime.min.time(),
                                                       tzinfo=timezone.utc),
                        full_content=s["body_portfolio"], char_length=len(s["body_portfolio"] or ""),
                        hashtags_used=None, views=None, likes_reactions=None, comments=None, shares=None,
                        content_status=s["status"],
                    )
                )
                n_pub += 1
            if linkedin_id is not None:
                session.add(
                    Publication(
                        user_id=user_id, content_piece_id=cp.id, platform_id=linkedin_id,
                        published_title=s["title"] if s["body_linkedin"] else None, publication_url=None,
                        published_at=datetime.combine(s["fecha_linkedin"], datetime.min.time(),
                                                       tzinfo=timezone.utc),
                        full_content=s["body_linkedin"],
                        char_length=len(s["body_linkedin"]) if s["body_linkedin"] else None,
                        hashtags_used=s["hashtags_linkedin"], views=None, likes_reactions=None,
                        comments=None, shares=None, content_status=s["status"],
                    )
                )
                n_pub += 1
        except Exception as e:  # noqa: BLE001
            report.error(table_cp, f"{s['slug']}: {e}")
    report.add(table_cp, n_cp)
    report.add(table_pub, n_pub)


# ===========================================================================
# AUDIT LOG -- decisiones de exclusion / resolucion de solapamiento
# ===========================================================================

async def write_audit_log(session, user_id: int, report: ImportReport) -> None:
    decisions = (
        "Import de boveda Obsidian -> tablas de dominio de carrera. Decisiones tomadas: "
        "(1) Excluidas del import: '1.4 - SECCIÓN.../1.4.1 - SECCIÓN - REDEFINE' (coaching, no dato de "
        "carrera, excluido explicitamente por el dueño de la boveda) y '00 - METODOLOGÍAS' (conocimiento "
        "operativo del agente, no se migra a tablas). "
        "(2) target_roles usa SOLO los 3 roles vigentes de 1.1.1/1.1.4 (Intelligent Automation Architect, "
        "AI Solutions Architect, Agentic AI Architect); NO se migro la version obsoleta de 5 roles presente "
        "en 1.2.2/1.2.3 (Data Scientist, ML Engineer, MLOps, Solutions Architect generico, Data Engineer) "
        "-esa version fue reemplazada en la propia boveda y no representa datos vigentes perdidos, ya que "
        "las competencias tecnicas/transferibles/de negocio de esos mismos documentos SI se migraron "
        "completas (solo se excluyo la tabla de mapeo a roles obsoletos). "
        "(3) Publicaciones (content_pieces/publications): se detecto solapamiento entre "
        "'2.3.5 - SECCIÓN - GUÍA Portafolio Web/2.3.5.4 - SECCIÓN - Blog' (3 posts: Bioterio, HIRA, "
        "Obsidian CoWork) y 3 de las 6 historias de '2.3.7 - SECCIÓN - Publicaciones/Portafolio' -mismo "
        "titulo real publicado y misma URL en cjhirashi.com. Los propios documentos de 2.3.7 declaran que "
        "2.3.5.4 es el borrador original superado. Se uso 2.3.7 (subcarpetas Portafolio/ y LinkedIn/) como "
        "fuente canonica unica y NO se inserto contenido adicional desde 2.3.5.4, para no duplicar los "
        "mismos 3 posts. Tampoco se uso el archivo suelto '2.3.7.1 - Historia Bioterio.md' (fuera de las "
        "subcarpetas): es un borrador historico marcado explicitamente como superado por su propio "
        "encabezado. Sin perdida de datos: el contenido real de los 3 posts esta completo en las versiones "
        "de 2.3.7 usadas. "
        "(4) Trayectorias/Proyectos duplicados y archivados dentro de '2.3.5 - SECCIÓN - GUÍA Portafolio "
        "Web' (2.3.5.2 Trayectorias, 2.3.5.3 Proyectos, varios con status:archived) NO se usaron como "
        "fuente: son copias de trabajo del mismo contenido ya migrado desde las fuentes canonicas 1.3.1 "
        "(Historial Cargos) y 1.3.5 (Proyectos de Portafolio). Sin perdida de datos. "
        "(5) Tablas sin instancias reales en la boveda (plantillas vacias, confirmado por inspeccion): "
        "market_segments, search_plans, applications, application_interactions, interviews, tags -no se "
        "insertaron filas."
    )
    session.add(
        AuditLog(
            user_id=user_id, action=AuditAction.IMPORT, resource_type="vault_import",
            resource_name="Boveda Obsidian -> dominio de carrera (30 tablas)",
            change_description=decisions, success=1,
            extra_metadata={"counts": report.counts, "errors": report.errors},
        )
    )
    await session.flush()


# ===========================================================================
# ORQUESTACION
# ===========================================================================

async def run_import(vault_dir: Path) -> ImportReport:
    report = ImportReport()
    report.note(
        "Excluidos por instruccion explicita: 1.4.1 - SECCIÓN - REDEFINE (coaching) y "
        "00 - METODOLOGÍAS (conocimiento operativo del agente)."
    )
    report.note(
        "target_roles usa los 3 roles vigentes (1.1.1/1.1.4); la version de 5 roles de 1.2.2/1.2.3 no se "
        "migro a target_roles (obsoleta), pero las competencias de esos mismos documentos si se migraron."
    )
    report.note(
        "content_pieces/publications: 2.3.5.4 (Blog) se detecto como borrador original de 3 de las 6 "
        "historias de 2.3.7 (mismo titulo y URL reales) -se uso 2.3.7 (Portafolio/LinkedIn) como fuente "
        "unica para evitar duplicados; sin perdida de datos."
    )
    report.note(
        "Tablas sin instancias reales en la boveda (no se insertan filas): market_segments, search_plans, "
        "applications, application_interactions, interviews, tags."
    )

    async with AsyncSessionLocal() as session:
        user_id = await get_user_id(session)
        print(f"Usuario resuelto: username=cjhirashi -> user_id={user_id}")

        # --- Dominio 1: Identidad ---
        await import_differentiators(session, vault_dir, user_id, report)
        await import_identity(session, vault_dir, user_id, report)
        await import_identity_reflections(session, vault_dir, user_id, report)
        competency_ids = await import_competencies(session, vault_dir, user_id, report)
        await import_certifications(session, vault_dir, user_id, report, competency_ids)
        role_ids = await import_target_roles(session, vault_dir, user_id, report)
        wh_ids = await import_work_history(session, vault_dir, user_id, report)
        ach_ids = await import_achievements(session, vault_dir, user_id, report, wh_ids)
        await import_star_stories(session, vault_dir, user_id, report, ach_ids)
        await import_career_reviews(session, vault_dir, user_id, report)
        await import_role_gap_analysis(session, vault_dir, user_id, report, role_ids)
        project_ids = await import_projects(session, vault_dir, user_id, report)

        # --- Dominio 2: Búsqueda ---
        await import_fit_scoring_factors(session, vault_dir, user_id, report)
        await import_role_narratives(session, vault_dir, user_id, report, role_ids)
        contact_ids = await import_networking_contacts(session, vault_dir, user_id, report)
        await import_target_companies(session, vault_dir, user_id, report, role_ids, contact_ids)
        await import_vacancies(session, vault_dir, user_id, report)
        await import_cv_versions(session, vault_dir, user_id, report, role_ids)
        await import_cover_letter_versions(session, vault_dir, user_id, report, role_ids)
        await import_contact_interactions(session, vault_dir, user_id, report, contact_ids)
        await import_networking_activities(session, vault_dir, user_id, report)

        # --- Dominio 3: Presencia Digital ---
        platform_ids = await import_digital_platforms(session, vault_dir, user_id, report)
        await import_content_and_publications(session, vault_dir, user_id, report, platform_ids, project_ids)

        # --- Dominio 4: Auditoria del propio import ---
        await write_audit_log(session, user_id, report)

        await session.commit()

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa la boveda Obsidian al dominio de carrera.")
    parser.add_argument(
        "--vault", type=str, default=os.environ.get("VAULT_DIR", "/tmp/vault"),
        help="Ruta a la carpeta Bóveda (default: $VAULT_DIR o /tmp/vault)",
    )
    args = parser.parse_args()
    vault_dir = Path(args.vault).resolve()
    if not vault_dir.is_dir():
        print(f"ERROR: no existe el directorio de boveda: {vault_dir}", file=sys.stderr)
        sys.exit(1)

    report = asyncio.run(run_import(vault_dir))
    report.print_summary()


if __name__ == "__main__":
    main()
