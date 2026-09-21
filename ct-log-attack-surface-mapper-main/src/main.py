#!/usr/bin/env python3
"""
main.py
-------
Orquestador del pipeline:

    1. ct_client consulta crt.sh y extrae todos los nombres históricos
    2. dns_grouper resuelve cada nombre y agrupa por IP compartida
    3. naming_patterns detecta convenciones y sugiere candidatos no vistos

Todo el proceso es pasivo: no se lanza ningún escaneo activo contra
el dominio objetivo, solo consultas a crt.sh y resolución DNS estándar.

Uso:
    python3 main.py --domain empresa.com
    python3 main.py --domain empresa.com --show-unresolved
"""

import argparse
import sys

from ct_client import fetch_certificates, extract_unique_names
from dns_grouper import resolve_names, group_by_ip, get_unresolved_names
from naming_patterns import analyze_naming_patterns


def main():
    parser = argparse.ArgumentParser(
        description="Mapea la superficie de ataque de un dominio a partir de Certificate Transparency logs"
    )
    parser.add_argument("--domain", required=True, help="Dominio raíz a analizar (ej. empresa.com)")
    parser.add_argument(
        "--show-unresolved",
        action="store_true",
        help="Muestra también los nombres que aparecieron en certificados pero ya no resuelven",
    )
    args = parser.parse_args()
    domain = args.domain.strip().lower()

    print(f"[1/3] Consultando crt.sh para *.{domain}...")
    try:
        entries = fetch_certificates(domain)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    names = extract_unique_names(entries)
    print(f"      -> {len(entries)} certificados encontrados, {len(names)} nombres únicos extraídos")

    if not names:
        print("No se encontraron nombres. Fin.")
        sys.exit(0)

    print("[2/3] Resolviendo nombres y agrupando por IP compartida...")
    resolved = resolve_names(names)
    ip_groups = group_by_ip(resolved)
    unresolved = get_unresolved_names(resolved)
    print(f"      -> {len(ip_groups)} IPs distintas, {len(unresolved)} nombres sin resolución activa")

    print("[3/3] Analizando patrones de naming...\n")
    insight = analyze_naming_patterns(names, domain)

    print("=" * 70)
    print("INFRAESTRUCTURA AGRUPADA POR IP (top 10 por nº de nombres)")
    print("=" * 70)
    for group in ip_groups[:10]:
        print(f"\n{group.ip}  ({len(group.names)} nombres)")
        for name in group.names[:8]:
            print(f"    - {name}")
        if len(group.names) > 8:
            print(f"    ... y {len(group.names) - 8} más")

    if args.show_unresolved and unresolved:
        print("\n" + "=" * 70)
        print(f"NOMBRES SIN RESOLUCIÓN ACTIVA ({len(unresolved)}) -- candidatos históricos")
        print("=" * 70)
        for name in unresolved[:20]:
            print(f"    - {name}")
        if len(unresolved) > 20:
            print(f"    ... y {len(unresolved) - 20} más")

    print("\n" + "=" * 70)
    print("PATRONES DE NAMING DETECTADOS")
    print("=" * 70)
    print(f"Prefijos frecuentes: {', '.join(insight.detected_prefixes) or '(ninguno con suficiente frecuencia)'}")
    print(f"Sufijos frecuentes:  {', '.join(insight.detected_suffixes) or '(ninguno con suficiente frecuencia)'}")

    if insight.suggested_candidates:
        print(f"\nCandidatos sugeridos ({len(insight.suggested_candidates)}, basados en patrones reales del dominio):")
        for candidate in insight.suggested_candidates[:15]:
            print(f"    - {candidate}")
        if len(insight.suggested_candidates) > 15:
            print(f"    ... y {len(insight.suggested_candidates) - 15} más")
    else:
        print("\nNo se detectaron suficientes patrones para sugerir candidatos.")


if __name__ == "__main__":
    main()
