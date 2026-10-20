---
name: page-detail
description: "Produce implementation-ready page breakdowns covering layout, components, content, imagery, interactions, and page states — one markdown file per page into docs/pages/. An implementing agent should need no further design input after reading this output. Use when the user says 'page detail', 'page breakdown', 'page spec', 'break down this page', 'detail the homepage', 'UI page plan', 'page layout', 'describe the page', or when a specific page needs a full visual/structural specification before UI implementation begins — even if the user just says 'design the dashboard page' or 'what should the landing page look like'."
user-invocable: true
argument-hint: "<page name(s), or 'all' to generate from sitemap>"
---

# Page Detail

Produce implementation-ready page breakdowns — one `[page-name].md` per page into `docs/pages/`. Every value must be explicit; if an implementing agent would guess, the breakdown is incomplete.

**Design philosophy: Dribbble-quality, award-worthy UI.** Every page must feel crafted, not assembled. Prioritize generous whitespace, bold typography hierarchies, refined color usage, layered depth (glassmorphism, subtle gradients, soft shadows), fluid motion, and intentional asymmetry over generic template layouts. The output should read like a top-shot Dribbble case study — visually distinctive, modern, and polished to a level that makes users pause and admire.

## Workflow

### 1. Ground

- Read `$ARGUMENTS` for page name(s) or scope.
- Auto-read when they exist: `docs/prd/main-v1.md`, `docs/prd/[module]-v1.md`, `docs/design/sitemap.md`, `docs/design/data-model.md`, `docs/design/uiux-design.md`.
- Use design-system component names/variants/tokens when available; fall back to descriptive naming otherwise.
- Match pages against sitemap and PRD; pull context automatically.
- **Visual benchmark** — mentally reference top Dribbble/Behance shots in the same domain. The page must compete with those, not with generic SaaS templates.

### 2. Interview

Skip if references provide sufficient context. Otherwise ask (one at a time, with recommended answer):
1. Primary user goal on this page?
2. Target user and how they arrive?
3. Key data entities and actions?

Stop when every section can be generated without fabricating content.

### 3. Generate

Write one kebab-case `[page-name].md` per page into `docs/pages/` (create dir if missing). Each file contains these sections in order:

#### 3.1 Page Metadata

Table: Name, Route, Purpose (one sentence), Target User, Primary Action, Inbound Links, Outbound Destinations.

#### 3.2 Layout Structure

Ordered top-to-bottom section list (e.g., Navbar → Hero → Features Grid → CTA → Footer). Per section:
- **Spatial rules** — columns/grid, gaps, alignment, max-width, padding (design tokens when available), visual separation.
- **Whitespace & breathing room** — generous padding between sections (never cramped). Specify vertical rhythm: section spacing ≥ 80–120px on desktop. Use whitespace as a design element, not leftover space.
- **Visual depth & layering** — specify elevation, overlapping elements, background layers (e.g., gradient blobs, grain textures, glassmorphic cards, frosted overlays). Sections should feel layered, not flat stacked divs.
- **Layout personality** — avoid cookie-cutter symmetric grids everywhere. Specify where to use intentional asymmetry, offset elements, overlapping imagery, broken-grid compositions, or staggered card layouts to create visual interest.
- **Responsive behavior** — per breakpoint (sm/md/lg/xl): what stacks, collapses, hides, reflows. Never write "responsive layout" without specifying per-breakpoint changes.

#### 3.3 Component Inventory

Per component: Name (design-system or descriptive), Variant (specific: single-select vs multi-select, ghost vs primary), Size (sm/md/lg), Section, Props/Config (placeholder, limits, icons), Initial State, State Dependencies, Data Binding (API/static/user input/computed).

**Visual refinement per component:**
- **Surface treatment** — specify border-radius (generous: 12–20px for cards, 8–12px for inputs), shadow depth (layered multi-shadow for premium feel), background (solid/gradient/glass/blur).
- **Typography weight** — bold headlines, light body text, oversized hero text (48–72px+). Specify font-weight contrasts within each component.
- **Color accent strategy** — where does the accent color appear? Gradient buttons, colored borders, tinted backgrounds, highlight underlines. Be specific.
- **Icon style** — outlined vs filled, stroke width, size relative to text, custom or library (Lucide, Phosphor, etc.).

Required specificity level:
- "Single-select dropdown with search, filterable, placeholder 'Select country...', 12px radius, subtle ring focus, smooth 200ms open animation"
- "Primary button, lg, label 'Get Started', full-width on mobile, gradient background (brand-500 → brand-600), 12px radius, hover: lift shadow + slight scale(1.02), press: scale(0.98)"
- "Text input, left icon (search), placeholder 'Search orders...', debounced 300ms, frosted glass background, soft inner shadow"
- "Confirmation modal, centered, backdrop blur 12px, 20px radius, title + body + cancel (ghost) + confirm (destructive), entry: scale from 95% + fade, exit: fade 150ms"

#### 3.4 Page States

Define all five states — specify which components are visible/hidden and layout adjustments for each. **Every state is a design opportunity, not an afterthought.** Empty and loading states should feel as polished as the populated view.

| State | Detail |
|---|---|
| Loading | Skeleton/shimmer layout per section — use animated gradient shimmer (not grey blocks). Match exact layout dimensions so there is zero layout shift on load. |
| Empty | Custom illustration (style-matched to brand) + warm message + prominent CTA (e.g., "No orders yet — Create your first order"). Center vertically with generous padding. Never show a blank white void. |
| Populated | Standard data view — the hero state, fully styled |
| Error | Inline errors with contextual styling, toasts with icon + dismiss animation, retry actions as secondary buttons, graceful fallback UI (not raw error text) |
| Unauthorized | Access denied with brand illustration, soft messaging, clear redirect CTA, or gated blur overlay with sign-in prompt |

#### 3.5 Content & Copywriting

Per section: exact heading text + level (h1/h2/etc.), exact body copy (or pattern + tone for dynamic), microcopy (labels, tooltips, placeholders, helpers, errors), content hierarchy, tone, character constraints. Never write "appropriate heading" — write the heading.

**Typography drama** — specify where to use oversized display text, where to mix font weights for contrast (e.g., light 300 + bold 700 in same heading), where to use letter-spacing (tight for headlines, relaxed for labels). Headlines should feel confident and punchy, not corporate-bland. Subheadings should complement, not compete.

#### 3.6 Imagery & Visual Flourishes

Per image slot: Section, Purpose (trust/emotion/explanation/decoration/social proof), Type (photo/illustration/icon/avatar/screenshot/video thumbnail/3D render/abstract shape), Style direction (e.g., "flat illustration, muted pastels", "3D abstract blob, iridescent gradient", "editorial photography, desaturated with color pop"), Aspect ratio, Sizing behavior (fixed/responsive/constrained with min/max), Alt text pattern.

**Visual richness requirements:**
- **Background treatments** — specify decorative elements: gradient orbs, mesh gradients, noise/grain overlays, dot grids, subtle pattern fills, floating geometric shapes. These add depth and uniqueness.
- **Image presentation** — images in cards with shadow + rounded corners, browser-mockup frames for screenshots, device mockups for app previews, parallax or tilt on scroll.
- **Illustration style** — cohesive across the page. Specify: line weight, color palette (from tokens), level of detail, character style if applicable.

Infer style from context: hero → aspirational + bold, features → explanatory + clean, testimonials → social proof + warm; B2B → sophisticated + restrained, consumer → vibrant + energetic, developer → minimal + precise. Always lean toward premium over generic.

#### 3.7 Interactions & Micro-interactions

- **Interactions** — action → outcome pairs. Forms: validate → loading → success/error. Navigation: trigger → destination.
- **Animation** — entry animations (staggered fade-up for lists, scale-in for cards, blur-to-sharp for images), component transitions (press/open/close/shimmer), state transitions, scroll-triggered effects. Use design-system motion tokens when available.
- **Hover & focus states** — every interactive element must have a visible, delightful hover state. Specify: color shift, shadow lift, scale nudge, underline slide, background fill, icon rotation — whatever fits. Focus rings should be styled (colored ring, not browser default).
- **Scroll-driven effects** — specify parallax layers, sticky elements, reveal-on-scroll sections (fade-up + translate 20px, staggered 100ms per item), progress indicators, or scroll-linked animations where they add value.
- **Purpose** — every animation tied to a reason (attention/confirmation/continuity/feedback/delight). Tasteful decorative animation IS allowed when it elevates perceived quality — but specify duration, easing (prefer ease-out / spring), and trigger.
- **Polish details** — smooth page transitions, number count-up animations for stats, typing effects for headlines, cursor-follow effects for hero sections, magnetic buttons — specify where these premium touches apply.

### 4. Validate

Before finalizing, verify:
- Every component has specific variant, size, and initial state.
- Every section has explicit responsive behavior per breakpoint.
- All five page states defined with equal visual care.
- All headings/primary copy are exact text with typographic intent (size, weight, spacing).
- Every image slot has purpose, type, aspect ratio, alt text pattern.
- Component names match design system when one exists.
- No value says "appropriate", "suitable", or defers choice to implementer.
- **Dribbble check** — would this page get featured on Dribbble? If it reads like a Bootstrap template, add: depth (shadows/glass), personality (asymmetry/color pops), motion (micro-interactions), and whitespace. Revise until it feels premium.
- At least three "signature moment" per page — a visual detail that makes the page memorable (animated hero, unique card hover, custom illustration, bold typography pairing).

Fix gaps inline before writing.

### 5. Pause

Print:
```text
Page detail written to docs/pages/[page-name].md
References used: [list files read]
Review and reply "approve" to proceed, "edit" to revise, or leave feedback.
```
Stop. Do not begin implementation until human approves.

## Rules

- Every value explicit — no guessing by the implementer.
- One independent file per page; do not combine pages.
- Use design-system names/tokens from `docs/design/uiux-design.md` when it exists.
- Do not model cross-page state; sitemap provides flow coherence.
- Prescriptive: exact variants, exact copy. Humans override for creative reasons.
- Write for a reader with no conversation context.
- **Quality bar: Dribbble top-shot.** Generic, flat, template-like output is a failure. Every page must have visual depth, typographic contrast, intentional whitespace, refined micro-interactions, and at least one standout design moment.
- **Uniqueness over convention.** Prefer distinctive layouts (broken grids, overlapping sections, bold color blocks) over safe symmetric grids — unless the content demands simplicity.
- **Details matter.** Specify border-radius values, shadow layers, gradient directions, animation durations, easing curves, hover transforms. Vague visual direction produces vague UI.
