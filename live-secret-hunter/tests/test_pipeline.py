"""
Tests de extracción de patrones (sin red) y de verificación de
liveness usando mocks (sin llamadas HTTP reales -- nunca se debe
llamar a APIs reales de terceros durante los tests).
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from patterns import SecretType
from extractor import scan_content, FoundSecret
from liveness_checker import verify_secret, LivenessStatus, _check_github_token, _check_stripe_key


def test_scan_content_detects_github_token():
    content = "const config = { token: 'ghp_123456789012345678901234567890123456' };"
    findings = scan_content(content, "https://example.com/app.js")

    github_findings = [f for f in findings if f.secret_type == SecretType.GITHUB_TOKEN]
    assert len(github_findings) == 1
    assert github_findings[0].value.startswith("ghp_")


def test_scan_content_detects_aws_key():
    content = "AWS_KEY=AKIAABCDEFGHIJKLMNOP"
    findings = scan_content(content, "https://example.com/app.js")

    aws_findings = [f for f in findings if f.secret_type == SecretType.AWS_ACCESS_KEY]
    assert len(aws_findings) == 1
    assert aws_findings[0].value == "AKIAABCDEFGHIJKLMNOP"


def test_scan_content_no_false_positive_on_random_string():
    content = "const id = 'user-1234567890-session-abcdef';"
    findings = scan_content(content, "https://example.com/app.js")

    assert len(findings) == 0


def test_scan_content_includes_context():
    content = "// api config\nconst k = 'AKIAABCDEFGHIJKLMNOP'; // do not commit"
    findings = scan_content(content, "https://example.com/app.js")

    assert len(findings) == 1
    assert "AKIAABCDEFGHIJKLMNOP" in findings[0].context


def test_verify_secret_live_github_token():
    finding = FoundSecret(
        secret_type=SecretType.GITHUB_TOKEN,
        value="ghp_fake",
        source_url="https://example.com/app.js",
        context="...",
    )

    with patch("liveness_checker.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_get.return_value = mock_response

        result = verify_secret(finding)

    assert result.status == LivenessStatus.LIVE
    assert "testuser" in result.detail


def test_verify_secret_dead_github_token():
    finding = FoundSecret(
        secret_type=SecretType.GITHUB_TOKEN,
        value="ghp_fake",
        source_url="https://example.com/app.js",
        context="...",
    )

    with patch("liveness_checker.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        result = verify_secret(finding)

    assert result.status == LivenessStatus.DEAD


def test_verify_secret_unknown_type_has_no_checker():
    finding = FoundSecret(
        secret_type=SecretType.AWS_ACCESS_KEY,
        value="AKIAABCDEFGHIJKLMNOP",
        source_url="https://example.com/app.js",
        context="...",
    )

    result = verify_secret(finding)

    assert result.status == LivenessStatus.UNKNOWN
    assert "no hay checker" in result.detail.lower() or "no checker" in result.detail.lower()


def test_verify_secret_network_error_returns_unknown():
    finding = FoundSecret(
        secret_type=SecretType.GITHUB_TOKEN,
        value="ghp_fake",
        source_url="https://example.com/app.js",
        context="...",
    )

    with patch("liveness_checker.requests.get") as mock_get:
        import requests
        mock_get.side_effect = requests.RequestException("connection error")

        result = verify_secret(finding)

    assert result.status == LivenessStatus.UNKNOWN


if __name__ == "__main__":
    test_scan_content_detects_github_token()
    test_scan_content_detects_aws_key()
    test_scan_content_no_false_positive_on_random_string()
    test_scan_content_includes_context()
    test_verify_secret_live_github_token()
    test_verify_secret_dead_github_token()
    test_verify_secret_unknown_type_has_no_checker()
    test_verify_secret_network_error_returns_unknown()
    print("Todos los tests pasaron correctamente.")
