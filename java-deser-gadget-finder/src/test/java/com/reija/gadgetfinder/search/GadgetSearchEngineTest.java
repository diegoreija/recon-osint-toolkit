package com.reija.gadgetfinder.search;

import com.reija.gadgetfinder.callgraph.CallGraph;
import com.reija.gadgetfinder.callgraph.MethodNode;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Estos tests construyen grafos de llamadas A MANO, simulando lo que
 * CallGraphBuilder generaría a partir de bytecode real. Esto permite
 * probar la lógica de búsqueda de forma completamente aislada del
 * parseo de bytecode -- si el algoritmo de BFS tiene un bug, se detecta
 * aquí sin necesidad de compilar JARs de prueba.
 */
class GadgetSearchEngineTest {

    @Test
    void findsDirectChainFromEntryPointToKnownSink() {
        CallGraph graph = new CallGraph();

        MethodNode entryPoint = new MethodNode("com/example/Evil", "readObject",
                "(Ljava/io/ObjectInputStream;)V", true);
        MethodNode sink = new MethodNode("java/lang/Runtime", "exec",
                "(Ljava/lang/String;)Ljava/lang/Process;", false);

        graph.addEdge(entryPoint, sink);

        GadgetSearchEngine engine = new GadgetSearchEngine(graph);
        List<GadgetChain> chains = engine.findAllChains();

        assertEquals(1, chains.size());
        assertEquals(1, chains.get(0).depth());
        assertEquals("java/lang/Runtime", chains.get(0).sink().owner());
    }

    @Test
    void findsIndirectChainThroughIntermediateMethods() {
        CallGraph graph = new CallGraph();

        MethodNode entryPoint = new MethodNode("com/example/Evil", "readObject",
                "(Ljava/io/ObjectInputStream;)V", true);
        MethodNode intermediate1 = new MethodNode("com/example/Helper", "process", "()V", false);
        MethodNode intermediate2 = new MethodNode("com/example/Helper", "run", "()V", false);
        MethodNode sink = new MethodNode("java/lang/ProcessBuilder", "start",
                "()Ljava/lang/Process;", false);

        graph.addEdge(entryPoint, intermediate1);
        graph.addEdge(intermediate1, intermediate2);
        graph.addEdge(intermediate2, sink);

        GadgetSearchEngine engine = new GadgetSearchEngine(graph);
        List<GadgetChain> chains = engine.findAllChains();

        assertEquals(1, chains.size());
        assertEquals(3, chains.get(0).depth());
    }

    @Test
    void prefersShortestPathWhenMultipleRoutesExist() {
        CallGraph graph = new CallGraph();

        MethodNode entryPoint = new MethodNode("com/example/Evil", "readObject",
                "(Ljava/io/ObjectInputStream;)V", true);
        MethodNode sink = new MethodNode("java/lang/Runtime", "exec",
                "(Ljava/lang/String;)Ljava/lang/Process;", false);
        MethodNode longRouteStep1 = new MethodNode("com/example/A", "a", "()V", false);
        MethodNode longRouteStep2 = new MethodNode("com/example/B", "b", "()V", false);

        // Camino directo (1 salto) y camino largo (3 saltos) al MISMO sink
        graph.addEdge(entryPoint, sink);
        graph.addEdge(entryPoint, longRouteStep1);
        graph.addEdge(longRouteStep1, longRouteStep2);
        graph.addEdge(longRouteStep2, sink);

        GadgetSearchEngine engine = new GadgetSearchEngine(graph);
        List<GadgetChain> chains = engine.findAllChains();

        // Solo debe reportarse UNA cadena hacia este sink desde este entry point
        // (la más corta, por diseño del BFS con deduplicación por sink)
        long chainsToThisSink = chains.stream()
                .filter(c -> c.sink().owner().equals("java/lang/Runtime"))
                .count();
        assertEquals(1, chainsToThisSink);
        assertEquals(1, chains.get(0).depth());
    }

    @Test
    void doesNotExceedConfiguredMaxDepth() {
        CallGraph graph = new CallGraph();

        MethodNode entryPoint = new MethodNode("com/example/Evil", "readObject",
                "(Ljava/io/ObjectInputStream;)V", true);
        MethodNode sink = new MethodNode("java/lang/Runtime", "exec",
                "(Ljava/lang/String;)Ljava/lang/Process;", false);

        // Cadena artificial de 5 saltos intermedios
        MethodNode prev = entryPoint;
        for (int i = 0; i < 5; i++) {
            MethodNode next = new MethodNode("com/example/Step" + i, "m" + i, "()V", false);
            graph.addEdge(prev, next);
            prev = next;
        }
        graph.addEdge(prev, sink);

        // maxDepth=2 no debería alcanzar a llegar a un sink que está a 6 saltos
        GadgetSearchEngine restrictedEngine = new GadgetSearchEngine(graph, 2);
        assertTrue(restrictedEngine.findAllChains().isEmpty());

        // con profundidad suficiente, sí se encuentra
        GadgetSearchEngine fullEngine = new GadgetSearchEngine(graph, 10);
        assertEquals(1, fullEngine.findAllChains().size());
    }

    @Test
    void returnsEmptyWhenNoPathReachesAnySink() {
        CallGraph graph = new CallGraph();

        MethodNode entryPoint = new MethodNode("com/example/Innocent", "readObject",
                "(Ljava/io/ObjectInputStream;)V", true);
        MethodNode harmless = new MethodNode("com/example/Helper", "logMessage", "()V", false);

        graph.addEdge(entryPoint, harmless);

        GadgetSearchEngine engine = new GadgetSearchEngine(graph);
        assertTrue(engine.findAllChains().isEmpty());
    }

    @Test
    void sameEntryPointCanReachMultipleDistinctSinks() {
        CallGraph graph = new CallGraph();

        MethodNode entryPoint = new MethodNode("com/example/Evil", "readObject",
                "(Ljava/io/ObjectInputStream;)V", true);
        MethodNode sinkExec = new MethodNode("java/lang/Runtime", "exec",
                "(Ljava/lang/String;)Ljava/lang/Process;", false);
        MethodNode sinkClassLoad = new MethodNode("java/lang/Class", "forName",
                "(Ljava/lang/String;)Ljava/lang/Class;", false);

        graph.addEdge(entryPoint, sinkExec);
        graph.addEdge(entryPoint, sinkClassLoad);

        GadgetSearchEngine engine = new GadgetSearchEngine(graph);
        List<GadgetChain> chains = engine.findAllChains();

        assertEquals(2, chains.size());
    }
}
