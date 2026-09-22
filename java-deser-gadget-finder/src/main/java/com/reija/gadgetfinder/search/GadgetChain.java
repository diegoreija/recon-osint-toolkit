package com.reija.gadgetfinder.search;

import com.reija.gadgetfinder.callgraph.MethodNode;
import com.reija.gadgetfinder.sinks.SinkCatalog;

import java.util.List;

/**
 * Representa una cadena de gadgets completa: desde un punto de entrada de
 * deserialización hasta un sink peligroso, pasando por los métodos
 * intermedios que forman el camino en el grafo de llamadas.
 */
public record GadgetChain(
        List<MethodNode> path,           // en orden: [entryPoint, ..., sinkMethod]
        SinkCatalog.Sink sink,
        int depth                        // longitud de la cadena -- cadenas más cortas son más fiables/explotables
) {

    public MethodNode entryPoint() {
        return path.get(0);
    }

    public String humanReadableChain() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < path.size(); i++) {
            if (i > 0) sb.append(" -> ");
            sb.append(path.get(i).humanReadable());
        }
        return sb.toString();
    }
}
