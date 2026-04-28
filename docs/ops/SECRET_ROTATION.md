# NRG Secrets Rotation Runbook

## Emergency Rotation Procedure

### Step 1: Generate New Secrets

```bash
# Generate new JWT_SECRET (32+ bytes; preferred helper)
python scripts/rotate_jwt_secret.py --output new_jwt_secret.env

# Or generate manually
openssl rand -base64 32 > new_jwt_secret

# Generate new SECRET_KEY  
openssl rand -hex 32 > new_secret_key

# Generate new POSTGRES_PASSWORD
openssl rand -base64 24 > new_postgres_password
```

### Step 2: Update Secret Manager

Store in your chosen secret manager:
- **Option A**: HashiCorp Vault
- **Option B**: AWS Secrets Manager
- **Option C**: Azure Key Vault
- **Option D**: 1Password

For HashiCorp Vault, write the generated JWT secret to `jwt_secret`:

```bash
vault kv patch secret/data/nrg/production jwt_secret="$(cut -d= -f2 new_jwt_secret.env)"
```

The API refuses to start when `JWT_ALGORITHM=HS256` and `JWT_SECRET` is shorter
than 32 bytes. Verify committed placeholders before rollout:

```bash
python scripts/check_jwt_secret_config.py
```

### Step 3: Update CI/CD

```bash
# Update GitHub Secrets
gh secret set JWT_SECRET --body "$(cat new_jwt_secret)"
gh secret set SECRET_KEY --body "$(cat new_secret_key)"
```

### Step 4: Rollout

```bash
make down
git pull
make bootstrap
make up
make seed
```

### Step 5: Verify

```bash
# Test login works
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Check auth secret health without exposing the secret value
curl -s http://localhost:8000/health | jq '.auth_status'
```

### Step 6: Revoke Old Secrets

After 24 hours, remove old secrets from secret manager.

---

## Monitoring

- **Gitleaks**: Runs on every commit
- **CI Job**: `secrets-scan` in CI pipeline
- **Alert**: Any finding > INFO triggers failure

---

## Contacts

| Role | Contact |
|------|---------|
| Security Lead | security@nrg.org.in |
| On-Call | oncall@nrg.org.in |
