"""
ct_client.py
------------
Consulta crt.sh (interfaz pública sobre los logs de Certificate
Transparency) para un dominio y extrae todos los nombres (SAN) que
han aparecido alguna vez en un certificado emitido para ese dominio
o sus subdominios.

Por qué certificados HISTÓRICOS y no solo los vigentes: un nombre
que apareció en un certificado hace dos años y ya no tiene uno
vigente puede seguir teniendo DNS activo y un servicio corriendo
detrás -- es infraestructura que el propio equipo de la empresa
puede haber olvidado, y es exactamente el tipo de activo que un
inventario "oficial" no recoge.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import List, Set

import requests

CRTSH_URL = "https://crt.sh/"


@dataclass
class CertEntry:
    id: int
    name_value: str
    issuer_name: str
    not_before: str
    not_after: str


def fetch_certificates(domain: str, retries: int = 5, backoff_seconds: float = 5.0) -> List[CertEntry]:
    """
    Descarga el listado de certificados de crt.sh para `%.domain`
    (incluye subdominios) en formato JSON.

    crt.sh no tiene SLA de disponibilidad garantizada, así que se
    reintenta con backoff simple antes de rendirse.
    """
    params = {"q": f"%.{domain}", "output": "json"}

    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(CRTSH_URL, params=params, timeout=30)
            response.raise_for_status()
            raw_entries = response.json()
            break
        except (requests.RequestException, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(backoff_seconds * (attempt + 1))
    else:
        raise RuntimeError(f"No se pudo consultar crt.sh tras {retries} intentos: {last_error}")

    entries = []
    for raw in raw_entries:
        entries.append(
            CertEntry(
                id=raw.get("id", 0),
                name_value=raw.get("name_value", ""),
                issuer_name=raw.get("issuer_name", ""),
                not_before=raw.get("not_before", ""),
                not_after=raw.get("not_after", ""),
            )
        )
    return entries


def extract_unique_names(entries: List[CertEntry]) -> Set[str]:
    """
    Cada CertEntry.name_value puede contener varios nombres separados
    por salto de línea (certificados multi-SAN). Se normalizan a
    minúsculas, se descartan wildcards duplicados de su base y se
    devuelve un set único.
    """
    names: Set[str] = set()
    wildcard_pattern = re.compile(r"^\*\.")

    for entry in entries:
        for raw_name in entry.name_value.split("\n"):
            name = raw_name.strip().lower()
            if not name:
                continue
            names.add(name)
            # si es wildcard, añadimos también la base sin "*."
            # porque a veces solo aparece la forma wildcard en crt.sh
            base = wildcard_pattern.sub("", name)
            if base != name:
                names.add(base)

    return names
