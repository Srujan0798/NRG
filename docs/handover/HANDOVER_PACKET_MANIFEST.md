# Handover Packet Manifest

**Target output:** `NRG_HANDOVER_2026-05-xx.zip`  
**Status:** Draft manifest. Do not create the final zip until P7-H and P8-B pass.

## Required Contents

| Item | Source path | Status |
|---|---|---|
| Signed production audit report | `docs/audits/NRG_PRODUCTION_AUDIT_2026-04-27.md.asc` | Pending GPG |
| Researcher UAT transcript | `evidence/2026-05-xx/uat_transcript_researcher.md` | Pending live UAT |
| Government UAT transcript | `evidence/2026-05-xx/uat_transcript_government.md` | Pending live UAT |
| Industry UAT transcript | `evidence/2026-05-xx/uat_transcript_industry.md` | Pending live UAT |
| Acceptance recording hash | `docs/handover/evidence/04_demo.sha256` | Template present |
| Helm charts | `infrastructure/helm/` | Present |
| Docker Compose files | `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.dev.yml` | Present |
| DPDP attestation | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` | Present, unsigned |
| Signed eternal tag proof | `git tag -v v1.0.0-eternal` output | Blocked, existing tag unsigned |
| Use-of-funds document | `docs/business/USE_OF_FUNDS_12_MONTH_2026-04-27.md` | Present |
| GPG signature manifest | `docs/handover/signatures/SIGNATURE_MANIFEST.md` | Present, pending signatures |

## Final Packaging Command

Run only after every row above is complete:

```bash
zip -r NRG_HANDOVER_2026-05-xx.zip \
  docs/audits/NRG_PRODUCTION_AUDIT_2026-04-27.md* \
  docs/handover \
  docs/business/USE_OF_FUNDS_12_MONTH_2026-04-27.md \
  evidence/2026-05-xx \
  infrastructure/helm \
  docker-compose.yml docker-compose.prod.yml docker-compose.dev.yml
```
