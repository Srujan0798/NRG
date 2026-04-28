---
name: figma-generate-design
description: Translates application pages, views, or multi-section layouts into Figma using the published design system. Use when task involves "write to Figma", "create in Figma from code", "push page to Figma", "create a screen", "build a landing page in Figma", "update the Figma screen to match code", or converting modals/dialogs/drawers/panels to Figma.
model-agnostic: true
dependencies: figma-use (MANDATORY — load before any use_figma call), figma-mcp-server
---

# Build / Update Screens and Views from Design System (Code → Figma)

> **Model-agnostic:** Works with any LLM that supports tool use.
> **MANDATORY:** Load `figma-use` before any `use_figma` call — it contains critical rules (color ranges, font loading, etc.).

Use this skill to create or update **screens, views, and multi-section UI containers** in Figma by reusing the published design system — components, variables, and styles — rather than drawing primitives with hardcoded values.

## Skill Boundaries

- **This skill**: Deliverable is a **composed Figma view** (new or updated) — full pages, modals, dialogs, drawers, sidebars, panels.
- For generating code from a Figma design → use `figma-implement-design`
- For creating new reusable components/variants → use `figma-use` directly
- For Code Connect mappings → use `figma-code-connect`

## Prerequisites

- Figma MCP server must be connected
- Target Figma file must have a published design system with components (or team library access)
- User provides either: a Figma file URL/file key, or context about which file to target
- Source code or description of the screen/view to build/update

## Parallel Workflow for Web Apps (when source has images)

When building from a **web app** that can be rendered in a browser AND the source contains images:

1. **Run in parallel:**
   - Start this skill's workflow (use_figma + design system components)
   - Run `generate_figma_design` to capture a pixel-perfect screenshot
2. **After both complete:** Update the use_figma output to match the pixel-perfect layout
3. **Transfer images:** Copy `imageHash` values from the capture to your use_figma output
4. **Delete the capture** — it was only a visual reference

**This parallel workflow is MANDATORY when the source contains images.** The `use_figma` Plugin API cannot fetch external image URLs — it can only set image fills by copying `imageHash` values from nodes already in the file.

## Required Workflow (follow in order)

### Step 1: Understand the Deliverable

1. Read relevant source files to understand structure, sections, and components used
2. Identify major sections (e.g., Header, Hero, Content Panels, Footer; or Title Bar, Form, Action Bar)
3. For each section, list UI components involved (buttons, inputs, cards, nav pills, etc.)
4. Check if source contains images — if yes and it's a web app, start parallel `generate_figma_design` capture now

### Step 2: Collect Component Keys, Variables, and Styles

Need three things from the design system: **components**, **variables** (colors, spacing, radii), **styles** (text/effect).

#### 2a: Discover components

**2a-i — Check Code Connect first** (files named `*.figma.ts`, `*.figma.tsx`, `*.figma.js`)
- Search for Code Connect file per component (e.g., `**/Button.figma.tsx`)
- Extract Figma component URL from each file, parse `fileKey` and `nodeId`
- Resolve component keys via `use_figma` against the library file

**2a-ii — Inspect existing screens** if components unresolved:
```js
const frame = figma.currentPage.findOne(n => n.name === "Existing Screen");
frame.findAll(n => n.type === "INSTANCE").forEach(inst => {
  // map component names → keys
});
```

**2a-iii — Last resort: `search_design_system`** with `includeComponents: true`, broad terms (button, input, nav, card, etc.)

Also capture component TEXT properties — you'll need them for `setProperties()` overrides.

#### 2b: Discover variables (colors, spacing, radii)

> **Warning:** `figma.variables.getLocalVariableCollectionsAsync()` only returns local variables — not library variables. Use `search_design_system` with `includeVariables: true` for library variables.

Search terms: "gray", "red", "blue", "background", "foreground", "border", "space", "radius", "gap", "padding"

Inspect existing screens for bound variables — most authoritative source.

Import library variables with `figma.variables.importVariableByKeyAsync(key)`.

#### 2c: Discover styles (text, effect)

Use `search_design_system` with `includeStyles: true` — terms: "heading", "body", "shadow", "elevation".
Or inspect existing screens for `textStyleId` and `effectStyleId` values.

Import with `figma.importStyleByKeyAsync(key)`.

### Step 3: Create the Wrapper Frame First

**Do NOT build sections as top-level page children and reparent later** — `appendChild()` across `use_figma` calls silently fails.

Create the wrapper in its own `use_figma` call, return its ID:

```js
const wrapper = figma.createAutoLayout("VERTICAL");
wrapper.name = "VIEW_NAME";
wrapper.resize(WIDTH, 100); // Full page: 1440 | Modal: 640 | Drawer: 360 | Panel: 400
wrapper.layoutSizingHorizontal = "FIXED";
wrapper.x = maxX + 200; // position away from existing content
return { success: true, wrapperId: wrapper.id };
```

### Step 4: Build Each Section Inside the Wrapper

One section per `use_figma` call. Fetch wrapper by ID at start of each call, append directly.

```js
const wrapper = await figma.getNodeByIdAsync("WRAPPER_ID");

// Import components by key
const buttonSet = await figma.importComponentSetByKeyAsync("BUTTON_KEY");
const primaryButton = buttonSet.children.find(c => c.name.includes("variant=primary"));

// Import variables for colors/spacing (NOT hardcoded values)
const bgVar = await figma.variables.importVariableByKeyAsync("BG_VAR_KEY");

// Build section with variable bindings
const section = figma.createAutoLayout();
section.setBoundVariable("paddingLeft", spacingVar);
const bgPaint = figma.variables.setBoundVariableForPaint(
  { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', bgVar
);
section.fills = [bgPaint];

// Override instance text using component property keys
const btnInstance = primaryButton.createInstance();
btnInstance.setProperties({ "Label#2:0": "Get Started" });

wrapper.appendChild(section);
section.layoutSizingHorizontal = "FILL"; // AFTER appending

return { success: true, createdNodeIds: [section.id] };
```

**Never hardcode hex colors or pixel spacing** when a design system variable exists.

After each section: validate with `get_screenshot` before moving on.

### Step 5: Validate and Transfer Images

Take screenshots of individual sections (not just full view) to catch:
- Cropped/clipped text
- Overlapping elements
- Placeholder text still showing
- Wrong component variants
- Blank image placeholders

**Transfer images from `generate_figma_design` capture:**
1. Find all image nodes in the capture (fills with `type === "IMAGE"`)
2. Match to corresponding frames in your output
3. Apply: `targetFrame.fills = [{ type: "IMAGE", imageHash: "hash", scaleMode: "FILL" }]`
4. Delete the capture output

### Step 6: Updating an Existing View

1. `get_metadata` to inspect existing structure
2. Identify which sections need updating
3. For each changed section: swap component instances, update text/variants/layout, add/remove sections
4. Validate with `get_screenshot` after each modification

## What to Build vs Import

| Build manually | Import from design system |
|---|---|
| Wrapper frame | Components (buttons, cards, inputs, etc.) |
| Section container frames | Variables (colors, spacing, radii) |
| Layout grids | Text styles (heading, body, caption) |
| | Effect styles (shadows, blurs) |

## For NRG Frontend

When building NRG tier dashboards:
- Researcher (Tier 1): full data visibility, `frontend/src/components/researcher/`
- Government (Tier 2): aggregated stats only, `frontend/src/components/government/`
- Industry (Tier 3): anonymized view, `frontend/src/components/industry/`

Match existing dashboard patterns. Check `frontend/src/` before creating any new components.
