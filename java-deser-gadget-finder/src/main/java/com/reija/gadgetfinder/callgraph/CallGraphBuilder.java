package com.reija.gadgetfinder.callgraph;

import org.objectweb.asm.*;

import java.io.*;
import java.util.*;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

/**
 * Construye un CallGraph completo a partir de un JAR, usando el
 * ClassVisitor/MethodVisitor de ASM para recorrer el bytecode de cada
 * método sin necesidad de cargar (ejecutar) ninguna clase.
 *
 * Esto es la diferencia clave frente a un enfoque basado en reflexión de
 * Java estándar: la reflexión requiere CARGAR la clase en la JVM (con
 * todos los riesgos y limitaciones que eso implica -- dependencias que
 * faltan, inicializadores estáticos con efectos secundarios). Con ASM se
 * lee el bytecode como datos puros, sin ejecutar nada.
 */
public final class CallGraphBuilder {

    // Nombres de método que la especificación de serialización de Java
    // invoca automáticamente durante el proceso de deserialización.
    // Son los puntos de entrada naturales para cualquier cadena de gadgets.
    private static final Set<String> DESERIALIZATION_ENTRY_METHODS = Set.of(
            "readObject",       // Serializable personalizado
            "readObjectNoData",
            "readResolve",      // sustitución de la instancia tras deserializar
            "readExternal",     // Externalizable
            "finalize",         // invocado por el GC, abusable en algunas cadenas clásicas
            "hashCode",         // invocado implícitamente si el objeto entra en un HashMap/HashSet
            "equals",
            "toString"          // invocado en logging/depuración, vector real en varias CVEs
    );

    public CallGraph buildFromJar(File jarFile) throws IOException {
        CallGraph graph = new CallGraph();

        try (JarFile jar = new JarFile(jarFile)) {
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (!entry.getName().endsWith(".class")) {
                    continue;
                }
                try (InputStream is = jar.getInputStream(entry)) {
                    analyzeClass(is, graph);
                } catch (Exception e) {
                    // Un .class corrupto o con versión de bytecode no soportada
                    // no debe tumbar el análisis completo del JAR -- se registra
                    // y se continúa con el resto de clases.
                    System.err.println("[WARN] No se pudo analizar " + entry.getName() + ": " + e.getMessage());
                }
            }
        }

        return graph;
    }

    private void analyzeClass(InputStream classBytes, CallGraph graph) throws IOException {
        ClassReader reader = new ClassReader(classBytes);
        reader.accept(new GraphBuildingClassVisitor(graph), ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
    }

    /** ClassVisitor que, por cada método de la clase, delega en un MethodVisitor que registra las llamadas. */
    private static final class GraphBuildingClassVisitor extends ClassVisitor {
        private final CallGraph graph;
        private String currentClassInternalName;

        GraphBuildingClassVisitor(CallGraph graph) {
            super(Opcodes.ASM9);
            this.graph = graph;
        }

        @Override
        public void visit(int version, int access, String name, String signature, String superName, String[] interfaces) {
            this.currentClassInternalName = name;
        }

        @Override
        public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
            boolean isEntryPoint = DESERIALIZATION_ENTRY_METHODS.contains(name);
            MethodNode callerNode = new MethodNode(currentClassInternalName, name, descriptor, isEntryPoint);
            graph.addNode(callerNode);

            return new MethodVisitor(Opcodes.ASM9) {
                @Override
                public void visitMethodInsn(int opcode, String owner, String calleeName, String calleeDescriptor, boolean isInterface) {
                    // Cada instrucción INVOKEVIRTUAL/INVOKESTATIC/INVOKESPECIAL/INVOKEINTERFACE
                    // es una arista real del grafo: "este método llama a ese otro".
                    boolean calleeIsEntryPoint = DESERIALIZATION_ENTRY_METHODS.contains(calleeName);
                    MethodNode calleeNode = new MethodNode(owner, calleeName, calleeDescriptor, calleeIsEntryPoint);
                    graph.addEdge(callerNode, calleeNode);
                }
            };
        }
    }
}
