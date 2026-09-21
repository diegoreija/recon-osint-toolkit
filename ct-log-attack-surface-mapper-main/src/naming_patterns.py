"""
naming_patterns.py
-------------------
Analiza los nombres observados para detectar convenciones de naming
(prefijos y sufijos frecuentes) y, a partir de ellas, sugiere nombres
candidatos que aún no se han visto en los certificados.

Importante: esto NO hace fuerza bruta ciega contra un diccionario
genérico. Solo combina los prefijos/sufijos que la propia organización
ya demostró usar (ej. si existen "dev-api" y "staging-api", sugiere
"prod-api" y "test-api" como huecos del mismo patrón) con el resto
de nombres base observados. Es inferencia sobre datos reales, no
adivinanza genérica -- por eso encaja en un flujo pasivo/OSINT.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Set

# Prefijos/sufijos comunes en entornos corporativos. Sirven como
# "vocabulario semilla" -- solo se sugieren si encajan con el patrón
# ya observado en los nombres reales, no se prueban todos a ciegas.
COMMON_ENV_TOKENS = ["dev", "staging", "stage", "test", "qa", "prod", "uat", "preprod"]
COMMON_INFRA_TOKENS = ["vpn", "mail", "admin", "internal", "intranet", "api", "portal"]

SEPARATOR_PATTERN = re.compile(r"[-.]")


@dataclass
class NamingInsight:
    detected_prefixes: List[str]
    detected_suffixes: List[str]
    suggested_candidates: List[str]


def _split_subdomain_label(full_name: str, root_domain: str) -> str:
    """Extrae solo la etiqueta de subdominio, sin el dominio raíz."""
    suffix = f".{root_domain}"
    if full_name.endswith(suffix):
        return full_name[: -len(suffix)]
    return full_name


def analyze_naming_patterns(names: Set[str], root_domain: str) -> NamingInsight:
    labels = [
        _split_subdomain_label(n, root_domain)
        for n in names
        if n != root_domain and not n.startswith("*.")
    ]

    prefix_counter: Counter = Counter()
    suffix_counter: Counter = Counter()

    for label in labels:
        parts = [p for p in SEPARATOR_PATTERN.split(label) if p]
        if not parts:
            continue
        prefix_counter[parts[0]] += 1
        if len(parts) > 1:
            suffix_counter[parts[-1]] += 1

    # Consideramos "patrón detectado" un token que aparece 2+ veces
    detected_prefixes = [tok for tok, count in prefix_counter.items() if count >= 2]
    detected_suffixes = [tok for tok, count in suffix_counter.items() if count >= 2]

    # Base names: la parte "core" del subdominio quitando prefijos/sufijos
    # de entorno conocidos, para poder recombinar
    base_names: Set[str] = set()
    for label in labels:
        parts = [p for p in SEPARATOR_PATTERN.split(label) if p]
        core_parts = [p for p in parts if p not in COMMON_ENV_TOKENS]
        if core_parts:
            base_names.add("-".join(core_parts))

    existing_labels = set(labels)
    suggested: Set[str] = set()

    # Solo sugerimos combinaciones de tokens de entorno DETECTADOS
    # como patrón real en este dominio, no todos los de la lista semilla
    env_tokens_in_use = [t for t in COMMON_ENV_TOKENS if t in detected_prefixes or t in detected_suffixes]

    for base in base_names:
        for env_token in env_tokens_in_use:
            candidate_prefix_style = f"{env_token}-{base}"
            candidate_suffix_style = f"{base}-{env_token}"
            for candidate in (candidate_prefix_style, candidate_suffix_style):
                if candidate not in existing_labels:
                    suggested.add(f"{candidate}.{root_domain}")

    return NamingInsight(
        detected_prefixes=sorted(detected_prefixes),
        detected_suffixes=sorted(detected_suffixes),
        suggested_candidates=sorted(suggested),
    )
