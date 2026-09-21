# live-secret-hunter

Extrae secretos expuestos en bundles JavaScript de producción y **verifica si siguen activos** consultando el endpoint de solo lectura oficial de cada proveedor, en vez de limitarse a señalar que "algo parece una clave".

---

## Motivación

Herramientas como TruffleHog o GitLeaks son excelentes detectando patrones de secretos en código. Su limitación no está en la detección, sino en lo que ocurre después: devuelven un hallazgo y ahí termina el trabajo automático. Alguien tiene que comprobar manualmente si esa clave sigue siendo válida o si ya fue rotada hace meses.

Esa comprobación es la que decide si un hallazgo es papel mojado o un `critical` real en un informe. Este proyecto la automatiza: por cada secreto detectado, ejecuta una única llamada de solo lectura al endpoint de validación oficial del proveedor correspondiente (whoami, balance, scopes...) para confirmar su estado.

| Lo que hacen los scanners estándar | Lo que añade este proyecto |
|---|---|
| Detectan el patrón de una clave | Detectan el patrón **y** comprueban si sigue siendo válida |
| Resultado: "posible secreto encontrado" | Resultado: activo / inactivo / no verificable, con detalle |
| Todo hallazgo pesa igual en el informe | Los hallazgos activos se pueden priorizar de forma objetiva |

---

## Funcionamiento

```
 URLs de bundles JS
   │
   ▼
 Descarga (extractor.py)
   │
   ▼
 Detección de patrones (patterns.py) ► lista de FoundSecret con contexto
   │
   ▼
 Verificación de liveness (liveness_checker.py) ► una llamada de solo lectura por secreto
   │
   ▼
 Clasificación final: activo / inactivo / no verificable
```

1. **Descarga.** Cada URL de JS indicada se descarga vía HTTP; los fallos de red se ignoran de forma silenciosa (no interrumpen el resto del escaneo).
2. **Detección.** Se aplican patrones acotados al formato real de cada proveedor (prefijos fijos, longitud, charset), no expresiones genéricas tipo "cadena alfanumérica larga" — eso reduce el ruido de falsos positivos desde el principio.
3. **Verificación.** Cada tipo de secreto con checker implementado se valida contra el endpoint más inofensivo posible de su proveedor. Ningún check escribe, modifica o borra nada.
4. **Clasificación.** Los resultados se agrupan en activos, inactivos y no verificables, en ese orden de prioridad en la salida.

---

## Proveedores soportados

| Proveedor | Detección | Verificación de liveness |
|---|---|---|
| GitHub (PAT) | ✅ | ✅ `GET /user` |
| Stripe (clave live) | ✅ | ✅ `GET /v1/balance` |
| SendGrid | ✅ | ✅ `GET /v3/scopes` |
| Firebase Realtime DB | ✅ | ✅ `GET /.json` (detecta reglas de seguridad públicas) |
| AWS Access Key | ✅ | ⚠️ No implementado (ver Limitaciones) |
| Google API Key | ✅ | ⚠️ No implementado |
| Slack Token | ✅ | ⚠️ No implementado |
| JWT genérico | ✅ | ⚠️ No aplica (no hay endpoint de validación universal) |

---

## Requisitos

- Python 3.10 o superior
- Acceso a internet, tanto al target (para descargar los JS) como a los endpoints de los proveedores (para verificación)

## Instalación

```bash
git clone https://github.com/diegoreija/live-secret-hunter.git
cd live-secret-hunter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python3 src/main.py --url <url-del-js> [--url <otra-url> ...] [--no-verify]
python3 src/main.py --url-list <fichero-con-urls>
```

| Opción | Descripción |
|---|---|
| `--url` | URL de un fichero JS a escanear. Repetible |
| `--url-list` | Fichero de texto con una URL por línea |
| `--no-verify` | Solo extrae, sin verificar liveness (ninguna llamada a terceros) |

Ver [`examples/sample_run.md`](examples/sample_run.md) para una salida completa comentada.

---

## Estructura del repositorio

```
.
├── src/
│   ├── patterns.py           Catálogo de patrones de secretos por proveedor
│   ├── extractor.py          Descarga de JS y extracción con contexto
│   ├── liveness_checker.py   Verificación de validez contra cada proveedor
│   └── main.py                Orquestación del pipeline y salida por consola
├── tests/
│   └── test_pipeline.py
├── examples/
│   └── sample_run.md
├── requirements.txt
├── LICENSE
└── README.md
```

## Decisiones de diseño

- **Patrones acotados al formato real de cada proveedor**, no regex genéricas. Reduce falsos positivos frente a un grep de "algo que parece una clave".
- **Cada checker usa el endpoint más inofensivo del proveedor** (identidad/balance/scopes), nunca uno que liste datos de negocio o modifique estado. La justificación de cada elección está en el docstring del checker correspondiente.
- **Proveedores sin checker se marcan como "no verificable"**, nunca se asume su estado. Es preferible un resultado incompleto a uno incorrecto.
- **Tests con mocks para las verificaciones de liveness.** Ningún test hace una llamada HTTP real — se simulan las respuestas de la API para poder probar la lógica de clasificación sin depender de credenciales reales ni de red.

## Tests

```bash
python3 tests/test_pipeline.py
```

Cubren extracción de patrones (incluyendo el caso de no generar falso positivo sobre una cadena alfanumérica cualquiera), inclusión de contexto, y los tres resultados posibles de verificación (activo, inactivo, sin checker, error de red) usando mocks.

---

## Limitaciones

- **AWS Access Key, Google API Key y Slack Token no tienen checker automático en esta versión.** Verificar una AWS key exige credenciales STS y expone más superficie de la deseable para un check "inofensivo" por defecto; Google API Key y Slack requieren decidir contra qué API concreta probar, lo cual varía según el scope de la clave. Quedan en el roadmap.
- **JWT genérico** se detecta pero no se verifica: no existe un endpoint de validación universal para JWTs, depende por completo del emisor.
- La detección se basa en patrones conocidos; un secreto con formato no estándar o de un proveedor no catalogado no se detecta.
- Los ficheros JS se descargan tal cual; si están minificados de forma agresiva o el secreto está ofuscado/concatenado en tiempo de ejecución, puede no aparecer en el texto fuente.

## Roadmap

- [ ] Checker para AWS Access Key vía `sts:GetCallerIdentity`
- [ ] Checker para Slack Token vía `auth.test`
- [ ] Modo de rastreo automático de bundles JS a partir de una URL raíz (en vez de listarlos a mano)
- [ ] Exportación de resultados a JSON para integrarlo en otros pipelines

---

## Uso responsable

Esta herramienta descarga contenido público y, en el paso de verificación, realiza llamadas de solo lectura a APIs de terceros usando credenciales encontradas en código de producción. Aunque cada check está diseñado para ser mínimamente invasivo, sigue siendo una interacción con sistemas ajenos: úsala únicamente sobre targets para los que tengas autorización explícita, y ten en cuenta que muchos programas de bug bounty tienen normas específicas sobre el uso de credenciales encontradas — revisa el scope antes de verificar nada.

## Licencia

MIT. Ver [LICENSE](LICENSE).

## Autor

Diego Reija López · [GitHub](https://github.com/diegoreija) · [LinkedIn](https://linkedin.com/in/diegoreijalopez)
