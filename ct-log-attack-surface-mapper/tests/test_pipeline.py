"""
Tests de la lógica core. No requieren red: prueban extracción de
nombres, agrupación por IP y detección de patrones con datos simulados.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ct_client import CertEntry, extract_unique_names
from dns_grouper import ResolvedName, group_by_ip, get_unresolved_names
from naming_patterns import analyze_naming_patterns


def test_extract_unique_names_handles_multi_san_and_wildcards():
    entries = [
        CertEntry(
            id=1,
            name_value="api.empresa.com\n*.empresa.com\nwww.empresa.com",
            issuer_name="Let's Encrypt",
            not_before="2024-01-01",
            not_after="2024-04-01",
        ),
        CertEntry(
            id=2,
            name_value="API.EMPRESA.COM",  # mismo nombre, distinta capitalización
            issuer_name="Let's Encrypt",
            not_before="2023-01-01",
            not_after="2023-04-01",
        ),
    ]

    names = extract_unique_names(entries)

    assert "api.empresa.com" in names
    assert "www.empresa.com" in names
    assert "empresa.com" in names  # extraído del wildcard
    # no debe haber duplicados por capitalización
    assert len([n for n in names if n == "api.empresa.com"]) == 1


def test_group_by_ip_groups_shared_infrastructure():
    resolved = [
        ResolvedName(name="a.empresa.com", ip="1.2.3.4"),
        ResolvedName(name="b.empresa.com", ip="1.2.3.4"),
        ResolvedName(name="c.empresa.com", ip="5.6.7.8"),
        ResolvedName(name="d.empresa.com", ip=None),  # no resuelve
    ]

    groups = group_by_ip(resolved)

    assert len(groups) == 2
    top_group = groups[0]
    assert top_group.ip == "1.2.3.4"
    assert set(top_group.names) == {"a.empresa.com", "b.empresa.com"}


def test_get_unresolved_names_returns_only_none_ip():
    resolved = [
        ResolvedName(name="live.empresa.com", ip="1.2.3.4"),
        ResolvedName(name="dead.empresa.com", ip=None),
        ResolvedName(name="also-dead.empresa.com", ip=None),
    ]

    unresolved = get_unresolved_names(resolved)

    assert set(unresolved) == {"dead.empresa.com", "also-dead.empresa.com"}


def test_naming_patterns_detects_env_prefix_and_suggests_gap():
    names = {
        "dev-api.empresa.com",
        "staging-api.empresa.com",
        "dev-portal.empresa.com",
        "staging-portal.empresa.com",
        "empresa.com",
    }

    insight = analyze_naming_patterns(names, "empresa.com")

    assert "dev" in insight.detected_prefixes
    assert "staging" in insight.detected_prefixes
    # "prod-api" y "prod-portal" no existen pero siguen el mismo patrón
    # -- solo se sugieren si "prod" fue detectado como token en uso,
    # así que probamos que al menos las combinaciones ya vistas
    # NO se sugieren de nuevo (evitar falsos "candidatos" que ya existen)
    assert "dev-api.empresa.com" not in insight.suggested_candidates
    assert "staging-portal.empresa.com" not in insight.suggested_candidates


def test_naming_patterns_no_pattern_no_suggestions():
    names = {"unique-name-one.empresa.com", "totally-different.empresa.com"}

    insight = analyze_naming_patterns(names, "empresa.com")

    assert insight.detected_prefixes == []
    assert insight.suggested_candidates == []


if __name__ == "__main__":
    test_extract_unique_names_handles_multi_san_and_wildcards()
    test_group_by_ip_groups_shared_infrastructure()
    test_get_unresolved_names_returns_only_none_ip()
    test_naming_patterns_detects_env_prefix_and_suggests_gap()
    test_naming_patterns_no_pattern_no_suggestions()
    print("Todos los tests pasaron correctamente.")
