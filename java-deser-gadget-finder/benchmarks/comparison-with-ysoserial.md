# Comparativa con ysoserial

| Aspecto | ysoserial | java-deser-gadget-finder |
|---|---|---|
| Enfoque | Payloads predefinidos por librería conocida | Descubrimiento automático mediante análisis de grafo |
| Cobertura | ~20 librerías con payload documentado | Cualquier JAR, sin lista previa |
| Qué hace si la librería no está en su lista | Nada — no hay payload disponible | Analiza el classpath real y busca en él |
| Salida | Un payload serializado listo para usar | Una cadena documentada (owner, método, orden de llamadas) hacia un sink clasificado por severidad |
| Requiere conocer la cadena de antemano | Sí, está hardcodeada por el autor de cada payload | No — la cadena es el resultado del análisis, no una entrada |
| Genera el objeto serializado final | Sí | No en esta versión (ver Roadmap del README) |

## Cuándo usar cada una

`ysoserial` sigue siendo la herramienta correcta cuando el classpath objetivo usa una de las librerías que ya tiene payload documentado — es más rápida y no requiere análisis previo.

`java-deser-gadget-finder` aporta valor en el caso que `ysoserial` no cubre: un classpath con librerías propias, poco comunes, o combinaciones no documentadas, donde no existe un payload listo y la alternativa sería buscar el gadget a mano con un decompilador.

En la práctica, ambas son complementarias: esta herramienta reduce el espacio de búsqueda manual a un puñado de cadenas candidatas; construir el payload final para una cadena nueva sigue siendo trabajo del investigador (o una futura fase de este mismo proyecto).
