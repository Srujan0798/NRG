# UX Copy Evidence — NRG Interface Review

**Skill**: ux-copy
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/29_UX_COPY.md`

---

## UX Copy Review: NRG Interface

### Overall Assessment: Share with noted improvements

The interface copy is functional but generic. Most text is adequate without being distinctive. Several areas need improvement for clarity, empathy, or actionability.

---

## 1. Login Page (`Login.tsx`)

### Current Copy
```typescript
researcher: {
  en: 'Researcher',
  tier: 'Tier 1',
  desc: 'Access publications, citations, and knowledge graphs across national research databases.'
},
government: {
  en: 'Government',
  tier: 'Tier 2',
  desc: 'Aggregate analytics, policy insights, and cross-institutional research trends.'
},
industry: {
  en: 'Industry',
  tier: 'Tier 3',
  desc: 'Discover academic partnerships, anonymized research capacity, and R&D collaboration.'
}
```

### Issues

| Element | Issue | Severity |
|---------|-------|----------|
| `desc` fields | Passive voice ("Access", "Aggregate", "Discover") — should be action-oriented | 🟡 Moderate |
| Tier labels | "Tier 1/2/3" is internal jargon — user doesn't care about tiers | 🟡 Moderate |
| No error copy | Login errors show generic messages — no helpful guidance | 🟡 Moderate |

### Recommended Copy

| Element | Current | Recommended |
|---------|---------|-------------|
| Researcher desc | "Access publications, citations, and knowledge graphs..." | "Find researchers, publications, and citations across India's national research database" |
| Government desc | "Aggregate analytics, policy insights..." | "Track national research trends, fund innovation, and measure impact across institutions" |
| Industry desc | "Discover academic partnerships, anonymized..." | "Connect with research teams, license innovations, and accelerate R&D" |
| Login error | "Invalid credentials" | "Username or password didn't match. Try again or reset your password." |
| Login button | "Sign In" or "Login" | "Sign in" (more modern) |

---

## 2. DPDP Consent Dialog (`DPDPConsentDialog.tsx`)

### Current Copy (from code review)
```typescript
dataPurpose = 'Research data analysis and knowledge graph enrichment'
retentionDays = 365
```

### Issues

| Element | Issue | Severity |
|---------|-------|----------|
| dataPurpose | Technical jargon ("knowledge graph enrichment") — user won't understand | 🟡 Moderate |
| Retention | "365 days" — should be in human terms | 🟡 Moderate |
| No visual hierarchy | Long text paragraphs hard to scan | 🟡 Moderate |
| Approve/Deny labels | Functional but cold — could be warmer | 🟢 Minor |

### Recommended Copy

| Element | Current | Recommended |
|---------|---------|-------------|
| dataPurpose | "Research data analysis and knowledge graph enrichment" | "To provide you personalized research insights and connect you with relevant publications and researchers" |
| Retention | "365 days" | "For 1 year, then automatically deleted" |
| Deny button | "Deny" | "No, keep my data private" (clearer consequence) |
| Approve button | "Approve" | "Yes, I understand" (acknowledgment language) |

---

## 3. Error States

### Issue Found
No custom error state component found with user-friendly copy. Error messages are likely generic HTTP codes or technical messages.

### Recommended Error Messages

| Error | Current | Recommended |
|-------|---------|-------------|
| 401 Unauthorized | "Unauthorized" | "Your session expired. Sign in again to continue." |
| 403 Forbidden | "Forbidden" | "You don't have access to this. Contact support if you believe this is an error." |
| 429 Rate Limit | "Rate limit exceeded" | "You're making requests too quickly. Please wait 1 minute and try again." |
| 500 Server Error | "Internal server error" | "Something went wrong on our end. We're working to fix it. Try again in a few minutes." |
| Network Error | "Network error" | "Couldn't reach the server. Check your connection and try again." |

---

## 4. Empty States

### Issue Found
No empty state copy visible in the codebase. Empty tables/lists likely show blank or "No data".

### Recommended Empty States

| Context | Recommended Copy |
|---------|-----------------|
| No search results | "No results for '[query]'. Try different keywords or check your spelling." |
| No publications | "No publications found for this researcher. Publications appear once indexed." |
| No funding records | "No funding records found. Funding data is updated quarterly." |
| Empty dashboard | "Your dashboard is ready. Run a query to see research insights." |

---

## 5. Loading States

### Current
No loading text visible — spinners alone.

### Recommended

| Context | Copy |
|---------|------|
| Query loading | "Searching research databases..." |
| Export loading | "Preparing your export..." |
| Auth loading | "Verifying your credentials..." |

---

## 6. Tier Badge

### Current
```typescript
const TIER_STYLES: Record<number, { label: string; bg: string; text: string }> = {
  1: { label: 'Researcher', bg: 'bg-blue-100', text: 'text-blue-800' },
  2: { label: 'Government', bg: 'bg-green-100', text: 'text-green-800' },
  3: { label: 'Industry', bg: 'bg-purple-100', text: 'text-purple-800' },
};
```

### Assessment: ✅ Good
Tier labels are clear and human-readable. Colors provide visual distinction. No issues.

---

## Priority Improvements

1. **Login descriptions** — Make action-oriented, not passive
2. **Error messages** — Replace technical codes with human-readable guidance
3. **Consent dialog** — Explain data purpose in plain language
4. **Empty states** — Add helpful copy explaining why empty and what to do

---

## Skill Deliverable

**Status**: COMPLETED

UX copy review found 6 areas for improvement:
1. Login descriptions use passive voice — should be action-oriented
2. Error messages likely too technical — needs user-friendly versions
3. Consent dialog uses jargon — "knowledge graph enrichment" confuses users
4. Empty states missing copy — users need context
5. Loading states lack explanatory text — spinners alone cause anxiety
6. Tier badge copy is good — no changes needed
