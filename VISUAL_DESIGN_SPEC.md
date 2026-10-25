# Experiment OS — Adaptive Glass Visual System

## 1. Appearance Direction

### 1.1 Design intent

The interface is a focused research instrument with the calm of an obsidian workspace and the tactility of carefully layered optical glass. Its appearance is dimensional without imitating physical hardware: materials respond to hierarchy, light, pointer proximity, and state, while controls remain legible and predictable.

The visual language combines:

- Deep tinted-neutral foundations in place of pure black.
- Translucent, blurred glass for selected surfaces and overlays.
- Fine reflective edges that imply thickness without heavy outlines.
- A single high-chroma accent family for navigation and focus.
- Diffuse ambient illumination, restrained colour fog, and sparse texture.
- Asymmetric bento composition with consistent spacing and corner radii.
- Tactile, spring-based motion with controlled settling and no gratuitous bounce.

### 1.2 Material principles

- **Hierarchy through light and elevation:** canvas, card, overlay, and active surfaces differ by tint, luminance, blur, and border response—not by arbitrary shadow strength.
- **Glass only where it communicates depth:** use translucent glass for floating panels, drawers, menus, sticky controls, and selected summary cards. Keep long-form notes and dense tables on opaque or near-opaque surfaces for contrast.
- **One accent band:** choose violet, cobalt, or emerald as the active product accent. Do not combine multiple equally dominant brand hues.
- **Ambient before decorative:** mesh gradients and aurora fields sit behind content, never beneath small text or dense data.
- **Optical alignment:** spacing, radii, and card balance are measured by visual mass; asymmetric grids must still align to a shared baseline and spacing scale.
- **State must remain explicit:** blur, glow, animation, and translucency supplement labels, icons, focus rings, and state text.

## 2. Colour Theory and Palette

### 2.1 Dark palette

Use a cool obsidian base with a subtle midnight bias. Pure black is excluded from large surfaces to reduce visual vibration and preserve separation between layers.

| Token | Value | Application |
|---|---|---|
| Canvas / Level 0 | `#090A0F` or `#0D0E12` | Application background and broad negative space |
| Surface / Level 1 | `#13151C` or `#161822` | Cards, content panels, editor surfaces |
| Elevated / Level 2 | `#1C1F2B` or `#202433` | Menus, dialogs, popovers, inspector drawers |
| Active / Level 3 | `#262A3B` | Hover, selected pills, active navigation, pressed secondary controls |
| Text primary | `#F2F3F7` | Primary copy, headings, essential values |
| Text secondary | `#A5ABBA` | Labels, descriptions, metadata with adequate contrast |
| Text tertiary | `#747D91` | Decorative or nonessential metadata only |
| Hairline | `rgba(236,240,255,0.10)` | Standard subtle borders |
| Hairline highlight | `rgba(255,255,255,0.28)` | Upper edge specular highlight |
| Focus | Accent at 100% | Keyboard focus, selected controls, active data point |

The Level 0 choice is a token variant, not a per-component preference. Pick one canvas token for a given theme and preserve consistent luminance ordering: (L_0 < L_1 < L_2 < L_3). Every adjacent elevation pair must remain visually distinguishable at normal display brightness.

### 2.2 Light palette

| Token | Value | Application |
|---|---|---|
| Canvas | `#F8F9FE` | Main application canvas |
| Card | `#FFFFFF` | Primary content cards |
| Elevated surface | `#FFFFFF` with cool tinted shadow | Menus and drawers |
| Border | `#E5E7EB` | Card boundary and controls |
| Border subtle | `#EEF0F2` | Nested group separation |
| Text primary | `#111827` | Main copy and headings |
| Text secondary | `#475569` | Labels and descriptions on white surfaces |
| Text muted | `#64748B` | Low priority metadata where contrast is sufficient |
| Decorative cool | `#94A3B8` | Icons, illustrations, and large nonessential shapes |

The visual target of 92–95% neutral opacity applies to near-black primary text over white, not white text over a light surface. Small text must meet WCAG AAA where practical (contrast ratio at least 7:1); all normal text must meet WCAG AA (at least 4.5:1). `#94A3B8` over white is reserved for large text, icons, or decoration when it does not meet the required contrast for the rendered size. Do not reduce text opacity as a substitute for a lower-priority semantic token.

### 2.3 Accent and functional colour

Select one primary accent family per product skin:

- **Electric violet:** primary focus, selection, and exploratory/AI affordances.
- **Cobalt:** primary focus for technical, analytical, and link-forward surfaces.
- **Emerald:** primary focus when progress and successful outcomes are the dominant product signal.

Functional tokens remain independent of the brand accent:

- Success: `#22C55E`.
- Warning: `#F59E0B`.
- Danger: `#EF4444`.
- Informational state: a cool blue with verified contrast against the current surface.

Functional colours communicate status only. Do not use success green as a general decorative glow or danger red as a generic attention accent.

### 2.4 60/30/10 colour distribution

- **60% foundation:** canvas, large negative spaces, neutral layout chrome.
- **30% structure:** cards, panels, typography, borders, and nested surfaces.
- **10% emphasis:** accent, state colours, focal values, and selected controls.

This ratio is a composition guide, not a pixel quota. Keep the accent below the 10% share on content-heavy screens; a continuously glowing interface exhausts attention and weakens state distinction.

## 3. Surface Materials, Glass, and Depth

### 3.1 Adaptive frosted glass

Glass panels use a translucent tinted fill, backdrop blur, controlled saturation, and a layered border. The visual recipe varies by context:

- **Floating menu / tooltip:** stronger blur and higher opacity to protect legibility over moving content.
- **Inspector / drawer:** medium blur, near-opaque fill, restrained edge highlight, no busy mesh directly behind copy.
- **Dashboard card:** low translucency; opaque fallback on devices without backdrop filtering.
- **Data table / editor:** opaque surface by default; never require background visibility to read a value.

The glass material is a rendered effect, not a semantic cue. A panel must remain distinguishable when blur is unavailable or disabled.

### 3.2 Specular edge and hairline

Each elevated glass surface may use a multi-layer edge:

1. A 1 px neutral boundary at 8–12% opacity around the full perimeter.
2. A top-edge hairline at 18–30% opacity, fading toward 4–8% at the lower edge.
3. A localized accent reflection no brighter than the focus accent at 12–18% opacity.
4. A narrow inner highlight inset by 1 px where surface separation otherwise disappears.

The top-edge highlight follows the ambient key-light direction consistently across the product. Do not create independent highlight directions for adjacent cards. Nested surfaces reduce specular strength by at least 30% per level.

### 3.3 Droplet / petal material motif

The semi-translucent pet drop is a brand-level decorative form, rendered as a small glass droplet or petal-shaped lens. It may anchor the logo, loading indicator, or rare empty-state illustration. The form uses:

- A translucent accent-tinted body with an inner luminous rim.
- A broad, soft highlight offset toward the shared upper-left key-light direction.
- A darker refracted base edge and a very subtle chromatic shift.
- A silhouette that remains recognizable at 16–24 px.

The motif is not used as a generic bullet, status dot, or repeated card ornament. Avoid high-gloss realism, heavy lens distortion, or multiple competing highlights.

### 3.4 Shadow and contact model

Use a diffuse two-part shadow rather than one hard offset:

- Ambient depth: 32 px blur, 4% opacity.
- Key-light contact: 8 px blur, 8% opacity.

Separate shadow tints by theme: cool charcoal for dark mode and cool slate for light mode. Add a faint local accent bloom only for focused or selected states. Shadow intensity is reduced for translucent surfaces because border reflection already communicates separation. Never use a sharp black shadow as the only elevation cue.

### 3.5 Surface layering

- Level 0: base canvas plus optional low-opacity radial mesh field.
- Level 1: primary opaque or lightly translucent cards.
- Level 2: floating glass menus, drawers, and dialogs.
- Level 3: active hover/pressed fills, selected pills, and keyboard-focus backplates.

A higher level may overlap a lower level; it may not obscure focus indicators or important validation state. Modal overlays dim the background with a cool neutral scrim while preserving a faint silhouette of context.

## 4. Bento Architecture and Spatial Composition

### 4.1 Grid system

Use a responsive 12-column conceptual grid on desktop, collapsing to 6 columns on compact tablet and one column on narrow mobile. Content aligns to a 4 px base spacing unit with a preferred 8 px rhythm.

- Desktop page gutter: 32–48 px.
- Tablet page gutter: 24–32 px.
- Mobile page gutter: 16–20 px.
- Bento gap: 16–24 px depending on density.
- Card interior padding: 20–28 px desktop; 16–20 px mobile.
- Main content maximum width: 1,360 px unless a canvas/data view requires a wider span.

### 4.2 Asymmetric bento rules

- Use one focal card per viewport region; focal cards may span two columns or rows but must not compete in size and accent simultaneously.
- Pair one large information block with two or three compact modules. Avoid a uniform dashboard checkerboard.
- Keep repeated cards on consistent top baselines and consistent text rhythm, even where spans differ.
- Maintain optical balance with interior insets of 16, 20, or 24 px. Select one inset per component tier; do not mix arbitrary padding values.
- Related cards share material and radius. Distinct content types are differentiated by hierarchy and small accent treatments, not unrelated shapes.
- Responsive reflow preserves reading order: primary action, key summary, recent work, supporting insights.

### 4.3 Radius scale

- Desktop primary cards: 16–24 px.
- Internal nested components: 12–16 px.
- Small pills and controls: 8–12 px, with fully rounded capsules reserved for tags and status chips.
- Dialog and large drawer corners: 20–24 px.

A card family chooses a radius token and holds it across hover, active, loading, and expanded states. Radius morphing is permitted only during a shared-element transition and must settle into the destination token.

## 5. Atmospheric Depth and Texture

### 5.1 Mesh gradients and aurora

- Use low-opacity radial mesh gradients with cool midnight, violet/cobalt, or emerald tint, at 4–10% opacity on the base canvas.
- Place aurora fields behind the primary content plane, with broad gradients and no visible band boundaries.
- Keep bright centres away from large text blocks, input fields, and dense metric tables.
- Limit visible aurora anchors to one or two per viewport; movement, if present, is extremely slow and non-directional.

### 5.2 Noise gain

An optional monochrome noise overlay at 1–2% opacity may reduce perceived colour banding. The grain is static or temporally stable to avoid shimmer. It must not reduce fine text contrast, affect image exports, interfere with antialiasing, or be mistaken for data texture. Disable it for reduced-transparency modes and low-power devices if it affects performance.

### 5.3 Glitter and microtexture

“Glitter” refers to sparse spatial anchors—small glints, fine highlights, and controlled texture—not decorative sparkle. It uses the same 16/20/24 px spacing grid as interior content. Glints are limited to large glass surfaces, loading/empty-state art, and selected accent edges; they never animate continuously beside reading content.

## 6. Fluent Motion and Interaction Physics

### 6.1 Motion principles

- Every movement has an origin, destination, and interaction cause.
- Response begins immediately; perceived latency is minimized before the full transition resolves.
- Motion conveys continuity, hierarchy, and state—not decoration.
- Spring motion must settle without perceptible bounce. Overshoot is limited to 1% of travel and suppressed for reduced-motion preferences.
- Use consistent mass and damping within a component family; do not make each control feel like a different material.

### 6.2 Spring profiles

| Profile | Stiffness | Damping | Mass | Intended response |
|---|---:|---:|---:|---|
| Micro / tactile | 300 | 25 | 0.8 | Button, toggle, icon, short state shift; target response under 150 ms |
| Structural / fluid | 200 | 28 | 1.0 | Modal, drawer, accordion, larger panel transition; 250–350 ms |

Use a damped spring response (x(t)) governed by mass, stiffness, and damping. For a displacement (x), the system follows (m\ddot{x}+c\dot{x}+kx=0). The damping ratio (\zeta=c/(2\sqrt{km})) is set near or above critical damping for navigation and content surfaces; micro controls may use slight underdamping if no visible oscillation remains.

Where native spring dynamics are unavailable, use a custom ultra-smooth deceleration curve equivalent to the requested “QBaser” fallback: rapid initial response, continuous velocity, and no end snap. The fallback is a controlled cubic-bezier family calibrated against the spring profile, not a mechanical ease-in/out preset.

### 6.3 Transition timing

- Hover/focus acknowledgement: 80–120 ms.
- Button press feedback: immediate frame response; settle within 120–150 ms.
- Small popover or tooltip: 120–180 ms, anchored at trigger coordinates.
- Exiting transient element: 150–200 ms, slightly faster than entry.
- Card-to-detail/shared layout transition: 250–350 ms, matching source and destination geometry.
- Drawer/modal transition: 250–350 ms; focus moves only after the panel is interactive.
- Loading shimmer: 1.6 s per sweep, 45-degree gradient, soft continuous progression.

Do not delay information availability until animation completes. Transition duration is a visual limit, not a blocking task duration.

### 6.4 Shared layout and element continuity

When opening a card, interpolate the card’s bounding box, radius, and surface material into the full detail container. The transition preserves the title and lead visual as stable anchors. Crossfades are used only for content that cannot be geometrically morphed. When leaving, reverse the spatial path and fade slightly faster so the stage clears for incoming content.

### 6.5 Press, hover, and origin-aware controls

- Press scale: `0.97` for tactile controls, returning to `1.0` through the micro spring.
- Hover may increase border luminance and surface elevation by one subtle token; it must not shift surrounding layout.
- Tooltips, menus, and dropdowns originate at the trigger’s screen coordinate and open along the user’s natural direction of intent.
- If viewport boundaries constrain direction, reposition while preserving the trigger edge as the visual anchor.
- Hover and press states never replace keyboard focus state. Focus remains persistent and visibly distinct.

### 6.6 Loading and asynchronous work

- Use skeletons that match final content geometry to avoid layout shift.
- Shimmer sweep is 45 degrees every 1.6 seconds with low-contrast luminance movement.
- Show textual progress when a wait is longer than 700 ms; use a stable status label with the skeleton.
- Avoid binary spinner-only loading for content panels. Use a spinner only for short, compact actions where spatial footprint must remain small.
- When data arrives, crossfade the skeleton into content over 120–180 ms without moving surrounding cards.

### 6.7 Reduced motion and interruption

- Respect system reduced-motion preference and application-level motion setting.
- Replace spatial transitions with opacity or immediate state changes; eliminate continuous aurora motion and shimmer.
- Press feedback may remain as a colour/border change without scale.
- Interrupt an in-flight transition on a new user action and retarget from the current visual state; never snap back to the original state first.

## 7. Tactile Depth and Dynamic Materials by Component

### 7.1 Primary action

- Single accent-filled surface, readable high-contrast label, subtle specular top edge.
- Hover increases accent luminance by a small bounded amount; active scales to 0.97 and reduces outer shadow.
- Disabled state uses a clearly differentiated neutral fill and legible muted label; do not encode disabled state through opacity alone.
- Loading state retains action identity and replaces the leading glyph with a compact progress affordance without changing button width.

### 7.2 Secondary action

- Near-transparent Level 1 fill, visible hairline, primary text contrast.
- Hover moves toward Level 2; pressed state uses Level 3 tint.
- Destructive actions retain danger text/icon and require explicit contextual confirmation for irreversible operations.

### 7.3 Cards and bento panels

- Level 1 surface with 16–24 px radius, multi-stop diffuse shadow, and subtle top-edge highlight.
- Hover uses local highlight and no more than 2 px perceived lift; keep text and neighboring cards stationary.
- Selected cards receive an accent hairline and an explicit selection marker.
- Expanded cards morph into the detail surface with shared geometry rather than an unrelated page replacement.

### 7.4 Fields and editors

- Opaque or near-opaque dark/light fill to protect text contrast.
- A 1 px border is visible at rest; focus border and soft focus halo use the primary accent.
- Placeholder contrast is secondary and must not resemble disabled text.
- Validation color is accompanied by a message and icon; preserve entered content through validation and async transitions.

### 7.5 Menus, modals, and drawers

- Level 2 glass with more opacity than cards, strong enough blur to separate but not obscure the underlying context.
- Hairline boundary plus diffuse shadow; modal scrim darkens rather than blurs the full viewport unless content context remains useful.
- Entry originates from the initiating control when spatially meaningful; large global dialogs use a centred scale/opacity transition with stable geometry.
- Escape closes transient surfaces where safe; focus trapping, restore-to-trigger behavior, and keyboard traversal are required.

### 7.6 Status chips and pills

- Use Level 3 only for active/selected chips; neutral pills use Level 1 or transparent fill.
- State colour occupies a small icon, edge, or text marker; avoid a large saturated background for routine metadata.
- Include text labels for success, warning, danger, and processing states.

## 8. Responsive and Environmental Adaptation

- On narrow viewports, reduce card padding and bento gaps before shrinking type below readable sizes.
- Collapse multi-column bento to one reading column; preserve the focal card and primary action at the top.
- Glass blur and backdrop saturation reduce on low-power hardware; opaque tokens provide equivalent hierarchy.
- High contrast mode replaces translucent borders with solid outlines and maintains all functional distinctions.
- Theme changes interpolate surface tokens over 180–240 ms only when reduced motion is not enabled; content and focus never disappear during the transition.
- Browser zoom and text scaling preserve control hit areas and do not truncate primary labels.

## 9. Visual Quality and Acceptance Criteria

- **Contrast:** body text meets WCAG AA minimum; critical labels and focus indicators are verified at actual rendered sizes. AAA is the target for primary reading surfaces.
- **Hierarchy:** each viewport has one dominant focal point, one primary action, and no more than two high-chroma attention anchors.
- **Surface distinction:** all four elevation levels remain distinguishable in dark and light themes without shadow dependence alone.
- **Glass fallback:** every frosted surface remains legible with backdrop blur disabled.
- **Motion continuity:** a new interaction retargets from current position and velocity; no sudden snap, double animation, or blocked action occurs.
- **Loading stability:** skeleton dimensions match final content closely enough to prevent visible layout jumping.
- **Density:** 16/20/24 px inset rhythm remains consistent within a component family; corner radius remains consistent across states.
- **Accessibility:** focus, selection, and status are not communicated by colour or motion alone; reduced motion and high contrast preferences are honored.
- **Material restraint:** noise, aurora, highlights, and shadows remain subordinate to experiment content and are disabled or reduced when they impair clarity.
