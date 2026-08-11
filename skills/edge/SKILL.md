---
name: edge
description: Edgy-modern (award-grade) web design direction. Invoke BEFORE designing any user-facing site/UI that should feel bold, premium, or experimental — triggers on "edgy", "award-winning", "Awwwards-style", "brutalist", "immersive", "premium portfolio/agency site". Structured as five universal laws + six named dials + six direction profiles (Swiss, brutalist, dark-luxury, WebGL-immersive, editorial, hybrid), with a free-tools-only stack and non-negotiable accessibility/performance floors.
---

# Edge — the edgy-modern design direction

This is a **direction, not a template** — distilled from award-circuit sites (Awwwards/CSSDA/FWA class) and the principles behind them. The skill has three altitudes with different force:

- **Laws** — five rules that hold across every flavor of the genre. Never vary.
- **Dials** — six named axes every project sets ONCE, explicitly, in the spec. This is where creative decision-making lives.
- **Profiles** — six presets of the dials (one per sub-style). Pick one, then work freely *within* it; override any dial deliberately and record the override in the spec. Never drift a dial mid-project — drift is what reads as amateur.

Deeper references in this skill's folder — load only what the task needs:
- `references/design-language.md` — the six direction profiles (dial sheets + signature-move shortlists), and the shared vocabularies with concrete numbers (type, color, composition, motion), anti-patterns.
- `references/motion-math.md` — algorithms and constants: particles, flow fields, noise, lerp/spring math, shader staples, scroll choreography, 60fps rules.
- `references/stack.md` — the current all-free stack, paid→free font map, hosting/CMS notes, progressive-enhancement ladder.

## The Laws (apply to every build, every profile)

1. **One hero motion moment per view.** Each screenful gets a single authored animation; everything else stays quiet. When everything animates, nothing matters.
2. **One signature motif, echoed everywhere.** Pick ONE bespoke device (a shader wipe, a particle field, a brush stroke, a hard-cut inversion) and run it consistently across cursor, reveals, and transitions. A motif reads as authored; a grab-bag of effects reads as a template.
3. **The seams are branded.** Preloader, page transition, menu-open state, hover, 404, footer — every in-between state is designed brand real estate, never a browser default.
4. **Flair budget discipline.** Spend experimentation where users *explore* (hero, transitions, footer); stay boring where users *do* (nav labels, forms, body copy, error states). CTAs say plain words.
5. **The system must exist to be broken.** A real grid, one modular scale, named tokens — violations (broken grid, clashing type, harsh cuts) read as intentional only against a system that is otherwise followed. Deviate deliberately and consistently, never accidentally.

## The Dials (set each one explicitly in the spec, at the start)

| Dial | Range |
|---|---|
| **Palette policy** | strict grayscale ↔ mono + 1 accent ↔ tokenized ramp/gradient taxonomy ↔ scene/imagery carries all color |
| **Type dominance** | type-as-hero (display face does the talking) ↔ image/scene-as-hero (type recedes to mono UI) |
| **Motion temperature** | raw-instant (no smoothing — the snap is the statement) ↔ weighted-smooth (lerp lag = luxury) ↔ cinematic-scrubbed (scroll/camera coupling) |
| **Ornament vocabulary** | exposed structure (index numbers, rulers, mono meta) ↔ raw-HTML brutalist ↔ minimal-elegant (hairlines, small caps) ↔ none |
| **Narrative shape** | two-beat storyboard (hook → proof + CTA) ↔ flat index/list ↔ lookbook flow ↔ conversion architecture |
| **Density & whitespace** | ma-luxury sparse ↔ structured-editorial ↔ dense/deliberately awkward |

## Step 1 — Pick the profile from the brand, not from taste

| Profile | The brand statement | Reach for it when |
|---|---|---|
| Swiss revival | "We are rigorous" | Design systems, editorial, institutions |
| Brutalist | "We are unfiltered/independent" | Music, art institutions, counter-positioning |
| Dark-luxury | "We are exclusive" | Fashion, hospitality, high-ticket services |
| WebGL-immersive | "We can build anything" | Campaigns, launches, creative-dev portfolios |
| Editorial | "The imagery is the product" | Fashion, photography, magazines |
| Hybrid (default) | "Craft + taste + skill" | Studios, agencies, portfolios, ambitious SaaS |

Full dial sheets with type/palette guidance, signature-move shortlists, and per-profile watch-outs are in `design-language.md`. State the chosen profile, its dial settings, and any overrides in the spec.

## Step 2 — Define the system before composing any page

Write these tokens into the spec/CSS custom properties first; pages come after:
- **Type:** faces per the profile, from the free-font map in `stack.md`. Hero scale via a single `clamp()` formula (never per-breakpoint px overrides). Numbers (leading/tracking/label treatment) in `design-language.md`.
- **Color:** ground, ink, accent as OKLCH-derived tokens per the palette dial; verify WCAG AA (4.5:1 body, 3:1 large) in EVERY ground the palette uses.
- **Grid & spacing:** 12-col fluid, 8px base unit, one modular scale (1.25 or 1.333; 1.618 only for display jumps).
- **Motion vocabulary:** 2–3 named easings max, one duration set, one stagger window, one lerp factor — all per the motion-temperature dial. Same numbers everywhere; consistency is what reads as craft.

## Step 3 — Choose the signature moment and the cheapest tech that achieves it

Climb this ladder only as far as the effect requires — the premium feel comes from timing, typography, and restraint, not shader complexity (several award winners are Canvas2D or pure CSS):
1. **CSS only** — inversion, marquees, masked line reveals, scroll-driven scrubbing, `linear()` springs.
2. **Canvas2D** — particle fields, constellation/flow-field backdrops, text-to-particles (algorithms in `motion-math.md`).
3. **SVG filters** — gooey/metaball, line-draw.
4. **WebGL effects layer** (OGL/curtains.js) — image displacement transitions, hover distortion.
5. **Full 3D scene** (Three.js WebGPURenderer + TSL, WebGL2 fallback) — only when the 3D world IS the hero moment (the WebGL-immersive profile).

Scroll effects: **scrubbed** only where 1:1 scroll coupling is the point (pinned sequence, horizontal gallery); **triggered-once** for everything else so the page never fights the user's scroll speed. Never hijack the whole page's scroll.

## Step 4 — Build on the free stack

Use `stack.md` for the current recipes. Non-negotiable sourcing rule: **free-for-commercial only** — check the actual license, not the download button ("free to try"/"personal use" fonts and export-gated editors are paid tools in disguise). GSAP + all its plugins, Lenis, Three.js, and the whole font map in `stack.md` are verified free.

## The Floors (violating any of these fails review — every profile, no exceptions)

- **Reduced motion:** honor `prefers-reduced-motion` in CSS *and* JS (`matchMedia`) — kill parallax/kinetic type/cursor followers, swap video to poster. The genre's biggest recurring failure; treat as a first-class design surface.
- **Keyboard & focus:** full keyboard path through every pinned/overlay/drag interaction; styled `:focus-visible` (never bare outline removal); drag-to-browse UIs get a click/arrow alternative (WCAG 2.2 §2.5.7). Custom cursor elements are `aria-hidden` and die on touch/reduced-motion. Never disable pinch-zoom (`maximum-scale`/`user-scalable=no` are forbidden).
- **HTML-first:** real headline/copy/CTA in server-rendered DOM (SSR/islands); canvas/WebGL hydrates on top as enhancement. Text never lives only inside canvas/video. `<noscript>` carries the headline + CTA.
- **Performance:** LCP < 2.5s, INP ≤ 200ms, CLS < 0.1 on a throttled mobile profile. Transform/opacity only; DPR capped at 2; rAF loops gated by IntersectionObserver; AVIF-first images; video = poster + `preload="metadata"` + pause off-screen + per-viewport sources. Defer 3D bundles past first paint; static poster on constrained devices.
- **Responsive by design (375/768/1440):** the mobile experience is designed, not "whatever's left" — horizontal sections stack, WebGL degrades to poster, type steps down via the `clamp()` minimum.

Note: "brutalist" flexes aesthetics, never floors — composed rawness still meets contrast, keyboard, and reduced-motion requirements.

## Anti-pattern quicklist (the ways this genre fails)

Whole-page scroll-jacking · multi-MB hero video/JS before first paint · text baked into canvas · identical reveal on every element · decorative preloaders that fake progress · kinetic type on body copy or nav · horizontal scroll as primary navigation · contrast sacrificed to vibe · cursor hidden with a laggy replacement everywhere · shipping with zero reduced-motion path · dial drift mid-project. Full list with reasons in `design-language.md`.

## Pipeline integration

- Inside `/feature`: this skill informs Stage 0 (spec gets the profile + dial settings + tokens + signature moment) and Stage 1 (architect brief names the stack from `stack.md`). Tests still come first; the direction changes *what* is built, not the TDD order.
- Brief **design-reviewer** with the chosen profile, its dial settings, and the floors — review against the direction's own rules, not generic heuristics. Dial drift is a reviewable defect.
- The responsive check and `/verify` run as usual; add a reduced-motion pass (emulate `prefers-reduced-motion`) to the verification checklist for any build using this skill.
