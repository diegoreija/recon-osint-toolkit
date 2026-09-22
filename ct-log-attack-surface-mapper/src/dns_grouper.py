"""
dns_grouper.py
--------------
Resuelve cada nombre extraído de los certificados a su IP (si sigue
teniendo DNS activo) y agrupa los nombres por IP compartida.

Por qué agrupar por IP: dos subdominios que no tienen ninguna
relación aparente por su nombre (ej. "api-legacy.empresa.com" y
"partner-portal.empresa.com") pueden estar en el mismo host físico
o el mismo balanceador. Verlos agrupados revela que pertenecen al
mismo bloque de infraestructura, algo que mirar los nombres uno a
uno no muestra.
"""

import socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ResolvedName:
    name: str
    ip: Optional[str]  # None si no resuelve (candidato a "histórico")


@dataclass
class IPGroup:
    ip: str
    names: List[str] = field(default_factory=list)


def resolve_names(names: set, timeout_seconds: float = 2.0) -> List[ResolvedName]:
    """
    Resuelve cada nombre a IP. Los wildcards puros (ej. "*.empresa.com")
    no son resolubles directamente y se omiten de la resolución --
    se conservan solo como parte del listado de nombres, no del mapeo
    por IP.
    """
    socket.setdefaulttimeout(timeout_seconds)
    resolved = []

    for name in sorted(names):
        if name.startswith("*."):
            continue
        try:
            ip = socket.gethostbyname(name)
        except (socket.gaierror, socket.timeout):
            ip = None
        resolved.append(ResolvedName(name=name, ip=ip))

    return resolved


def group_by_ip(resolved_names: List[ResolvedName]) -> List[IPGroup]:
    """Agrupa los nombres que resolvieron correctamente por IP compartida."""
    groups: Dict[str, IPGroup] = {}

    for rn in resolved_names:
        if rn.ip is None:
            continue
        if rn.ip not in groups:
            groups[rn.ip] = IPGroup(ip=rn.ip)
        groups[rn.ip].names.append(rn.name)

    # Ordenamos por número de nombres compartidos (descendente) --
    # las IPs con más nombres agrupados suelen ser infraestructura
    # compartida (balanceador, CDN, hosting compartido) y son las
    # más interesantes de revisar primero.
    return sorted(groups.values(), key=lambda g: len(g.names), reverse=True)


def get_unresolved_names(resolved_names: List[ResolvedName]) -> List[str]:
    """
    Nombres que aparecieron en certificados pero ya no resuelven --
    candidatos a infraestructura histórica/shadow IT. No implica que
    estén "vivos" de otra forma (podrían resolver en DNS interno,
    o simplemente haber sido dados de baja del todo); es una pista,
    no una confirmación.
    """
    return [rn.name for rn in resolved_names if rn.ip is None]
