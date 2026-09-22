#!/usr/bin/env python3
"""
main.py
-------
Orquestador: descarga los JS indicados, extrae secretos con los
patrones conocidos y verifica cuáles siguen vivos.

Uso:
    python3 main.py --url https://target.com/static/main.js
    python3 main.py --url-list urls.txt
    python3 main.py --url https://target.com/main.js --no-verify
"""

import argparse
import sys

from extractor import scan_urls
from liveness_checker import verify_all, LivenessStatus


def load_urls_from_file(path: str) -> list:
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Extrae secretos de bundles JS de producción y verifica si siguen activos"
    )
    parser.add_argument("--url", action="append", help="URL de un fichero JS (repetible)")
    parser.add_argument("--url-list", help="Fichero con una URL de JS por línea")
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Solo extrae secretos, sin verificar si siguen activos (más rápido, menos llamadas salientes)",
    )
    args = parser.parse_args()

    urls = list(args.url) if args.url else []
    if args.url_list:
        urls.extend(load_urls_from_file(args.url_list))

    if not urls:
        print("Debes indicar al menos --url o --url-list")
        sys.exit(1)

    print(f"[1/2] Descargando y escaneando {len(urls)} fichero(s) JS...")
    findings = scan_urls(urls)
    print(f"      -> {len(findings)} posibles secretos encontrados")

    if not findings:
        print("No se encontraron secretos con los patrones conocidos. Fin.")
        sys.exit(0)

    if args.no_verify:
        print("\nSecretos encontrados (sin verificar, --no-verify activo):\n")
        for f in findings:
            print(f"  [{f.secret_type.value}] {f.source_url}")
            print(f"      valor: {f.value}")
            print(f"      contexto: ...{f.context}...\n")
        return

    print("[2/2] Verificando si cada secreto sigue activo (endpoints de solo lectura)...\n")
    verified = verify_all(findings)

    live = [v for v in verified if v.status == LivenessStatus.LIVE]
    dead = [v for v in verified if v.status == LivenessStatus.DEAD]
    unknown = [v for v in verified if v.status == LivenessStatus.UNKNOWN]

    if live:
        print("=" * 70)
        print(f"🔴 SECRETOS ACTIVOS ({len(live)}) -- impacto real, priorizar")
        print("=" * 70)
        for v in live:
            print(f"\n[{v.finding.secret_type.value}] {v.finding.source_url}")
            print(f"    valor: {v.finding.value}")
            print(f"    estado: {v.detail}")

    if unknown:
        print("\n" + "=" * 70)
        print(f"⚪ SIN VERIFICACIÓN AUTOMÁTICA ({len(unknown)}) -- revisar manualmente")
        print("=" * 70)
        for v in unknown:
            print(f"\n[{v.finding.secret_type.value}] {v.finding.source_url}")
            print(f"    valor: {v.finding.value}")
            print(f"    motivo: {v.detail}")

    if dead:
        print("\n" + "=" * 70)
        print(f"⚫ SECRETOS INACTIVOS ({len(dead)}) -- ya rotados/revocados")
        print("=" * 70)
        for v in dead:
            print(f"    [{v.finding.secret_type.value}] {v.finding.source_url}")


if __name__ == "__main__":
    main()
