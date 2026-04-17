# NRG Threat Model (STRIDE)

## Overview
Threat model for National Research Graph using STRIDE methodology.

---

## Spoofing
| Threat | Mitigation |
|--------|------------|
| Impersonating valid users | Role-based access control |
| API key theft | Secret rotation, env vars only |

---

## Tampering
| Threat | Mitigation |
|--------|------------|
| SQL injection attempts | Sandbox enforces SELECT-only |
| Vector payload tampering | Read-only Qdrant role |
| State manipulation | Immutable audit trail |

---

## Repudiation
| Threat | Mitigation |
|--------|------------|
| Denying query execution | Full audit logging |
| Data deletion | Immutable logs |

---

## Information Disclosure
| Threat | Mitigation |
|--------|------------|
| Schema leaked to LLM | Metadata-only prompt |
| Raw data exfiltration | Read-only sandbox |
| Vector results leak | Tier-based filtering |

---

## Denial of Service
| Threat | Mitigation |
|--------|------------|
| Query flooding | Rate limiting |
| Vector DB exhaustion | Collection size limits |

---

## Elevation of Privilege
| Threat | Mitigation |
|--------|------------|
| Tier escalation | Database-level enforcement |
| Admin access | Separate credentials |

---

## Risk Matrix

| Category | Phase 1 Risk | Phase 2 Risk |
|----------|--------------|--------------|
| Spoofing | LOW | MEDIUM |
| Tampering | LOW | LOW |
| Repudiation | LOW | LOW |
| Info Disclosure | LOW | MEDIUM |
| DoS | MEDIUM | MEDIUM |
| Elevation | LOW | LOW |

---

## Security Controls

1. **Network**: Egress monitoring
2. **Application**: RBAC, sandbox
3. **Database**: Read-only role
4. **Audit**: Full logging