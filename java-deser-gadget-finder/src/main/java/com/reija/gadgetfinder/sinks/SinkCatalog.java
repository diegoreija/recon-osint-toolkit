package com.reija.gadgetfinder.sinks;

import java.util.Set;

/**
 * Catálogo de "sinks": métodos que, si son alcanzables desde un punto de
 * entrada de deserialización, representan impacto real (RCE, carga de
 * clases arbitraria, acceso a ficheros).
 *
 * La lista está organizada por categoría de impacto porque el nivel de
 * severidad no es el mismo para todos: Runtime.exec es RCE directo,
 * mientras que un sink de tipo "file read" es solo impacto de confidencialidad.
 * Esta clasificación es la que luego usa el reporte final para priorizar
 * qué cadena mostrar primero.
 */
public final class SinkCatalog {

    public enum Severity {
        CRITICAL_RCE,       // ejecución de comandos/código arbitrario
        HIGH_CLASS_LOADING, // carga dinámica de clases (puede derivar en RCE indirecto)
        MEDIUM_FILE_ACCESS, // lectura/escritura de ficheros arbitraria
        MEDIUM_REFLECTION   // invocación reflexiva genérica -- depende del contexto
    }

    public record Sink(String owner, String methodName, Severity severity, String description) {
    }

    private static final Set<Sink> SINKS = Set.of(
            new Sink("java/lang/Runtime", "exec", Severity.CRITICAL_RCE,
                    "Ejecución directa de comandos del sistema operativo"),
            new Sink("java/lang/ProcessBuilder", "start", Severity.CRITICAL_RCE,
                    "Ejecución directa de comandos del sistema operativo"),
            new Sink("java/lang/ProcessBuilder", "<init>", Severity.CRITICAL_RCE,
                    "Construcción de un proceso del sistema operativo"),

            new Sink("java/lang/reflect/Method", "invoke", Severity.MEDIUM_REFLECTION,
                    "Invocación reflexiva de método arbitrario -- severidad depende de qué método se invoque"),
            new Sink("java/lang/Class", "forName", Severity.HIGH_CLASS_LOADING,
                    "Carga dinámica de una clase arbitraria por nombre"),
            new Sink("java/lang/ClassLoader", "loadClass", Severity.HIGH_CLASS_LOADING,
                    "Carga dinámica de una clase arbitraria a través de un ClassLoader"),
            new Sink("java/lang/ClassLoader", "defineClass", Severity.HIGH_CLASS_LOADING,
                    "Definición de una clase nueva a partir de bytes arbitrarios -- vector directo a RCE"),

            new Sink("java/io/FileOutputStream", "<init>", Severity.MEDIUM_FILE_ACCESS,
                    "Escritura de fichero en una ruta potencialmente controlada por el atacante"),
            new Sink("java/nio/file/Files", "write", Severity.MEDIUM_FILE_ACCESS,
                    "Escritura de fichero mediante la API NIO"),

            new Sink("javax/script/ScriptEngine", "eval", Severity.CRITICAL_RCE,
                    "Evaluación de script arbitrario (Nashorn/JS) -- RCE directo"),
            new Sink("groovy/lang/GroovyShell", "evaluate", Severity.CRITICAL_RCE,
                    "Evaluación de script Groovy arbitrario -- RCE directo, vector clásico de gadgets conocidos")
    );

    public static Set<Sink> all() {
        return SINKS;
    }

    /** Comprueba si (owner, methodName) coincide con algún sink conocido. */
    public static Sink match(String owner, String methodName) {
        for (Sink sink : SINKS) {
            if (sink.owner().equals(owner) && sink.methodName().equals(methodName)) {
                return sink;
            }
        }
        return null;
    }
}
