"""
extractor.py
------------
Descarga ficheros JS de un listado de URLs (bundles de producción) y
aplica los patrones de patterns.py para extraer secretos, junto con
el contexto (unas pocas líneas alrededor) para facilitar la revisión
manual y reducir falsos positivos evidentes a simple vista.
"""

from dataclasses import dataclass
from typing import List

import requests

from patterns import PATTERNS, SecretType


@dataclass
class FoundSecret:
    secret_type: SecretType
    value: str
    source_url: str
    context: str


def fetch_js(url: str, timeout_seconds: float = 15.0) -> str:
    """Descarga el contenido de un fichero JS. Devuelve cadena vacía si falla."""
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""


def extract_context(content: str, match_start: int, match_end: int, window: int = 40) -> str:
    """Devuelve una porción de texto alrededor del match, para dar contexto sin volcar todo el fichero."""
    start = max(0, match_start - window)
    end = min(len(content), match_end + window)
    snippet = content[start:end].replace("\n", " ")
    return snippet.strip()


def scan_content(content: str, source_url: str) -> List[FoundSecret]:
    """Aplica todos los patrones conocidos sobre el contenido de un fichero JS."""
    findings: List[FoundSecret] = []

    for pattern in PATTERNS:
        for match in pattern.regex.finditer(content):
            value = match.group(1)
            context = extract_context(content, match.start(), match.end())
            findings.append(
                FoundSecret(
                    secret_type=pattern.secret_type,
                    value=value,
                    source_url=source_url,
                    context=context,
                )
            )

    return findings


def scan_urls(urls: List[str]) -> List[FoundSecret]:
    """Descarga y escanea una lista de URLs de ficheros JS."""
    all_findings: List[FoundSecret] = []
    for url in urls:
        content = fetch_js(url)
        if not content:
            continue
        all_findings.extend(scan_content(content, url))
    return all_findings
