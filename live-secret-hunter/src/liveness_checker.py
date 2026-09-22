"""
liveness_checker.py
--------------------
Por cada secreto encontrado, hace UNA llamada de solo lectura al
endpoint de validación oficial del proveedor correspondiente para
comprobar si el secreto sigue siendo válido.

Esto es lo que diferencia el proyecto de un grep con regex: un
secreto encontrado en un bundle JS puede llevar meses rotado y ser
papel mojado. Sin verificar liveness, un informe de pentest reporta
ruido. Con verificación, se reporta impacto real.

Reglas de diseño importantes:
- Cada check usa el endpoint MÁS INOFENSIVO posible del proveedor
  (ej. "whoami"/"get caller identity", nunca un endpoint que liste
  datos de negocio ni que modifique nada).
- Ningún check escribe, borra ni modifica nada -- todos son de
  solo lectura y de la superficie mínima necesaria para confirmar
  validez.
- Si un proveedor no tiene un checker implementado, se marca como
  "no verificable" en vez de asumir nada.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests

from patterns import SecretType
from extractor import FoundSecret


class LivenessStatus(Enum):
    LIVE = "live"
    DEAD = "dead"
    UNKNOWN = "unknown"  # el proveedor no tiene checker o la llamada falló por red


@dataclass
class VerifiedSecret:
    finding: FoundSecret
    status: LivenessStatus
    detail: str


def _check_github_token(token: str) -> VerifiedSecret:
    """
    GET /user con el token -- endpoint de solo lectura que confirma
    identidad sin exponer ni modificar nada del repositorio.
    """
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            username = response.json().get("login", "unknown")
            return LivenessStatus.LIVE, f"Token válido, autenticado como '{username}'"
        elif response.status_code == 401:
            return LivenessStatus.DEAD, "Token inválido o revocado (401)"
        else:
            return LivenessStatus.UNKNOWN, f"Respuesta inesperada: {response.status_code}"
    except requests.RequestException as exc:
        return LivenessStatus.UNKNOWN, f"Error de red: {exc}"


def _check_stripe_key(key: str) -> tuple:
    """
    GET /v1/balance -- endpoint de solo lectura estándar para
    verificar credenciales de Stripe sin acceder a datos de clientes.
    """
    try:
        response = requests.get(
            "https://api.stripe.com/v1/balance",
            auth=(key, ""),
            timeout=10,
        )
        if response.status_code == 200:
            return LivenessStatus.LIVE, "Clave válida, acceso confirmado a /v1/balance"
        elif response.status_code == 401:
            return LivenessStatus.DEAD, "Clave inválida o revocada (401)"
        else:
            return LivenessStatus.UNKNOWN, f"Respuesta inesperada: {response.status_code}"
    except requests.RequestException as exc:
        return LivenessStatus.UNKNOWN, f"Error de red: {exc}"


def _check_sendgrid_key(key: str) -> tuple:
    """GET /v3/scopes -- lista los permisos de la key sin enviar ningún email."""
    try:
        response = requests.get(
            "https://api.sendgrid.com/v3/scopes",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        if response.status_code == 200:
            return LivenessStatus.LIVE, "Clave válida, acceso confirmado a /v3/scopes"
        elif response.status_code == 401:
            return LivenessStatus.DEAD, "Clave inválida o revocada (401)"
        else:
            return LivenessStatus.UNKNOWN, f"Respuesta inesperada: {response.status_code}"
    except requests.RequestException as exc:
        return LivenessStatus.UNKNOWN, f"Error de red: {exc}"


def _check_firebase_url(url: str) -> tuple:
    """
    GET a la raíz de la Realtime Database con .json -- si las reglas
    de seguridad son públicas, devuelve datos; si no, un error de
    permisos. Esto NO es "hackear" nada: es literalmente comprobar
    si la base de datos ya está configurada como públicamente legible,
    que es justo el misconfig que se quiere detectar.
    """
    try:
        response = requests.get(f"https://{url}/.json", timeout=10)
        if response.status_code == 200 and response.text.strip() != "null":
            return LivenessStatus.LIVE, "La base de datos responde con datos accesibles públicamente"
        elif response.status_code in (401, 403):
            return LivenessStatus.DEAD, "Acceso denegado -- reglas de seguridad correctamente configuradas"
        else:
            return LivenessStatus.UNKNOWN, f"Respuesta inesperada: {response.status_code}"
    except requests.RequestException as exc:
        return LivenessStatus.UNKNOWN, f"Error de red: {exc}"


# Registro de checkers disponibles. Los tipos que no aparecen aquí
# (AWS, Google API Key, Slack, JWT genérico) no tienen verificación
# automática en esta versión -- ver README, sección de limitaciones,
# para el porqué de cada caso.
_CHECKERS = {
    SecretType.GITHUB_TOKEN: _check_github_token,
    SecretType.STRIPE_KEY: _check_stripe_key,
    SecretType.SENDGRID_KEY: _check_sendgrid_key,
    SecretType.FIREBASE_URL: _check_firebase_url,
}


def verify_secret(finding: FoundSecret) -> VerifiedSecret:
    """Verifica un secreto individual usando el checker apropiado, si existe."""
    checker = _CHECKERS.get(finding.secret_type)

    if checker is None:
        return VerifiedSecret(
            finding=finding,
            status=LivenessStatus.UNKNOWN,
            detail="No hay checker automático implementado para este tipo de secreto",
        )

    status, detail = checker(finding.value)
    return VerifiedSecret(finding=finding, status=status, detail=detail)


def verify_all(findings: list) -> list:
    """Verifica una lista de FoundSecret y devuelve la lista de VerifiedSecret."""
    return [verify_secret(f) for f in findings]
