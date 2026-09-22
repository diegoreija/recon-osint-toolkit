# java-deser-gadget-finder

Análisis estático de bytecode Java que construye un grafo de llamadas a partir de un JAR y **descubre automáticamente** cadenas de gadgets de deserialización explotables, en lugar de depender de una lista fija de payloads para librerías ya conocidas.

---

## Motivación

Herramientas como `ysoserial` son el estándar para explotar deserialización insegura en Java, y funcionan muy bien contra el conjunto de librerías que ya tienen un payload documentado (Commons Collections, Spring, Groovy, Hibernate...). El problema aparece cuando el classpath objetivo usa una combinación de librerías que no está en esa lista: `ysoserial` no ofrece nada, y encontrar el gadget pasa a ser trabajo manual con un decompilador, buscando a ojo qué clases serializables terminan invocando algo peligroso.

Este proyecto automatiza esa búsqueda manual. Dado un JAR, construye el grafo completo de llamadas entre métodos y recorre ese grafo desde cada punto de entrada de deserialización (`readObject`, `readResolve`, `finalize`...) hasta encontrar cualquier camino que llegue a un sink peligroso (`Runtime.exec`, `ProcessBuilder`, carga dinámica de clases...). El resultado es un descubrimiento de gadgets nuevo, no la reproducción de uno ya documentado.

| `ysoserial` y herramientas equivalentes | `java-deser-gadget-finder` |
|---|---|
| Payloads fijos para ~20 librerías conocidas | Analiza cualquier JAR, sin lista previa |
| No aporta nada si la librería no está en su catálogo | Construye el grafo real de esa librería concreta y busca en él |
| Requiere saber de antemano qué cadena usar | Descubre la cadena, si existe |

---

## Cómo funciona (resumen)

```
JAR ──► ASM (lectura de bytecode) ──► CallGraph ──► BFS desde entry points ──► Cadenas encontradas
```

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para el detalle completo del algoritmo, las decisiones de diseño y las limitaciones conocidas.

En una frase: se lee el bytecode de cada clase con **ASM** (sin ejecutar nada, sin cargar las clases en la JVM), se construye un grafo dirigido donde cada arista es una instrucción `INVOKE*` real, y se hace una búsqueda en anchura desde cada método que la especificación de serialización de Java invoca automáticamente, hasta encontrar un sink peligroso alcanzable.

---

## Requisitos

- Java 17 o superior (JDK, no solo JRE)
- Maven 3.8+
- Acceso a Maven Central para resolver las dependencias (ASM, JCommander, JUnit 5)

## Compilación

```bash
git clone https://github.com/diegoreija/java-deser-gadget-finder.git
cd java-deser-gadget-finder
mvn clean package
```

Esto genera `target/gadget-finder.jar`, un JAR ejecutable con todas las dependencias incluidas (vía `maven-shade-plugin`).

## Uso

```bash
java -jar target/gadget-finder.jar --jar <ruta-al-jar-objetivo>
```

| Opción | Descripción |
|---|---|
| `--jar` | Ruta al JAR a analizar. Obligatorio |
| `--max-depth` | Profundidad máxima de búsqueda en el grafo (por defecto 12) |
| `--stats-only` | Solo muestra estadísticas del grafo construido, sin ejecutar la búsqueda |

```bash
java -jar target/gadget-finder.jar --jar examples/commons-collections-demo/target/demo.jar
```

Ver [`examples/sample_run.md`](examples/sample_run.md) para una salida completa comentada, incluyendo la reproducción de un gadget ya conocido como validación de que el algoritmo funciona correctamente.

---

## Estructura del repositorio

```
.
├── pom.xml
├── docs/
│   └── ARCHITECTURE.md          Detalle del algoritmo y decisiones de diseño
├── src/main/java/com/reija/gadgetfinder/
│   ├── classpath/                (carga de JARs -- ver CallGraphBuilder)
│   ├── callgraph/
│   │   ├── MethodNode.java       Nodo del grafo: un método identificado por owner+name+descriptor
│   │   ├── CallGraph.java        Grafo dirigido con listas de adyacencia
│   │   └── CallGraphBuilder.java Construcción del grafo a partir de bytecode real (ASM)
│   ├── sinks/
│   │   └── SinkCatalog.java      Catálogo de métodos peligrosos, clasificados por severidad
│   ├── search/
│   │   ├── GadgetChain.java      Modelo de una cadena encontrada
│   │   └── GadgetSearchEngine.java  BFS desde cada entry point hasta cada sink alcanzable
│   └── cli/
│       └── Main.java             Punto de entrada y presentación del reporte
├── src/test/java/...              Tests unitarios de cada componente
├── examples/
│   └── sample_run.md
└── benchmarks/
    └── comparison-with-ysoserial.md
```

---

## Decisiones de diseño

- **BFS, no DFS.** Garantiza encontrar el camino más corto primero. Una cadena corta tiene menos condiciones intermedias (casts, genéricos, nulls) que puedan romper el payload real — se prioriza lo más fiable de explotar, no solo lo primero que se encuentra.
- **Deduplicación por sink, no por camino.** Desde un mismo entry point, solo se conserva la cadena más corta hacia cada sink distinto. Esto evita saturar el reporte con variantes redundantes del mismo hallazgo.
- **Un fallo al parsear una clase no aborta el análisis completo.** Un `.class` corrupto o con una versión de bytecode no soportada se registra como aviso y se continúa con el resto — el objetivo es maximizar la cobertura del análisis sobre un JAR real, que puede tener de todo.
- **Catálogo de sinks clasificado por severidad**, no una lista plana. Permite que el reporte priorice lo que de verdad importa (RCE directo) por encima de hallazgos de impacto menor (lectura de fichero).

## Tests

```bash
mvn test
```

La parte más importante está en `GadgetSearchEngineTest`: los grafos de prueba se construyen **a mano**, simulando lo que `CallGraphBuilder` generaría a partir de bytecode real. Esto permite verificar la corrección del algoritmo de búsqueda (camino más corto, límite de profundidad, múltiples sinks desde un mismo entry point, ausencia de falso positivo cuando no hay camino) de forma completamente aislada del parseo de bytecode.

---

## Limitaciones

- No resuelve polimorfismo dinámico de forma completa (ver `docs/ARCHITECTURE.md` para el detalle).
- No simula flujo de datos entre métodos — las cadenas encontradas reducen drásticamente el espacio de búsqueda, pero no sustituyen la validación manual final de que el payload es realmente construible.
- No genera el objeto serializado final que dispara la cadena; ese paso queda para el investigador, con la cadena ya localizada como guía.
- El catálogo de sinks (`SinkCatalog`) es una lista curada, no exhaustiva — ampliarla es la mejora más directa a corto plazo.

## Roadmap

- [ ] Resolución de polimorfismo: seguir aristas hacia todas las implementaciones conocidas de una interfaz/clase abstracta, no solo la firma declarada
- [ ] Generador de payload (`payload_generator/`): construir automáticamente el objeto serializado a partir de una cadena encontrada
- [ ] Ampliar `SinkCatalog` con sinks específicos de frameworks comunes (Spring, Hibernate)
- [ ] Modo de análisis de classpath completo (varios JARs a la vez, no solo uno)

---

## Uso responsable

Esta herramienta realiza análisis estático puro: lee bytecode, no ejecuta código del JAR analizado ni interactúa con ningún sistema en red. Aun así, las cadenas que encuentre solo deben usarse para construir pruebas de concepto dentro de un engagement autorizado o contra software propio.

## Licencia

MIT. Ver [LICENSE](LICENSE).

## Autor

Diego Reija López · [GitHub](https://github.com/diegoreija) · [LinkedIn](https://linkedin.com/in/diegoreijalopez)
