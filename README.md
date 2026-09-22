# recon-osint-toolkit

Colección de herramientas de reconocimiento pasivo y priorización de vulnerabilidades, pensadas para encajar en las primeras fases de un engagement: **descubrir superficie de ataque, encontrar credenciales expuestas y priorizar qué atacar primero**, todo antes de lanzar ningún escaneo activo agresivo contra el objetivo.

---

## Cómo encajan los tres proyectos

```
                    ┌─────────────────────────────┐
                    │  ct-log-attack-surface-mapper │  ← ¿qué infraestructura existe?
                    │  (Certificate Transparency)   │     (pasivo, sin tocar el target)
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │      live-secret-hunter       │  ← ¿hay credenciales expuestas
                    │   (JS de producción + APIs)   │     en lo que ya encontré?
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │   exploit-priority-scanner    │  ← de todo lo encontrado,
                    │  (Nmap + Nuclei + EPSS)       │     ¿qué ataco primero?
                    └─────────────────────────────┘
```

Cada herramienta funciona de forma independiente y tiene su propio README con documentación completa, pero en un engagement real el flujo natural es este orden: primero mapear qué existe sin tocar nada (CT logs), después revisar si esa superficie ya expone secretos en código público (JS de producción), y por último, sobre los servicios activos detectados, priorizar por explotabilidad real.

---

## Proyectos

### [`exploit-priority-scanner/`](exploit-priority-scanner/)
Correlador de Nmap + Nuclei + EPSS que prioriza vulnerabilidades por probabilidad real de explotación, no solo por severidad CVSS.

### [`ct-log-attack-surface-mapper/`](ct-log-attack-surface-mapper/)
Mapeo de superficie de ataque a partir de Certificate Transparency logs: agrupa infraestructura por IP compartida y detecta nombres históricos sin DNS activo. Reconocimiento completamente pasivo.

### [`live-secret-hunter/`](live-secret-hunter/)
Extrae secretos expuestos en bundles JavaScript de producción y verifica si siguen activos consultando el endpoint de solo lectura oficial de cada proveedor.

---

## Requisitos generales

Cada subproyecto tiene su propio `requirements.txt` y README con instrucciones específicas. En común:

- Python 3.10+
- Un entorno virtual por proyecto (recomendado, evita conflictos de versiones entre ellos)

```bash
cd exploit-priority-scanner   # o el proyecto que corresponda
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso responsable

Todas las herramientas de este repositorio están pensadas para reconocimiento pasivo o de bajo impacto. Aun así, cada una interactúa en algún grado con sistemas ajenos (consultas DNS, descarga de ficheros públicos, llamadas de solo lectura a APIs). Úsalas únicamente sobre objetivos para los que tengas autorización explícita.

## Licencia

MIT para todo el repositorio. Ver [LICENSE](LICENSE).

## Autor

Diego Reija López · [GitHub](https://github.com/diegoreija) · [LinkedIn](https://linkedin.com/in/diegoreijalopez)
