# Component Pattern Specifications

This reference defines the exact structure for each component pattern in section 4.9 of the design system. Every component below must be fully specified using tokens from section 4.6.

## How to Read This Template

Each component has:
- **Token mapping**: every visual property (bg, text, border, shadow, radius, padding, gap) as a semantic token reference.
- **Size variants**: sm, md, lg dimensions where applicable.
- **State mappings**: which interactive state rules from section 4.5 apply, with exact token overrides per state.
- **Motion**: which transition preset from section 4.6 applies to state changes.
- **Icons**: which icon tokens from section 4.7 are used, with size and color rules.
- **Layout rules**: padding, gap, alignment, and any structural constraints.

Replace `{token-name}` placeholders with the actual semantic tokens defined in the design system.

---

## Atoms

### Buttons

Four variants × three sizes × five states.

**Variants:** primary, secondary, ghost, destructive

For each variant, specify:

| Property | Token |
|---|---|
| Background | `color-button-{variant}-default` |
| Text | `color-button-{variant}-text` |
| Border | `border-button-{variant}` |
| Border radius | `radius-button` |
| Font | use `body-{size}` level from Typography |
| Shadow | `shadow-button-{variant}` (if any) |

**Size variants:**

| Size | Padding (x / y) | Height | Font Level | Icon Size |
|---|---|---|---|---|
| sm | `space-3` / `space-1` | 32px | `body-sm` | `icon-sm` |
| md | `space-4` / `space-2` | 40px | `body-md` | `icon-md` |
| lg | `space-6` / `space-3` | 48px | `body-lg` | `icon-lg` |

**State mappings** (per variant):

| State | Background | Text | Border | Other |
|---|---|---|---|---|
| default | `color-button-{variant}-default` | `color-button-{variant}-text` | — | — |
| hover | `color-button-{variant}-hover` | (unchanged) | — | cursor: pointer |
| focus | (unchanged) | (unchanged) | — | focus ring per 4.5 |
| active | `color-button-{variant}-active` | (unchanged) | — | — |
| disabled | `color-button-{variant}-default` | (unchanged) | — | opacity 0.5, no pointer events |

**Motion:** `transition-color` on background for hover/active. Disabled state has no transition.

**Icons:** Leading/trailing icon uses `icon-{size}` matching button size (sm→icon-sm, md→icon-md, lg→icon-lg). Icon color inherits button text color. Icon-to-label gap: `space-2`.

### Inputs

Types: text, select, textarea, number.

| Property | Token |
|---|---|
| Background | `surface-input-default` |
| Text | `text-input` |
| Placeholder | `text-input-placeholder` |
| Border | `border-input-default` |
| Border radius | `radius-input` |
| Padding | `space-3` (x) / `space-2` (y) |
| Font | `body-md` |
| Label font | `body-sm` weight medium |

**State mappings:**

| State | Border | Background | Other |
|---|---|---|---|
| default | `border-input-default` | `surface-input-default` | — |
| focus | `border-input-focus` | `surface-input-default` | focus ring per 4.5 |
| error | `border-input-error` | `surface-input-default` | error message below in `text-error` |
| disabled | `border-input-disabled` | `surface-input-disabled` | opacity 0.5, no pointer events |

**Motion:** `transition-color` on border color for focus/error transitions.

### Checkbox & Radio

| Property | Token |
|---|---|
| Size | 20px (md), 16px (sm) |
| Border | `border-input-default` |
| Border radius | `radius-sm` (checkbox), `radius-full` (radio) |
| Checked background | `color-primary-500` |
| Check mark | `color-white` or `text-inverse` |
| Label gap | `space-2` |

### Toggle / Switch

| Property | Token |
|---|---|
| Track width / height | 44px / 24px |
| Thumb size | 20px |
| Track (off) | `surface-input-default` + `border-input-default` |
| Track (on) | `color-primary-500` |
| Thumb | `color-white` |
| Transition | inherits from Interactive States |

### Badges / Tags

| Property | Token |
|---|---|
| Background | `surface-badge-{variant}` (e.g., info, success, warning, error, neutral) |
| Text | `text-badge-{variant}` |
| Border radius | `radius-full` |
| Padding | `space-1` (y) / `space-2` (x) |
| Font | `caption` |

### Labels

| Property | Token |
|---|---|
| Font | `body-sm` weight medium |
| Color | `text-default` |
| Required indicator | `text-error`, asterisk |
| Margin bottom | `space-1` |

### Dividers

| Property | Token |
|---|---|
| Color | `border-subtle` |
| Width | `border-thin` (1px) |
| Margin | `space-4` (vertical divider uses vertical margin) |

---

## Molecules

### Form Groups

A form group composes: Label + Input + Helper text / Error message.

| Property | Token |
|---|---|
| Stack direction | vertical |
| Gap (label → input) | `space-1` |
| Gap (input → helper/error) | `space-1` |
| Helper text font | `caption` |
| Helper text color | `text-muted` |
| Error text font | `caption` |
| Error text color | `text-error` |
| Error icon | `icon-sm` in `text-error`, placed before error text |

### Cards

| Property | Token |
|---|---|
| Background | `surface-card` |
| Border | `border-default` |
| Border radius | `radius-lg` |
| Shadow | `shadow-sm` |
| Padding | `space-6` |
| Header font | `h6` or `body-lg` weight semibold |
| Header/body gap | `space-4` |
| Body font | `body-md` |
| Footer alignment | flex end, gap `space-3` |
| Footer border-top | `border-subtle` with `space-4` top padding |

### Alerts / Toasts

Variants: info, success, warning, error.

| Property | Token |
|---|---|
| Background | `surface-alert-{variant}` |
| Border-left or border | `border-alert-{variant}`, width `border-thick` |
| Border radius | `radius-md` |
| Icon | `icon-md` in `color-{variant}-500` |
| Title font | `body-md` weight semibold |
| Body font | `body-sm` |
| Padding | `space-4` |
| Icon/content gap | `space-3` |
| Toast shadow | `shadow-lg` |
| Toast z-index | `z-toast` |

**Motion:** Alerts use no entrance animation (they appear inline). Toasts use `transition-slide` (slide in from top/bottom) + `transition-fade` on dismiss. Auto-dismiss after configurable duration (default 5s).

**Icons:** Leading icon `icon-md` in `color-{variant}-500`. Dismiss button icon `icon-sm`.

### Nav Items

| Property | Token |
|---|---|
| Padding | `space-2` (y) / `space-3` (x) |
| Font | `body-sm` weight medium |
| Text color (default) | `text-muted` |
| Text color (active) | `text-default` |
| Background (hover) | `surface-hover` |
| Background (active) | `surface-active` |
| Border radius | `radius-md` |
| Icon/label gap | `space-2` |
| Active indicator | left border `border-thick` in `color-primary-500`, or background tint |

**Icons:** Leading icon `icon-sm`, color inherits nav item text color. Active icon uses `text-default`.

### List Items

| Property | Token |
|---|---|
| Padding | `space-3` (y) / `space-4` (x) |
| Font | `body-md` |
| Border bottom | `border-subtle` |
| Hover background | `surface-hover` |
| Secondary text | `body-sm` in `text-muted` |

---

## Organisms

Structure and token mapping only. No interaction logic or responsive behavior beyond collapse breakpoint notes.

### Navbar

| Property | Token |
|---|---|
| Height | 64px (desktop), 56px (mobile) |
| Background | `surface-navbar` |
| Border bottom | `border-default` |
| Shadow | `shadow-sm` (optional, project-dependent) |
| Z-index | `z-sticky` |
| Padding (x) | `space-6` (desktop), `space-4` (mobile) |
| Logo/nav gap | `space-8` |
| Nav items gap | `space-1` |
| Collapse breakpoint | `md` — below this, switch to hamburger menu |
| Position | sticky top |

**Motion:** Mobile menu uses `transition-slide` for open/close.

### Sidebar

| Property | Token |
|---|---|
| Width | 256px (expanded), 64px (collapsed) |
| Background | `surface-sidebar` |
| Border right | `border-default` |
| Z-index | `z-sticky` |
| Padding | `space-4` (y) / `space-3` (x) |
| Section label | `overline` in `text-muted`, `space-6` top margin |
| Nav item style | per Nav Items molecule |
| Collapse breakpoint | `lg` — below this, overlay with `z-modal` |

**Motion:** Collapse/expand uses `transition-slide`. Mobile overlay uses `transition-fade` on backdrop + `transition-slide` on panel.

### Modal

| Property | Token |
|---|---|
| Overlay background | `color-black` at 50% opacity |
| Overlay z-index | `z-modal` |
| Container background | `surface-card` |
| Container radius | `radius-lg` |
| Container shadow | `shadow-xl` |
| Container max-width | 480px (sm), 640px (md), 800px (lg) |
| Header padding | `space-6` (x) / `space-4` (y) |
| Header font | `h5` |
| Header border-bottom | `border-subtle` |
| Body padding | `space-6` |
| Footer padding | `space-6` (x) / `space-4` (y) |
| Footer border-top | `border-subtle` |
| Footer alignment | flex end, gap `space-3` |

**Motion:** Entrance: `transition-scale` (scale up from 95% + fade). Exit: `transition-fade`. Overlay: `transition-fade`.

| Property | Token |
|---|---|
| Header background | `surface-table-header` |
| Header font | `body-sm` weight semibold, `text-muted` |
| Header padding | `space-3` (y) / `space-4` (x) |
| Header border-bottom | `border-default`, `border-medium` width |
| Row padding | `space-3` (y) / `space-4` (x) |
| Row border-bottom | `border-subtle` |
| Row font | `body-md` |
| Row hover | `surface-hover` |
| Striped rows (optional) | alternate `surface-table-stripe` |
| Cell alignment | left (text), right (numbers) |
