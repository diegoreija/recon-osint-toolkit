package com.reija.gadgetfinder.callgraph;

import java.util.Objects;

/**
 * Representa un nodo del grafo de llamadas: un método concreto de una clase
 * concreta, identificado por su firma completa (owner + name + descriptor).
 *
 * Por qué se guarda el descriptor y no solo el nombre: en Java el overloading
 * permite varios métodos con el mismo nombre y distintos parámetros. Sin el
 * descriptor, "toString()" y "toString(Object)" colisionarían como si fueran
 * el mismo nodo del grafo, lo que rompería la precisión de la búsqueda de
 * cadenas.
 */
public final class MethodNode {

    private final String owner;      // nombre interno de la clase, ej. "java/lang/Runtime"
    private final String name;       // nombre del método, ej. "exec"
    private final String descriptor; // descriptor JVM, ej. "(Ljava/lang/String;)Ljava/lang/Process;"

    // Marca si este método es alcanzable desde la deserialización directamente
    // (readObject, readResolve, readExternal, finalize) -- son los "entry points"
    // naturales desde los que empieza la búsqueda de cadenas.
    private final boolean isDeserializationEntryPoint;

    public MethodNode(String owner, String name, String descriptor, boolean isDeserializationEntryPoint) {
        this.owner = Objects.requireNonNull(owner);
        this.name = Objects.requireNonNull(name);
        this.descriptor = Objects.requireNonNull(descriptor);
        this.isDeserializationEntryPoint = isDeserializationEntryPoint;
    }

    public String getOwner() {
        return owner;
    }

    public String getName() {
        return name;
    }

    public String getDescriptor() {
        return descriptor;
    }

    public boolean isDeserializationEntryPoint() {
        return isDeserializationEntryPoint;
    }

    /** Identificador único usado como clave en el grafo (owner.name:descriptor). */
    public String id() {
        return owner + "." + name + ":" + descriptor;
    }

    public String humanReadable() {
        return owner.replace('/', '.') + "#" + name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MethodNode)) return false;
        MethodNode that = (MethodNode) o;
        return owner.equals(that.owner) && name.equals(that.name) && descriptor.equals(that.descriptor);
    }

    @Override
    public int hashCode() {
        return Objects.hash(owner, name, descriptor);
    }

    @Override
    public String toString() {
        return id();
    }
}
