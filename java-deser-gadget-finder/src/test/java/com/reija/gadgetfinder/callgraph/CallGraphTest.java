package com.reija.gadgetfinder.callgraph;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class CallGraphTest {

    @Test
    void addEdgeRegistersBothDirections() {
        CallGraph graph = new CallGraph();
        MethodNode a = new MethodNode("com/example/A", "foo", "()V", false);
        MethodNode b = new MethodNode("com/example/B", "bar", "()V", false);

        graph.addEdge(a, b);

        assertTrue(graph.callees(a.id()).contains(b.id()));
        assertTrue(graph.callers(b.id()).contains(a.id()));
    }

    @Test
    void entryPointsReturnsOnlyMarkedNodes() {
        CallGraph graph = new CallGraph();
        MethodNode normal = new MethodNode("com/example/A", "foo", "()V", false);
        MethodNode entry = new MethodNode("com/example/B", "readObject", "(Ljava/io/ObjectInputStream;)V", true);

        graph.addNode(normal);
        graph.addNode(entry);

        assertEquals(1, graph.entryPoints().size());
        assertEquals(entry.id(), graph.entryPoints().get(0).id());
    }

    @Test
    void nodeCountAndEdgeCountAreAccurate() {
        CallGraph graph = new CallGraph();
        MethodNode a = new MethodNode("com/example/A", "foo", "()V", false);
        MethodNode b = new MethodNode("com/example/B", "bar", "()V", false);
        MethodNode c = new MethodNode("com/example/C", "baz", "()V", false);

        graph.addEdge(a, b);
        graph.addEdge(a, c);
        graph.addEdge(b, c);

        assertEquals(3, graph.nodeCount());
        assertEquals(3, graph.edgeCount());
    }

    @Test
    void methodNodeDistinguishesOverloadsByDescriptor() {
        MethodNode overloadA = new MethodNode("com/example/A", "toString", "()Ljava/lang/String;", false);
        MethodNode overloadB = new MethodNode("com/example/A", "toString", "(I)Ljava/lang/String;", false);

        assertNotEquals(overloadA, overloadB);
        assertNotEquals(overloadA.id(), overloadB.id());
    }
}
