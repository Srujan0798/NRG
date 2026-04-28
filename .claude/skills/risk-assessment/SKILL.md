---
name: risk-assessment
description: Identify, assess, and mitigate operational risks. Trigger with "what are the risks", "risk assessment", "risk register", "what could go wrong", or when the user is evaluating risks associated with a project, vendor, process, or decision.
---

# /risk-assessment

Identify, assess, and mitigate operational risks.

## Usage

```
/risk-assessment $ARGUMENTS
```

## Workflow

### 1. Identify Risks

- What could go wrong?
- Categorize: operational, technical, financial, legal, reputational
- Source from stakeholders, historical incidents, and external factors

### 2. Assess Impact and Likelihood

For each risk:
- **Impact**: Severity if the risk materializes (1-5)
- **Likelihood**: Probability of occurrence (1-5)
- **Risk score**: Impact × Likelihood

### 3. Prioritize

- High score risks = immediate attention
- Consider velocity (how fast could this escalate)
- Distinguinate inherent vs residual risk

### 4. Define Mitigations

- Preventive controls (reduce likelihood)
- Detective controls (identify early)
- Corrective controls (reduce impact)
- Transfer or accept where appropriate

### 5. Monitor and Review

- Risk register with owners and review dates
- Trigger conditions for escalation
- Post-incident updates

## Output

Risk register with impact/likelihood scoring, mitigation plans, and monitoring schedule.
