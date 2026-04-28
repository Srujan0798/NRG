---
name: figma-implement-design
description: Translates Figma designs into production-ready application code with 1:1 visual fidelity. Use when implementing UI code from Figma files, when user mentions "implement design", "generate code", "implement component", provides Figma URLs, or asks to build components matching Figma specs.
model-agnostic: true
dependencies: figma-use (required — load before any use_figma call), figma-mcp-server
---

# Implement Design (Figma → Code)

> **Model-agnostic:** Works with any LLM that supports tool use.
> Requires: Figma MCP server connected. For writing back to Figma canvas, also load `figma-use`.

## Skill Boundaries

- **This skill**: Deliverable is **code in the repository** that matches a Figma design.
- For creating/editing nodes inside Figma → use `figma-use`
- For building a full Figma screen from code → use `figma-generate-design`
- For Code Connect mappings → use `figma-code-connect`

## Prerequisites

- Figma MCP server must be connected and accessible
- User provides a Figma URL: `https://figma.com/design/:fileKey/:fileName?node-id=1-2`
  - `:fileKey` = the file key
  - `1-2` = node ID (specific component or frame)
- **OR** when using `figma-desktop` MCP: user selects node in Figma desktop app (no URL required)

## Required Workflow (follow in order, no skipping)

### Step 1: Get Node ID

Parse from URL:
- URL: `https://figma.com/design/kL9xQn2VwM8pYrTb4ZcHjF/DesignSystem?node-id=42-15`
- File key: `kL9xQn2VwM8pYrTb4ZcHjF`
- Node ID: `42-15`

For `figma-desktop` MCP: tools auto-use the currently selected node.

### Step 2: Fetch Design Context

```
get_design_context(fileKey=":fileKey", nodeId="1-2")
```

Returns: layout properties, typography, colors/design tokens, component structure, spacing.

**If response is too large:** use `get_metadata` first to get the node map, then fetch specific child nodes.

### Step 3: Capture Visual Reference

```
get_screenshot(fileKey=":fileKey", nodeId="1-2")
```

This screenshot is the source of truth for validation. Keep it accessible throughout implementation.

### Step 4: Download Required Assets

Download any assets (images, icons, SVGs) returned by the Figma MCP server.

Rules:
- If the MCP returns a `localhost` source for an image or SVG — use that source directly
- Do NOT import new icon packages — assets come from the Figma payload
- Do NOT use placeholders if a `localhost` source is provided

### Step 5: Translate to Project Conventions

Key principles:
- Treat Figma MCP output as a design representation, not final code style
- Replace Tailwind utility classes with the project's preferred utilities or design tokens
- Reuse existing components (buttons, inputs, typography) instead of duplicating
- Use the project's color system, typography scale, and spacing tokens
- Respect existing routing, state management, and data-fetch patterns

**For NRG:** Use the existing component library in `frontend/src/components/`. Match the tier-specific dashboard patterns (Researcher/Government/Industry).

### Step 6: Achieve 1:1 Visual Parity

- Prioritize Figma fidelity
- Avoid hardcoded values — use design tokens from Figma where available
- When project tokens differ from Figma specs, prefer project tokens but adjust minimally to match visuals
- Follow WCAG accessibility requirements

### Step 7: Validate Against Figma

Before marking complete:
- [ ] Layout matches (spacing, alignment, sizing)
- [ ] Typography matches (font, size, weight, line height)
- [ ] Colors match exactly
- [ ] Interactive states work (hover, active, disabled)
- [ ] Responsive behavior follows Figma constraints
- [ ] Assets render correctly
- [ ] Accessibility standards met

## Implementation Rules

### Component Organization
- Place UI components in the project's designated design system directory
- Follow project naming conventions
- Avoid inline styles unless truly necessary for dynamic values

### Design System Integration
- ALWAYS use existing components when possible
- Map Figma design tokens to project design tokens
- Extend existing components rather than creating new ones
- Document any new components added

### Code Quality
- No hardcoded values — extract to constants or design tokens
- Keep components composable and reusable
- Add TypeScript types for component props
- Include JSDoc comments for exported components

## Common Issues

| Issue | Cause | Solution |
|---|---|---|
| Figma output truncated | Design too complex | Use `get_metadata` first, then fetch specific nodes |
| Visual mismatch | Spacing/color discrepancy | Compare side-by-side with Step 3 screenshot |
| Assets not loading | MCP assets endpoint | Verify `localhost` URLs are used directly without modification |
| Token values differ | Project tokens vs Figma | Prefer project tokens, adjust spacing/size minimally |
