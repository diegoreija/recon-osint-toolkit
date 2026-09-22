package com.reija.gadgetfinder.sinks;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SinkCatalogTest {

    @Test
    void matchesKnownRceSink() {
        SinkCatalog.Sink result = SinkCatalog.match("java/lang/Runtime", "exec");

        assertNotNull(result);
        assertEquals(SinkCatalog.Severity.CRITICAL_RCE, result.severity());
    }

    @Test
    void doesNotMatchUnknownMethod() {
        SinkCatalog.Sink result = SinkCatalog.match("com/example/Innocuous", "doNothing");

        assertNull(result);
    }

    @Test
    void distinguishesSeverityLevelsAcrossCatalog() {
        boolean hasCritical = SinkCatalog.all().stream()
                .anyMatch(s -> s.severity() == SinkCatalog.Severity.CRITICAL_RCE);
        boolean hasClassLoading = SinkCatalog.all().stream()
                .anyMatch(s -> s.severity() == SinkCatalog.Severity.HIGH_CLASS_LOADING);

        assertTrue(hasCritical);
        assertTrue(hasClassLoading);
    }

    @Test
    void matchIsExactOnOwnerAndMethodName() {
        // mismo nombre de método, distinta clase -- no debe dar falso positivo
        SinkCatalog.Sink result = SinkCatalog.match("com/example/MyRuntime", "exec");

        assertNull(result);
    }
}
