package com.reija.gadgetfinder.cli;

import com.beust.jcommander.JCommander;
import com.beust.jcommander.Parameter;
import com.reija.gadgetfinder.callgraph.CallGraph;
import com.reija.gadgetfinder.callgraph.CallGraphBuilder;
import com.reija.gadgetfinder.search.GadgetChain;
import com.reija.gadgetfinder.search.GadgetSearchEngine;

import java.io.File;
import java.util.List;

public final class Main {

    static final class Args {
        @Parameter(names = {"--jar"}, required = true, description = "Ruta al JAR a analizar")
        String jarPath;

        @Parameter(names = {"--max-depth"}, description = "Profundidad máxima de búsqueda de cadenas (por defecto 12)")
        int maxDepth = 12;

        @Parameter(names = {"--stats-only"}, description = "Solo muestra estadísticas del grafo, sin buscar cadenas")
        boolean statsOnly = false;
    }

    public static void main(String[] rawArgs) {
        Args args = new Args();
        JCommander.newBuilder().addObject(args).build().parse(rawArgs);

        File jarFile = new File(args.jarPath);
        if (!jarFile.exists()) {
            System.err.println("Error: no existe el fichero " + args.jarPath);
            System.exit(1);
        }

        System.out.println("[1/3] Analizando bytecode y construyendo el grafo de llamadas...");
        CallGraph graph;
        try {
            graph = new CallGraphBuilder().buildFromJar(jarFile);
        } catch (Exception e) {
            System.err.println("Error analizando el JAR: " + e.getMessage());
            System.exit(1);
            return;
        }

        System.out.printf("      -> %d métodos, %d llamadas registradas, %d entry points de deserialización%n",
                graph.nodeCount(), graph.edgeCount(), graph.entryPoints().size());

        if (args.statsOnly) {
            return;
        }

        System.out.println("[2/3] Buscando cadenas de gadgets (BFS desde cada entry point)...");
        GadgetSearchEngine engine = new GadgetSearchEngine(graph, args.maxDepth);
        List<GadgetChain> chains = engine.findAllChains();
        System.out.printf("      -> %d cadena(s) de gadgets encontradas%n%n", chains.size());

        System.out.println("[3/3] Resultado:");
        System.out.println("=".repeat(90));

        if (chains.isEmpty()) {
            System.out.println("No se encontraron cadenas hacia ningún sink conocido dentro de la profundidad configurada.");
            System.out.println("Prueba a aumentar --max-depth si el classpath es muy grande.");
            return;
        }

        for (GadgetChain chain : chains) {
            System.out.printf("[%s] Sink: %s#%s (%s)%n",
                    chain.sink().severity(),
                    chain.sink().owner().replace('/', '.'),
                    chain.sink().methodName(),
                    chain.sink().description());
            System.out.println("  Cadena (" + chain.depth() + " saltos): " + chain.humanReadableChain());
            System.out.println();
        }
    }
}
