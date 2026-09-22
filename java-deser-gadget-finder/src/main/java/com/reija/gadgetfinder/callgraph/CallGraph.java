package com.reija.gadgetfinder.callgraph;

import java.util.*;

/**
 * Grafo dirigido de llamadas entre métodos: una arista A -> B significa
 * "el método A invoca al método B en algún punto de su bytecode".
 *
 * Se construye una vez a partir de todas las clases del classpath analizado
 * y luego se reutiliza tanto para la búsqueda de gadgets (search/) como
 * para estadísticas del análisis.
 *
 * Nota de diseño: el grafo se guarda como lista de adyacencia con HashMap
 * de HashSet -- para un JAR mediano (varios miles de métodos) esto entra
 * cómodo en memoria y las búsquedas BFS/DFS son O(V+E), no hace falta
 * nada más sofisticado (grafo en disco, etc.) a esta escala.
 */
public final class CallGraph {

    private final Map<String, MethodNode> nodesById = new HashMap<>();
    private final Map<String, Set<String>> adjacency = new HashMap<>(); // callerId -> calleeIds
    private final Map<String, Set<String>> reverseAdjacency = new HashMap<>(); // calleeId -> callerIds

    public void addNode(MethodNode node) {
        nodesById.putIfAbsent(node.id(), node);
        adjacency.computeIfAbsent(node.id(), k -> new HashSet<>());
        reverseAdjacency.computeIfAbsent(node.id(), k -> new HashSet<>());
    }

    /** Registra que `caller` invoca a `callee`. Ambos nodos deben existir o se registran vacíos. */
    public void addEdge(MethodNode caller, MethodNode callee) {
        addNode(caller);
        addNode(callee);
        adjacency.get(caller.id()).add(callee.id());
        reverseAdjacency.get(callee.id()).add(caller.id());
    }

    public MethodNode getNode(String id) {
        return nodesById.get(id);
    }

    public Collection<MethodNode> allNodes() {
        return nodesById.values();
    }

    public Set<String> callees(String methodId) {
        return adjacency.getOrDefault(methodId, Collections.emptySet());
    }

    public Set<String> callers(String methodId) {
        return reverseAdjacency.getOrDefault(methodId, Collections.emptySet());
    }

    public int nodeCount() {
        return nodesById.size();
    }

    public int edgeCount() {
        return adjacency.values().stream().mapToInt(Set::size).sum();
    }

    public List<MethodNode> entryPoints() {
        List<MethodNode> result = new ArrayList<>();
        for (MethodNode n : nodesById.values()) {
            if (n.isDeserializationEntryPoint()) {
                result.add(n);
            }
        }
        return result;
    }
}
