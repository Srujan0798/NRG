---
name: runbook
description: Create or update an operational runbook for a recurring task or procedure. Use when documenting a task that on-call or ops needs to run repeatably, turning tribal knowledge into exact step-by-step commands, adding troubleshooting and rollback steps to an existing procedure, or writing escalation paths for when things go wrong.
---

# /runbook

Create or update an operational runbook for a recurring task or procedure.

## Usage

```
/runbook $ARGUMENTS
```

## Workflow

### 1. Define the Task

- What the runbook covers
- When to use it (triggers, alerts, schedules)
- Prerequisites and access requirements

### 2. Write Step-by-Step Procedure

- Exact commands or actions
- Expected output at each step
- Verification checkpoints
- Time estimates per step

### 3. Add Troubleshooting

- Common failure modes
- Diagnostic commands
- Recovery steps

### 4. Define Escalation

- When to escalate
- Who to contact
- Severity classification
- Communication template

### 5. Maintenance

- Review frequency
- Last tested date
- Known gaps or TODOs

## Output

Operational runbook document with procedure, troubleshooting, and escalation sections.
