"""
Registro de perfiles de agente: vista mínima (id, label, nivel) del catálogo completo.

Es lo que `contracts/agent-registry.json` fija como canon compartido con la API (que conserva
solo este registro para validar `agent_profile_ids` y mostrar `agent_label`). La definición
completa (prompts, tools, delegación) vive en `services/agent_profiles.py`; este módulo se
deriva de ella para que no puedan divergir. El test de contrato compara ambos con el JSON.
"""
from dataclasses import dataclass
from typing import List, Set

from services import agent_profiles


@dataclass(frozen=True)
class RegistryEntry:
    id: str
    label: str
    level: int


def registry_entries() -> List[RegistryEntry]:
    return [RegistryEntry(p.id, p.label, p.level) for p in agent_profiles.list_profiles()]


def known_profile_ids() -> Set[str]:
    return {e.id for e in registry_entries()}
