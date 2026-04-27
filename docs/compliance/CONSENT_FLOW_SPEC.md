# NRG Consent Flow Specification

> **Version:** 1.0  
> **Status:** DESIGN READY  
> **DPDP Compliance:** Section 6 (Consent), Section 12-14 (Data Principal Rights)  
> **Owner:** Product / Compliance  

## 1. Consent Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │───→│   Consent    │───→│   Audit     │───→│   Consent   │
│  Action     │    │   Service    │    │   Chain     │    │   Dashboard │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │                  │
        ↓                  ↓                  ↓                  ↓
   Registration      Granular UI       HMAC-signed       Withdrawal
   Login             Checkboxes        immutable log     + re-consent
```

## 2. Consent Types

NRG uses **granular, purpose-specific consent** with 4 independent consent flags:

| Consent ID | Purpose | Default | UI Label |
|-----------|---------|---------|----------|
| `profile_visibility` | Show profile to other researchers | OFF | "Make my profile visible to other researchers" |
| `aggregate_stats` | Include in institutional statistics | ON | "Include my data in anonymous aggregate statistics" |
| `govt_contact` | Contact by government agencies | OFF | "Allow verified government agencies to contact me for policy input" |
| `platform_updates` | Receive newsletters | ON | "Send me platform updates and research newsletters" |

**Rules:**
- All defaults are **opt-in** (OFF) except `aggregate_stats` and `platform_updates`
- No consent is **bundled** with account creation
- Withdrawing `profile_visibility` does NOT delete account
- Withdrawing ALL consents still allows login and personal data access

## 3. User Journey

### 3.1 Registration Flow

```
Step 1: Enter email + password + institution
        ↓
Step 2: Email verification (OTP)
        ↓
Step 3: Privacy Notice (Layer 1 — 1 page summary, 22 languages)
        ↓
Step 4: Granular Consent Checkboxes (4 independent toggles)
        ↓
Step 5: Confirmation page showing what was consented to
        ↓
Step 6: Account created + consent record written to audit chain
```

### 3.2 Layered Privacy Notice

| Layer | Content | Length | Action Required |
|-------|---------|--------|-----------------|
| **Layer 1** | Summary: what data, why, who sees it, your rights | ~300 words | Must scroll to bottom |
| **Layer 2** | Purpose-specific details per consent flag | ~100 words each | Expandable accordion |
| **Layer 3** | Full legal text (this Privacy Notice) | Full document | Link to separate page |

**Language:** Layer 1 available in all 22 scheduled languages of India. Default based on browser Accept-Language.

### 3.3 Consent UI Wireframe

```
┌─────────────────────────────────────────────┐
│  🔒 Your Privacy Choices                     │
│                                              │
│  You control how your data is used.          │
│  You can change these anytime in Settings.   │
│                                              │
│  ☐ Make my profile visible to other          │
│    researchers                               │
│    [ℹ️  Your name, institution, and          │
│         research areas will be searchable]    │
│                                              │
│  ☑ Include my data in anonymous              │
│    aggregate statistics                      │
│    [ℹ️  Counts and averages only — no        │
│         personal identification]              │
│                                              │
│  ☐ Allow verified government agencies        │
│    to contact me for policy input            │
│    [ℹ️  Only for policy research; your       │
│         email is not shared directly]         │
│                                              │
│  ☑ Send me platform updates and              │
│    research newsletters                      │
│    [ℹ️  Max 1 email per week; unsubscribe   │
│         anytime]                              │
│                                              │
│  [Continue]                                  │
│                                              │
│  📄 Full Privacy Notice  |  🌐 हिंदी में    │
└─────────────────────────────────────────────┘
```

## 4. Consent Record Schema

```json
{
  "consent_id": "uuid-v4",
  "user_id": "user-uuid",
  "timestamp": "2026-04-25T12:00:00+05:30",
  "action": "GRANT | WITHDRAW | UPDATE",
  "consents": {
    "profile_visibility": true,
    "aggregate_stats": true,
    "govt_contact": false,
    "platform_updates": true
  },
  "context": {
    "ip_address_hash": "sha256-of-ip",
    "user_agent_hash": "sha256-of-ua",
    "session_id": "session-uuid",
    "ui_version": "consent-v1.0"
  },
  "previous_consents": {
    "profile_visibility": false,
    "aggregate_stats": true,
    "govt_contact": false,
    "platform_updates": true
  },
  "previous_consent_id": "previous-uuid-or-null"
}
```

**Storage:**
- Primary: `consent_log` table in PostgreSQL
- Immutable: HMAC-signed event in audit chain
- Retention: 7 years (legal requirement)

## 5. API Specification

### 5.1 Record Consent

```http
POST /api/v1/consent
Authorization: Bearer {token}
Content-Type: application/json

{
  "consents": {
    "profile_visibility": true,
    "aggregate_stats": true,
    "govt_contact": false,
    "platform_updates": true
  }
}
```

**Response:**
```json
{
  "consent_id": "consent-uuid",
  "timestamp": "2026-04-25T12:00:00+05:30",
  "audit_hash": "sha256-hash-of-event",
  "status": "recorded"
}
```

### 5.2 Get Current Consent

```http
GET /api/v1/me/consents
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": "user-uuid",
  "consents": {
    "profile_visibility": true,
    "aggregate_stats": true,
    "govt_contact": false,
    "platform_updates": true
  },
  "last_updated": "2026-04-25T12:00:00+05:30",
  "consent_history": [
    {"consent_id": "uuid-1", "timestamp": "...", "action": "GRANT"},
    {"consent_id": "uuid-2", "timestamp": "...", "action": "UPDATE"}
  ]
}
```

### 5.3 Withdraw Consent

```http
DELETE /api/v1/consent/{consent_type}
Authorization: Bearer {token}
```

**Example:** `DELETE /api/v1/consent/platform_updates`

**Response:**
```json
{
  "consent_id": "new-uuid",
  "action": "WITHDRAW",
  "withdrawn_consent": "platform_updates",
  "effective_at": "2026-04-25T12:00:00+05:30",
  "audit_hash": "sha256-hash"
}
```

**Immediate effects:**
- `platform_updates` → Unsubscribe from mailing list within 24h
- `profile_visibility` → Profile hidden from search within 1h
- `aggregate_stats` → Excluded from next statistics computation
- `govt_contact` → Flag removed from government-facing directory

## 6. Consent Dashboard (User-Facing)

```
┌─────────────────────────────────────────────┐
│  My Consents                                 │
│                                              │
│  Last updated: 25 Apr 2026, 12:00 PM IST    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │ ✅ Profile Visibility      [Edit]   │    │
│  │    Visible to other researchers     │    │
│  │    Granted: 25 Apr 2026             │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │ ✅ Aggregate Statistics    [Edit]   │    │
│  │    Included in anonymous stats      │    │
│  │    Granted: 25 Apr 2026             │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │ ❌ Government Contact      [Enable] │    │
│  │    Not contactable for policy       │    │
│  │    Withdrawn: 25 Apr 2026           │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  [Download My Data]  [Delete My Account]    │
└─────────────────────────────────────────────┘
```

## 7. Consent Enforcement

### 7.1 Backend Enforcement

```python
# src/auth/consent_middleware.py
from functools import wraps
from fastapi import HTTPException, Depends

REQUIRED_CONSENTS = {
    "profile_visibility": ["/api/v1/researchers/search", "/api/v1/researchers/{id}"],
    "govt_contact": ["/api/v1/govt/directory"],
    "aggregate_stats": [],  # Passive — affects analytics pipeline
    "platform_updates": [],  # Passive — affects mailing list
}

def require_consent(consent_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not current_user.consents.get(consent_type, False):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "CONSENT_REQUIRED",
                        "consent_type": consent_type,
                        "message": f"User has not consented to {consent_type}"
                    }
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage:
@app.get("/api/v1/researchers/search")
@require_consent("profile_visibility")
async def search_researchers(...):
    ...
```

### 7.2 Frontend Enforcement

```typescript
// frontend/src/hooks/useConsent.ts
export function useConsent(consentType: string): boolean {
  const { user } = useAuth();
  return user?.consents?.[consentType] ?? false;
}

// frontend/src/components/ResearcherDirectory.tsx
export function ResearcherDirectory() {
  const hasVisibility = useConsent("profile_visibility");
  
  if (!hasVisibility) {
    return <ConsentPrompt consentType="profile_visibility" />;
  }
  
  return <ResearcherList />;
}
```

## 8. Audit & Compliance

### 8.1 Audit Events

Every consent action generates an audit event:

```json
{
  "event_type": "CONSENT_GRANTED",
  "actor": {"type": "user", "id": "user-uuid", "tier": "academic"},
  "resource": {"type": "consent", "id": "consent-uuid"},
  "action": {
    "verb": "GRANT",
    "detail": "profile_visibility=true, aggregate_stats=true, govt_contact=false, platform_updates=true"
  },
  "context": {
    "ip_hash": "sha256-of-ip",
    "session_id": "session-uuid"
  }
}
```

### 8.2 Compliance Checks

| Check | Frequency | Owner |
|-------|-----------|-------|
| Consent record completeness | Daily | Automated |
| Audit chain integrity | Continuous | Automated |
| Withdrawal response time | Weekly | Compliance |
| Consent UI accessibility | Quarterly | UX |
| DPDP Board reporting | Annual | DPO |

## 9. Parental Consent (Under 18)

For users under 18:

```
Step 1: User indicates age < 18 during registration
        ↓
Step 2: Account created in PENDING state (no data processing)
        ↓
Step 3: Parent/guardian receives email with verification link
        ↓
Step 4: Parent completes separate consent form
        ↓
Step 5: Account activated + parental consent recorded
        ↓
Step 6: Annual re-verification required until age 18
```

**Parental consent record:**
```json
{
  "consent_id": "parental-uuid",
  "minor_user_id": "user-uuid",
  "guardian_name": "Parent Name",
  "guardian_email": "parent@example.com",
  "guardian_phone": "hashed-phone",
  "verification_method": "email_link",
  "verified_at": "2026-04-25T12:00:00+05:30",
  "expires_at": "2027-04-25T12:00:00+05:30"
}
```

## 10. Implementation Checklist

- [ ] Consent UI component (`ConsentForm.tsx`)
- [ ] Consent API endpoints (`POST /consent`, `GET /me/consents`, `DELETE /consent/{type}`)
- [ ] Consent middleware (`require_consent` decorator)
- [ ] Consent dashboard page (`/settings/consents`)
- [ ] Audit chain integration
- [ ] Parental consent workflow
- [ ] Layer 1 privacy notice in 22 languages
- [ ] Email notification on consent change
- [ ] Automated compliance checks
- [ ] DPO review and sign-off
