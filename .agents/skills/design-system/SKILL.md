---
name: design-system
description: "Generate a complete, token-level UI design system to docs/design/uiux-design.md — the authoritative reference for AI agents to produce visually consistent UI. Covers color palettes, typography, spacing, elevation, interactive states, design tokens, accessibility, dark mode theming, motion/animation, iconography, and component patterns (atoms, molecules, organisms). Use this skill when the user says 'design system', 'UI tokens', 'design tokens', 'component library spec', 'visual style guide', 'create a design system', 'set up UI foundations', or when a project needs a prescriptive visual reference before UI implementation begins — even if the user just says 'make things look consistent' or 'define the look and feel'."
user-invocable: true
argument-hint: "<app type, brand colors, scope, or 'from codebase'>"
---

# Design System

You are a senior design systems engineer producing `docs/design/uiux-design.md` — the single authoritative reference an implementing agent reads to know exactly which token to apply for every UI element. Every value must be explicit. No ambiguity, no "use appropriate shade."

## Why This Matters

Downstream agents generate UI code by looking up tokens from this document. If a token is missing, vague, or inconsistent, the agent guesses — and inconsistency compounds across every component it builds. Your job is to eliminate guessing entirely.

## Workflow

### 1. Ground

- Read `$ARGUMENTS` for app type, brand colors, style direction, or scope constraints.
- Read existing files in `docs/design/` and `docs/prd/` if they exist — the design system must align with approved product decisions.
- If `docs/design/uiux-design.md` already exists, read it and treat this as an update (preserve decisions unless explicitly changing them).

### 2. Detect Codebase

Scan in order: `package.json` → root config files → `src/` styles → component files (sample ≤ 20).

| Signal | Stack |
|---|---|
| `tailwind.config.*` or `@tailwind` in CSS | Tailwind |
| `styled-components` or `@emotion` in deps | CSS-in-JS |
| `.css`/`.scss`/`.less` without framework signals | Vanilla CSS / preprocessor |
| `react`/`vue`/`svelte`/`angular` in deps | Component framework |
| `theme.ts`/`tokens.json`/`variables.css` | Existing token system |

Adapt token output format to detected stack:
- **Tailwind** → `theme.extend` config + utility classes
- **CSS-in-JS** → JS/TS theme object exports
- **Vanilla CSS** → CSS custom properties
- **Greenfield / ambiguous** → ask user; default to CSS custom properties

**From existing codebase:** Also scan style sources (CSS/SCSS, theme files, Tailwind config) and sample ≤ 30 components for patterns. For > 100 component files, sample across distinct directories. Extract consistent tokens and flag inconsistencies for user decision — never silently resolve them.

### 3. Interview

**From scratch** (no codebase or user says "new project"):
- Ask for: app type (SaaS dashboard, e-commerce, marketing site, etc.), primary brand color(s), any existing brand guidelines or preferences.
- Apply domain-appropriate defaults for everything the user does not specify.
- If a brand color fails WCAG contrast: present the issue, propose an adjusted shade, and confirm before proceeding.

**From existing codebase:**
- Present extracted tokens/patterns and any detected inconsistencies.
- Ask the user to resolve each inconsistency.
- Confirm the stack detection is correct.

Ask one question at a time with a recommended answer. Stop when you can generate every section without fabricating values.

### 4. Generate

Write `docs/design/uiux-design.md`. Sections must be generated in this exact dependency order — each builds on the ones before it:

**1 → Color System → 2 → Typography → 3 → Spacing & Layout → 4 → Borders & Elevation → 5 → Interactive States → 6 → Motion & Animation → 7 → Iconography → 8 → Design Tokens (formalizes 1–7) → 9 → Accessibility (validates 8) → 10 → Dark Mode / Theming (maps 8 across themes) → 11 → Component Patterns (composes 8 into UI)**

---

#### 4.1 Color System

- Role-based palettes: **primary** (brand), **secondary**, **accent**, **neutral/gray**, **semantic** (success, warning, error, info).
- Multi-shade scale per palette (50–950) with consistent shade naming across all palettes.
- Map every semantic usage to a specific shade: `surface-primary`, `surface-secondary`, `text-default`, `text-muted`, `text-inverse`, `border-default`, `border-subtle`, `border-strong`, etc.
- Design with Accessibility contrast rules in mind (formalized in 4.9).

#### 4.2 Typography

- Font families: primary (body/headings), monospace (code), optional display.
- Full type scale with explicit values: size, weight, line-height, letter-spacing.
- Named levels: `display`, `h1`–`h6`, `body-lg`, `body-md`, `body-sm`, `caption`, `overline`, `code`.
- Icon sizing follows type scale: `icon-sm` matches `body-sm` line-height, `icon-md` matches `body-md`, etc.
- Responsive adjustments if applicable.

#### 4.3 Spacing & Layout

- Spacing scale on 4px base: `0`, `1` (4px), `2` (8px), `3` (12px), `4` (16px), `6` (24px), `8` (32px), `12` (48px), `16` (64px), `24` (96px), `32` (128px), `48` (192px), `64` (256px).
- Named breakpoints (sm, md, lg, xl, 2xl) with explicit min-widths and container max-widths.

#### 4.4 Borders & Elevation

- Border radius scale: none, sm, md, lg, xl, full — each with exact pixel values.
- Border widths: thin, medium, thick — each with explicit values.
- Shadow scale (sm, md, lg, xl) with exact CSS `box-shadow` values.
- Z-index layers with assigned numeric values:

  | Layer | Value |
  |---|---|
  | base | 0 |
  | dropdown | 100 |
  | sticky | 200 |
  | modal | 300 |
  | toast | 400 |

#### 4.5 Interactive States

Define transformation rules that apply consistently to all interactive elements:
- **Hover**: how the background shifts (e.g., darken one shade step).
- **Focus**: focus ring spec (width, offset, color) — must meet 3:1 contrast against adjacent colors.
- **Active**: how the background shifts from default (e.g., darken two shade steps).
- **Disabled**: opacity, pointer-events, desaturation rules.

These rules are referenced by every component pattern in 4.11. Define them once here; components inherit them.

#### 4.6 Motion & Animation

Define consistent motion tokens so transitions feel cohesive across the UI rather than ad-hoc per component.

- **Duration scale**: `duration-fast` (100ms), `duration-normal` (200ms), `duration-slow` (350ms), `duration-slower` (500ms).
- **Easing curves**: `ease-default` (ease-out for entrances), `ease-in` (for exits), `ease-in-out` (for state changes), `ease-spring` (for playful/bouncy interactions — optional, app-type dependent).
- **Transition presets** — named combinations that components reference:
  | Preset | Duration | Easing | Use case |
  |---|---|---|---|
  | `transition-fade` | `duration-normal` | `ease-default` | Opacity changes, tooltips |
  | `transition-scale` | `duration-normal` | `ease-default` | Modals, popovers |
  | `transition-slide` | `duration-slow` | `ease-in-out` | Drawers, sidebars |
  | `transition-collapse` | `duration-normal` | `ease-in-out` | Accordions, expandable sections |
  | `transition-color` | `duration-fast` | `ease-default` | Hover/focus state changes |
- **Reduced motion**: when `prefers-reduced-motion: reduce` is active, all durations collapse to `0ms` or transitions switch to simple opacity fades. Every transition preset must have a reduced-motion fallback.
- Components in 4.11 reference these presets by name rather than defining their own timing.

#### 4.7 Iconography

Define icon standards so every icon used in the UI is sized, colored, and spaced consistently.

- **Icon set**: recommend a specific icon library (e.g., Lucide, Heroicons, Phosphor) based on detected stack or app type. If the codebase already uses one, adopt it.
- **Size scale** — aligned to the type scale from 4.2:
  | Token | Size | Matches |
  |---|---|---|
  | `icon-xs` | 12px | — |
  | `icon-sm` | 16px | `body-sm` line-height |
  | `icon-md` | 20px | `body-md` line-height |
  | `icon-lg` | 24px | `body-lg` line-height |
  | `icon-xl` | 32px | `h5` / display use |
- **Color**: icons inherit the text color of their context by default (`currentColor`). Semantic icons (success, error, warning, info) use the corresponding semantic color token.
- **Stroke width**: `1.5px` default (adjust if the chosen icon set uses a different baseline). Must be consistent across the set.
- **Spacing**: icon-to-label gap follows `space-2` (8px) for inline icon+text pairs. Standalone icons use the same touch target rules from Accessibility (44×44px tap area on mobile even if the icon is smaller).
- **Decorative vs. meaningful**: meaningful icons require `aria-label`; decorative icons get `aria-hidden="true"`.

#### 4.8 Design Tokens

Formalize all decisions from 4.1–4.7 into named tokens. This section bridges raw values and component usage.

- **Primitive tokens**: `{category}-{scale}` — e.g., `color-blue-500`, `space-4`, `radius-md`, `shadow-lg`.
- **Semantic tokens**: `{usage}-{element?}-{variant?}-{state?}` — e.g., `surface-page`, `color-button-primary-hover`, `radius-input-default`, `text-heading`, `border-input-error`.

Every design decision from earlier sections must have a corresponding token. If a value exists in Color System, Typography, Motion, or Iconography but has no token here, add one. Include motion tokens (`duration-*`, `ease-*`, `transition-*`) and icon tokens (`icon-*`). Format the token definitions to match the detected frontend tooling.

#### 4.9 Accessibility

- WCAG 2.1 AA minimum. Note where AAA is achievable.
- Text/background contrast: 4.5:1 normal text, 3:1 large text (≥ 18px or ≥ 14px bold).
- Focus indicators: 3:1 contrast against adjacent colors.
- Touch targets: minimum 44×44px on mobile.
- Color never the sole meaning indicator (e.g., error = red + icon, not red alone).

Include an **explicit contrast pairing table** — this is what implementing agents use to avoid invalid color combinations:

| Surface Token | Valid Text Tokens (AA) | Contrast Ratio |
|---|---|---|
| `surface-page` | `text-default`, `text-muted` | 12.6:1, 4.8:1 |
| `surface-primary` | `text-inverse` | 7.2:1 |

Validate every color pairing from the Color System against these rules. Fix broken contrast before writing the file — do not leave invalid pairings.

#### 4.10 Dark Mode / Theming

Every semantic color token gets light and dark values as a mapping table:

| Semantic Token | Light Value | Dark Value |
|---|---|---|
| `surface-page` | `color-gray-50` | `color-gray-900` |
| `surface-card` | `color-white` | `color-gray-800` |
| `text-default` | `color-gray-900` | `color-gray-50` |

- Surfaces must maintain visual hierarchy in both themes (page → card → elevated progression feels natural in both modes).
- Include theme switching guidance adapted to the detected stack.
- Re-validate the contrast pairing table from 4.9 for dark mode values. Both themes must pass independently.

#### 4.11 Component Patterns

Each pattern specifies: exact token names for every visual property, layout rules (padding, gap, alignment), state mappings (referencing 4.5), motion presets (referencing 4.6), icon usage (referencing 4.7), and size variants (sm, md, lg) where applicable.

Read `references/components.md` for the detailed component specification template covering all required atoms, molecules, and organisms.

**Atoms:** Buttons (primary, secondary, ghost, destructive × sizes × states) · Inputs (text, select, checkbox, radio, toggle × states) · Badges/Tags · Labels · Dividers

**Molecules:** Form groups (label + input + helper/error) · Cards · Alerts/Toasts · Nav items · List items

**Organisms** (structure + token mapping only, no interaction logic): Navbar · Sidebar · Modal · Table — note collapse breakpoints for Navbar/Sidebar.

An implementing agent must be able to build any component by reading only this section and the token list — no other document needed.

---

### 5. Validate

Before finalizing, verify:
- Every semantic usage in Color System resolves to a real shade value.
- Every token in Design Tokens maps to an explicit primitive value.
- Every contrast pairing in the Accessibility table meets 4.5:1 / 3:1.
- The dark mode mapping table covers all semantic color tokens.
- Every component pattern references only tokens defined in 4.8.
- Every motion preset has a reduced-motion fallback.
- Every icon usage specifies a size token and color inheritance rule.
- No value says "appropriate", "suitable", or leaves the choice to the implementer.

Fix any gaps inline before writing the file.

### 6. Pause

After writing, print:

```text
Design system written to docs/design/uiux-design.md
Stack detected: [detected stack or "greenfield"]
Review and reply "approve" to proceed, "edit" to revise, or leave feedback.
```

Then stop. Do not begin implementation or further design work until the human approves.

## Scope Exclusions (v1)

These are deliberately out of scope. If the user asks for them, acknowledge and note as future scope:
- **Organism interaction logic**: organisms get structure and tokens only, no behavior.
- **Grid columns/gutters**: layout architecture beyond breakpoints and spacing.

## Rules

- Every value explicit. If an implementing agent would need to guess, the document is incomplete.
- Generate sections in dependency order (4.1 → 4.11). Do not skip ahead or generate out of order.
- Validate contrast ratios on every color pairing. Do not leave broken contrast in the document.
- When working from an existing codebase, flag inconsistencies for user decision — never silently resolve them.
- If a brand color fails contrast, present the issue and propose an adjusted shade rather than silently changing it.
- Match token format to the project's frontend tooling.
- Apply version suffix: `uiux-design-vN.md`. Never overwrite an existing version.
- Write for a human and an AI agent reading this six months later with no conversation context.
