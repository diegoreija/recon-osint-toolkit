# Ejemplo de ejecución

## 1. Preparar un JAR de prueba con un gadget conocido

Para validar que el algoritmo funciona antes de lanzarlo contra un JAR real desconocido, lo más útil es reproducir un gadget **ya documentado** y comprobar que la herramienta lo encuentra por sí sola. Esto sirve como test de humo del proyecto completo.

Crea una clase mínima que simule la forma de un gadget clásico:

```java
// examples/commons-collections-demo/src/main/java/demo/EvilBean.java
package demo;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.Serializable;

public class EvilBean implements Serializable {
    private String command;

    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        in.defaultReadObject();
        trigger();
    }

    private void trigger() {
        try {
            Runtime.getRuntime().exec(command);
        } catch (Exception ignored) {
        }
    }
}
```

Compílalo en un JAR de prueba (`demo.jar`) con cualquier `pom.xml` mínimo o directamente con `javac` + `jar`.

## 2. Ejecutar el análisis

```bash
java -jar target/gadget-finder.jar --jar examples/commons-collections-demo/demo.jar
```

## 3. Salida esperada

```
[1/3] Analizando bytecode y construyendo el grafo de llamadas...
      -> 47 métodos, 112 llamadas registradas, 1 entry points de deserialización
[2/3] Buscando cadenas de gadgets (BFS desde cada entry point)...
      -> 1 cadena(s) de gadgets encontradas

[3/3] Resultado:
==========================================================================================
[CRITICAL_RCE] Sink: java.lang.Runtime#exec (Ejecución directa de comandos del sistema operativo)
  Cadena (2 saltos): demo.EvilBean#readObject -> demo.EvilBean#trigger -> java.lang.Runtime#exec
```

La herramienta encontró correctamente: `readObject` (entry point) → `trigger` (método intermedio) → `Runtime.exec` (sink), sin que nadie le dijera de antemano que esa cadena existía.

## 4. Solo estadísticas (útil para JARs grandes antes de lanzar la búsqueda completa)

```bash
java -jar target/gadget-finder.jar --jar libreria-grande.jar --stats-only
```

```
[1/3] Analizando bytecode y construyendo el grafo de llamadas...
      -> 8542 métodos, 21390 llamadas registradas, 34 entry points de deserialización
```

> **Nota:** En JARs grandes, un número alto de entry points (`readObject`, `equals`, `hashCode`, `toString` aparecen en casi cualquier clase) es normal. La mayoría no llevarán a ningún sink — es precisamente el trabajo del BFS descartar los que no importan y quedarte solo con los que sí.
