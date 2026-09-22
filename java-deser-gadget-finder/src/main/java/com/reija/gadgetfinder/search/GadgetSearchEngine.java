package com.reija.gadgetfinder.search;

import com.reija.gadgetfinder.callgraph.CallGraph;
import com.reija.gadgetfinder.callgraph.MethodNode;
import com.reija.gadgetfinder.sinks.SinkCatalog;

import java.util.*;

/**
 * Motor de búsqueda: para cada entry point de deserialización del grafo,
 * hace un BFS hacia adelante (siguiendo las aristas de "quién llama a
 * quién") hasta encontrar el primer sink peligroso alcanzable.
 *
 * Por qué BFS y no DFS: BFS garantiza encontrar el camino MÁS CORTO
 * primero. Una cadena de gadgets más corta es más fiable de construir
 * como payload real (menos condiciones intermedias que puedan fallar:
 * tipos genéricos, casts, nulls) -- así que priorizar profundidad mínima
 * es una decisión de diseño deliberada, no solo de eficiencia algorítmica.
 *
 * Límite de profundidad: sin límite, un grafo con miles de métodos podría
 * generar una explosión combinatoria de caminos irrelevantes (cadenas de
 * 40 saltos que en la práctica nunca serían explotables). Se acota a
 * MAX_DEPTH configurable, con 12 como valor por defecto -- las cadenas de
 * gadgets reales documentadas en CVEs raramente superan los 8-10 saltos.
 */
public final class GadgetSearchEngine {

    private final CallGraph graph;
    private final int maxDepth;

    public GadgetSearchEngine(CallGraph graph, int maxDepth) {
        this.graph = graph;
        this.maxDepth = maxDepth;
    }

    public GadgetSearchEngine(CallGraph graph) {
        this(graph, 12);
    }

    /**
     * Busca todas las cadenas de gadgets encontradas, una por cada
     * combinación (entry point, sink) donde exista un camino en el grafo.
     * Se deduplica por entry point: solo se conserva la cadena más corta
     * hacia CADA sink distinto desde ese entry point.
     */
    public List<GadgetChain> findAllChains() {
        List<GadgetChain> results = new ArrayList<>();

        for (MethodNode entryPoint : graph.entryPoints()) {
            results.addAll(bfsFromEntryPoint(entryPoint));
        }

        // Ordenar por profundidad ascendente: las cadenas más cortas
        // (más fiables de explotar en la práctica) van primero en el reporte.
        results.sort(Comparator.comparingInt(GadgetChain::depth));
        return results;
    }

    private List<GadgetChain> bfsFromEntryPoint(MethodNode entryPoint) {
        List<GadgetChain> found = new ArrayList<>();
        Set<String> sinksAlreadyFoundForThisEntry = new HashSet<>();

        Queue<List<String>> queue = new ArrayDeque<>(); // cada elemento es el camino (lista de ids) hasta ese nodo
        Set<String> visited = new HashSet<>();

        queue.add(List.of(entryPoint.id()));
        visited.add(entryPoint.id());

        while (!queue.isEmpty()) {
            List<String> currentPath = queue.poll();
            if (currentPath.size() > maxDepth) {
                continue;
            }

            String currentId = currentPath.get(currentPath.size() - 1);
            MethodNode currentNode = graph.getNode(currentId);
            if (currentNode == null) continue;

            // ¿El nodo actual ES un sink conocido? -- comprobamos por owner+name,
            // ya que el descriptor exacto puede variar por overloads del sink.
            SinkCatalog.Sink matchedSink = SinkCatalog.match(currentNode.getOwner(), currentNode.getName());
            if (matchedSink != null && !currentId.equals(entryPoint.id())) {
                String sinkKey = matchedSink.owner() + "." + matchedSink.methodName();
                if (!sinksAlreadyFoundForThisEntry.contains(sinkKey)) {
                    sinksAlreadyFoundForThisEntry.add(sinkKey);
                    List<MethodNode> resolvedPath = resolvePath(currentPath);
                    found.add(new GadgetChain(resolvedPath, matchedSink, resolvedPath.size() - 1));
                }
                // No cortamos el BFS aquí: el mismo entry point puede llegar
                // a OTROS sinks distintos por otros caminos.
                continue;
            }

            for (String calleeId : graph.callees(currentId)) {
                if (!visited.contains(calleeId)) {
                    visited.add(calleeId);
                    List<String> newPath = new ArrayList<>(currentPath);
                    newPath.add(calleeId);
                    queue.add(newPath);
                }
            }
        }

        return found;
    }

    private List<MethodNode> resolvePath(List<String> idPath) {
        List<MethodNode> resolved = new ArrayList<>();
        for (String id : idPath) {
            MethodNode node = graph.getNode(id);
            if (node != null) {
                resolved.add(node);
            }
        }
        return resolved;
    }
}
