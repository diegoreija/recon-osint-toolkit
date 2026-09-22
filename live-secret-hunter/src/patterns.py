"""
patterns.py
-----------
Catálogo de patrones de secretos conocidos. Cada patrón lleva asociado
no solo la regex de detección, sino el TIPO de servicio al que
pertenece -- eso es lo que permite después decidir CÓMO verificar si
sigue vivo (cada servicio tiene su propio endpoint de validación).

Por qué no basta con "esto parece una clave": una regex que detecta
"algo con forma de API key" genera muchísimo ruido (falsos positivos
de hashes, IDs de sesión, etc.). Acotar el patrón al formato exacto
de cada proveedor conocido reduce ese ruido de forma significativa.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Pattern


class SecretType(Enum):
    AWS_ACCESS_KEY = "aws_access_key"
    GOOGLE_API_KEY = "google_api_key"
    STRIPE_KEY = "stripe_key"
    GITHUB_TOKEN = "github_token"
    SLACK_TOKEN = "slack_token"
    SENDGRID_KEY = "sendgrid_key"
    GENERIC_JWT = "generic_jwt"
    FIREBASE_URL = "firebase_url"


@dataclass
class SecretPattern:
    secret_type: SecretType
    regex: Pattern
    description: str


# Los patrones están acotados al formato REAL documentado por cada
# proveedor (prefijos fijos, longitud, charset), no a "cualquier
# string alfanumérico largo" -- eso es lo que diferencia esto de un
# grep genérico.
PATTERNS: List[SecretPattern] = [
    SecretPattern(
        secret_type=SecretType.AWS_ACCESS_KEY,
        regex=re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        description="AWS Access Key ID",
    ),
    SecretPattern(
        secret_type=SecretType.GOOGLE_API_KEY,
        regex=re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b"),
        description="Google API Key",
    ),
    SecretPattern(
        secret_type=SecretType.STRIPE_KEY,
        regex=re.compile(r"\b(sk_live_[0-9a-zA-Z]{24,})\b"),
        description="Stripe Secret Key (live)",
    ),
    SecretPattern(
        secret_type=SecretType.GITHUB_TOKEN,
        regex=re.compile(r"\b(ghp_[0-9A-Za-z]{36})\b"),
        description="GitHub Personal Access Token",
    ),
    SecretPattern(
        secret_type=SecretType.SLACK_TOKEN,
        regex=re.compile(r"\b(xox[baprs]-[0-9A-Za-z\-]{10,})\b"),
        description="Slack Token",
    ),
    SecretPattern(
        secret_type=SecretType.SENDGRID_KEY,
        regex=re.compile(r"\b(SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43})\b"),
        description="SendGrid API Key",
    ),
    SecretPattern(
        secret_type=SecretType.GENERIC_JWT,
        regex=re.compile(r"\b(eyJ[0-9A-Za-z_\-]+\.eyJ[0-9A-Za-z_\-]+\.[0-9A-Za-z_\-]+)\b"),
        description="JSON Web Token",
    ),
    SecretPattern(
        secret_type=SecretType.FIREBASE_URL,
        regex=re.compile(r"\b([a-z0-9\-]+\.firebaseio\.com)\b"),
        description="Firebase Realtime Database URL",
    ),
]
