# Agent Assignments - National Research Graph

## Current Window Status

| Window | Agent | Status | Current Task | Priority |
|--------|-------|--------|--------------|----------|
| W1 | CODEX | Available | Security Gateway Hardening | HIGH |
| W2 | KIMI | Available | Architecture Review | HIGH |
| W3 | GEMINI | Available | Database Deployment | HIGH |
| W4 | GEMINI | Available | Load Testing | MEDIUM |
| W5 | QWEN | Available | Security Audit | MEDIUM |
| W6 | QWEN | Available | UAT Execution | MEDIUM |

---

## Agent Capabilities

### CODEX (High Tier - Subscription)
- Complex integration tasks
- Debugging and error resolution
- Core execution loop
- Security gateway implementation
- Deployment pipeline creation

### KIMI (Balanced Tier)
- System architecture design
- Planning and strategy
- Code structure decisions
- Review and validation
- Documentation

### GEMINI (Free Tier)
- Parallel task execution
- Code generation
- Database operations
- Load testing
- Infrastructure deployment

### QWEN (Free Tier)
- Testing and validation
- Security audits
- UAT execution
- Documentation generation
- Report compilation

---

## Phase 3 Assignments

### Parallel Block 1 (Infrastructure)
| Task ID | Agent | Task | Dependencies |
|---------|-------|------|--------------|
| NRG-P3-GEM-001 | GEMINI-W1 | Database Deployment | None |
| NRG-P3-KIMI-001 | KIMI-W1 | Architecture Review | None |

### Parallel Block 2 (Testing)
| Task ID | Agent | Task | Dependencies |
|---------|-------|------|--------------|
| NRG-P3-CODEX-001 | CODEX-W1 | Gateway Hardening | None |
| NRG-P3-GEM-002 | GEMINI-W2 | Load Testing | GEM-001 |
| NRG-P3-QWEN-001 | QWEN-W1 | Security Audit | GEM-001 |
| NRG-P3-QWEN-002 | QWEN-W2 | UAT Execution | GEM-001 |

### Sequential
| Task ID | Agent | Task | Dependencies |
|---------|-------|------|--------------|
| NRG-P3-CODEX-002 | CODEX-W1 | Deployment Pipeline | All Block 2 |

---

## Cost Optimization Strategy

1. **Use GEMINI/QWEN for parallel tasks** (Free tier)
2. **Reserve CODEX for complex integration** (Subscription)
3. **Use KIMI for architecture decisions** (Balanced)
4. **Batch similar tasks** to reduce context switching

---

## Task Queue

### High Priority
1. Database Deployment (GEMINI-W1)
2. Gateway Hardening (CODEX-W1)
3. Security Audit (QWEN-W1)

### Medium Priority
1. Load Testing (GEMINI-W2)
2. UAT Execution (QWEN-W2)
3. Architecture Review (KIMI-W1)

### Low Priority
1. Deployment Pipeline (CODEX-W1)
2. Documentation Updates

---

## Synchronization Points

1. **SYNC 1**: After infrastructure deployment
2. **SYNC 2**: After all tests passing
3. **SYNC 3**: Before production deployment

---

**Last Updated**: 2026-04-14
