# Arquitectura

## Visión general del pipeline

```
JAR de entrada
      │
      ▼
CallGraphBuilder (ASM ClassReader + ClassVisitor + MethodVisitor)
      │  recorre cada .class del JAR, sin cargarlo en la JVM
      ▼
CallGraph
      │  grafo dirigido: nodo = método concreto, arista = "A invoca a B"
      ▼
GadgetSearchEngine (BFS desde cada entry point de deserialización)
      │
      ▼
List<GadgetChain>
      │  ordenadas por profundidad ascendente
      ▼
Reporte por consola (CLI)
```

## Por qué ASM y no reflexión estándar de Java

La reflexión de Java (`Class.forName`, `getDeclaredMethods`, etc.) requiere **cargar** la clase en la JVM para poder inspeccionarla. Eso implica:

- Ejecutar los inicializadores estáticos de la clase (pueden tener efectos secundarios no deseados, o simplemente fallar si faltan dependencias del classpath)
- Necesitar todas las dependencias transitivas resueltas para que la carga no falle
- No poder analizar bytecode de versiones de Java más nuevas que la JVM que ejecuta el analizador

ASM lee el fichero `.class` como **datos binarios puros**, sin ejecutar nada. Esto es exactamente lo que hacen herramientas de análisis estático serias (decompiladores, linters de bytecode, el propio compilador `javac` en ciertas fases) y es la razón por la que se descartó una alternativa más simple basada en parsear la salida de texto de `javap`.

## El algoritmo de búsqueda, paso a paso

### 1. Identificación de entry points

Un "entry point de deserialización" es cualquier método que la especificación de serialización de Java invoca automáticamente en algún momento del ciclo de vida de un objeto deserializado:

| Método | Cuándo se invoca |
|---|---|
| `readObject` | Deserialización personalizada de un `Serializable` |
| `readResolve` | Sustitución de la instancia tras deserializar |
| `readExternal` | Deserialización de un `Externalizable` |
| `finalize` | Invocado por el recolector de basura (vector del gadget clásico `CommonsCollections1`) |
| `hashCode` / `equals` | Invocado implícitamente si el objeto acaba en un `HashMap`/`HashSet` tras deserializar |
| `toString` | Invocado en logging/depuración — vector documentado en varias CVEs reales |

Estos se marcan en el momento de construir el grafo (`CallGraphBuilder`), comparando el nombre del método contra este catálogo fijo.

### 2. Construcción del grafo

Por cada `.class` del JAR:
- Se usa `ClassReader` de ASM para leer el bytecode
- Un `ClassVisitor` personalizado captura el nombre de la clase actual
- Por cada método, un `MethodVisitor` intercepta las instrucciones `INVOKEVIRTUAL`, `INVOKESTATIC`, `INVOKESPECIAL` e `INVOKEINTERFACE` — cada una de estas instrucciones se traduce directamente en una arista del grafo

Un `.class` corrupto o con una versión de bytecode no soportada no aborta el análisis completo: se registra un aviso y se continúa con el resto (ver `CallGraphBuilder.buildFromJar`).

### 3. Búsqueda de cadenas (BFS)

Para cada entry point encontrado, se ejecuta un BFS (búsqueda en anchura) siguiendo las aristas del grafo hacia adelante. Se eligió BFS sobre DFS de forma deliberada:

- BFS garantiza encontrar el camino **más corto** primero
- Una cadena más corta tiene menos condiciones intermedias que puedan fallar en la práctica (casts, genéricos, valores nulos) — es más fiable de convertir en un payload real
- Se acota la profundidad máxima (`maxDepth`, 12 por defecto) para evitar explosión combinatoria en grafos grandes; las cadenas de gadgets documentadas en CVEs reales raramente superan los 8-10 saltos

Cuando el BFS llega a un nodo que coincide con algún sink del catálogo (`SinkCatalog`), se registra la cadena completa y se sigue explorando — el mismo entry point puede alcanzar varios sinks distintos por caminos diferentes, y todos interesan.

### 4. Clasificación por severidad

Cada sink tiene una severidad asignada (`CRITICAL_RCE`, `HIGH_CLASS_LOADING`, `MEDIUM_FILE_ACCESS`, `MEDIUM_REFLECTION`), documentada en `SinkCatalog`. Esto permite que el reporte final priorice lo que de verdad importa: una cadena hacia `Runtime.exec` pesa mucho más que una hacia una escritura de fichero.

## Limitaciones conocidas del algoritmo actual

- **No resuelve polimorfismo dinámico de forma completa.** Si un método llama a una interfaz o clase abstracta, el grafo actual registra la arista contra la firma de la interfaz, no contra todas las implementaciones concretas posibles. Esto puede hacer que se pierdan cadenas que solo son visibles siguiendo la implementación real en tiempo de ejecución. Está documentado como mejora futura (ver Roadmap en el README).
- **No verifica tipos de forma completa a lo largo de la cadena.** El grafo conecta métodos por nombre+descriptor, pero no simula el flujo de datos real (qué objeto concreto se pasa de un método a otro). Esto significa que algunas cadenas reportadas pueden no ser explotables en la práctica sin una verificación manual adicional — la herramienta reduce drásticamente el espacio de búsqueda, no sustituye la validación final por un humano.
- **No genera el payload serializado final.** Encuentra y reporta la cadena; construir el objeto Java serializado que la dispare de verdad es un paso manual posterior (o una futura fase del proyecto, ver `payload_generator/` en la estructura).
