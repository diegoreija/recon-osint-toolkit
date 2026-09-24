# recon-osint-toolkit

A collection of passive reconnaissance and vulnerability prioritization tools, designed for the early phases of an engagement: **discover attack surface, find exposed credentials, and prioritize what to attack first**, all before launching any aggressive active scanning against the target.

---

## How the four projects fit together

```
                    ┌─────────────────────────────┐
                    │  ct-log-attack-surface-mapper │  ← what infrastructure exists?
                    │  (Certificate Transparency)   │     (passive, never touches the target)
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │      live-secret-hunter       │  ← are there exposed credentials
                    │   (production JS + APIs)      │     in what I already found?
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │   web-tech-cve-matcher        │  ← what CVEs affect the exact
                    │  (fingerprinting + NVD+EPSS)  │     versions running here?
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │   exploit-priority-scanner    │  ← of everything found,
                    │  (Nmap + Nuclei + EPSS)       │     what do I attack first?
                    └─────────────────────────────┘
```

Each tool works independently and has its own README with full documentation, but in a real engagement the natural flow is this order: first map what exists without touching anything (CT logs), then check whether that surface already exposes secrets in public code (production JS), then match the exact web technology versions found against known CVEs, and finally, on the active services detected, prioritize by real exploitability.

---

## Projects

### [`exploit-priority-scanner/`](exploit-priority-scanner/)
Correlates Nmap + Nuclei + EPSS to prioritize vulnerabilities by real exploitation probability, not just CVSS severity.

### [`ct-log-attack-surface-mapper/`](ct-log-attack-surface-mapper/)
Maps attack surface from Certificate Transparency logs: groups infrastructure by shared IP and flags historical hostnames with no active DNS. Fully passive reconnaissance.

### [`live-secret-hunter/`](live-secret-hunter/)
Extracts secrets exposed in production JavaScript bundles and verifies whether they're still active by querying each provider's official read-only endpoint.

### [`web-tech-cve-matcher/`](web-tech-cve-matcher/)
Fingerprints web technologies on a URL and matches known CVEs via the official NVD database, ranked by CVSS + EPSS combined.

---

## General requirements

Each subproject has its own `requirements.txt` and README with specific instructions. In common:

- Python 3.10+
- One virtual environment per project (recommended, avoids version conflicts between them)

```bash
cd exploit-priority-scanner   # or whichever project applies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Responsible use

Every tool in this repository is designed for passive or low-impact reconnaissance. Even so, each one interacts to some degree with third-party systems (DNS queries, downloading public files, read-only API calls). Use them only against targets you're explicitly authorized to assess.

## License

MIT for the entire repository. See [LICENSE](LICENSE).

## Author

Diego Reija López · [GitHub](https://github.com/diegoreija) · [LinkedIn](https://linkedin.com/in/diegoreijalopez)
