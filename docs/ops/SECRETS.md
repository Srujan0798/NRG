# NRG Secrets Management v1.0

## Secrets Requiring Rotation

| Secret | Location | Rotation Procedure |
|--------|----------|-------------------|
| JWT_SECRET | .env | `openssl rand -base64 32` |
| SECRET_KEY | .env.production | `openssl rand -hex 32` |
| POSTGRES_PASSWORD | .env | Generate and update in Docker secrets |
| API Keys | Cloud provider | Revoke and regenerate |

## Rotation Procedure

```bash
# 1. Generate new secrets
openssl rand -base64 32 > new_jwt_secret
openssl rand -hex 32 > new_secret_key

# 2. Store in secret manager
# (HashiCorp Vault, AWS Secrets Manager, etc.)

# 3. Update CI/CD
# Update environment variables in CI

# 4. Rollout
make down
make bootstrap
make up
```

## Emergency Rollback

```bash
# Revert to previous secrets
git revert "secrets rotation commit"
make down && make up
```

## Monitoring

- Gitleaks pre-commit hook blocks new commits
- CI job `secrets-scan` runs gitleaks detect
- Alert on any finding above CRITICAL

---

*See docs/ops/SECRETS.md for the rotation runbook.*