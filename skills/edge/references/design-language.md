# Edge — design language reference

Two parts: the **six direction profiles** (dial presets — pick one, override deliberately), then the **shared vocabularies** (the numbers and moves every profile draws from). Every number is a proven default, not a law — deviate deliberately and consistently, never accidentally.

## Part 1 — Direction profiles

Each profile sets the six dials (palette / type dominance / motion temperature / ornament / narrative / density). Overrides are allowed and normal — record them in the spec. Dials never drift mid-project.

### Swiss revival — "We are rigorous"
- **Dials:** paper off-white ground + ink + one flat accent (classically red) · type-as-hero · motion precise-and-quick (0.3–0.6s, quart-out, minimal lag) · ornament = exposed structure at full volume (rulers, gridlines, index numbers, mono meta) · narrative = editorial index · density = structured, disciplined whitespace.
- **Type:** one grotesk family doing everything at extreme size contrast is the Swiss move (Switzer, Inter, Archivo, Helvetica-class). Optional mono for meta.
- **Signature shortlist:** masked line reveals · edge-pinned type · visible grid as graphic · marquee word-bands · hard inversion between chapters.
- **Watch-outs:** no gradients, no soft shadows, no decorative easing — violations must be compositional (a broken column), never ornamental.

### Brutalist — "We are unfiltered"
- **Dials:** harsh B/W + one violent accent — the one profile where pure `#000`/`#fff` is correct · type-as-hero (oversized system/mono faces) · motion **raw-instant**: no smoothing, no lerp, hard cuts, instant hover states — the snap IS the statement · ornament = raw HTML (underlined links, hard 1–2px borders, no radius, visible seams) · narrative = flat index/list · density = deliberately awkward asymmetry.
- **Type:** system stack, JetBrains/IBM Plex Mono, Archivo Black, Space Grotesk — weight and size over refinement.
- **Signature shortlist:** hard-cut section inversion · giant underlined links as nav · crosshair/default cursor (no follower) · table-like layouts · unstyled-looking buttons that are pixel-considered.
- **Watch-outs:** brutalism is *composed* rawness — the grid still exists underneath, and floors never flex: "ugly on purpose" ≠ low contrast, missing focus states, or keyboard traps.

### Dark-luxury — "We are exclusive"
- **Dials:** near-black ground **throughout** (no inversion rhythm — one continuous dark world), warm off-white ink, metallic/muted accent (`#d4af37`-family) used rarely · type-as-hero via a serif display voice · motion slow-and-weighted: 0.8–1.4s heroes, expo-out, heavy lerp lag — the slowest flavor · ornament = minimal-elegant (hairlines, small caps, folio numbers; no index-number tech ornament) · narrative = ceremonial lookbook pacing · density = maximum ma; vast negative space is the luxury signal.
- **Type:** Fraunces / Instrument Serif / Butler for display + a quiet grotesk (Inter, Switzer) for UI.
- **Signature shortlist:** serif hero at enormous scale · slow crossfade/vignette or iris image transitions · gold hairline dividers · lerped cursor ring at the slowest factor.
- **Watch-outs:** muted gold on near-black fails AA easily — verify every accent use; slow applies to hero moments only, micro-interactions stay 0.3s or the UI feels broken.

### WebGL-immersive — "We can build anything"
- **Dials:** the scene/render carries ALL color; UI chrome strictly neutral mono · **scene-as-hero** — type recedes to small mono/grotesk UI labels · motion cinematic-scrubbed (camera moves, physics, drag) · ornament = HUD-like mono meta (coordinates, counters, "SCROLL" prompts) · narrative = spatial exploration (drag-to-browse world, scroll-driven camera) · density = canvas-first, minimal DOM chrome.
- **Type:** one mono + one plain grotesk, small and utilitarian — type deliberately the least important element.
- **Signature shortlist:** the scene IS the motif — bespoke shader transition (noise-perturbed wipe), draggable canvas world, cursor-as-lens with spring physics, branded two-tone preloader.
- **Watch-outs:** heaviest floors burden of any profile — HTML content mirror + `<noscript>`, poster fallback on constrained devices, drag alternatives (WCAG 2.2 §2.5.7), DPR cap, bundle deferred past first paint. Spend the entire flair budget on the scene; every other surface is plain CSS.

### Editorial / fashion — "The imagery is the product"
- **Dials:** desaturated chrome, photography carries color · image-led with high-contrast serif display moments (mixed roman/italic within one headline is the genre move) · motion gentle, triggered-once reveals · ornament = print devices (captions, folios, ruled lines) · narrative = lookbook flow, generous sequencing · density = airy, image-forward.
- **Type:** Fraunces / Instrument Serif display + neutral grotesk captions; scale contrast between huge serif and tiny caption meta.
- **Signature shortlist:** image-over-type overlap · italic/roman mixing · restrained parallax on imagery · caption-as-ornament · quiet page-long crossfades.
- **Watch-outs:** image weight is the perf risk — AVIF, lazy below fold, `fetchpriority` on the LCP hero; serif at small sizes needs a contrast check.

### Hybrid (creative-studio default) — "Craft + taste + skill"
- **Dials:** off-black or warm-paper ground + 1 accent (or strict grayscale letting work carry color) · type-as-hero with ONE distinctive display face · motion weighted-smooth — the lag-=-luxury flavor (lerp 0.05–0.15) · ornament = exposed structure in moderation (index numbers, mono meta) · narrative = two-beat storyboard (hook: huge type + ambient motion → reward: proof + one CTA) ending in footer-as-final-scene · density = balanced with real ma.
- **Type:** General Sans / Space Grotesk / Clash Display display + Inter-class workhorse + mono meta.
- **Signature shortlist:** two-part lerped cursor with `difference` blend · ghost numerals · section inversion rhythm · skew-on-scroll-velocity grids · ambient Canvas2D field behind content · per-letter hero reveal.
- **Watch-outs:** the genre's most crowded flavor — the signature-motif choice is the differentiation; without a distinctive motif this profile collapses into "generic award site."

**SaaS/product wearing any profile:** keep conversion architecture boring and legible — flair lives on surfaces (hero, gradients-as-taxonomy, tinted code windows, section seams), never on the path to sign-up. Trust content (badges, SLAs, legal) lives inside the same visual system, not quarantined.

## Part 2 — Shared vocabularies

### Typography numbers

- Hero/display: 10–20vw equivalent through ONE fluid formula: `font-size: clamp(2.5rem, 12vw, 9rem)`. Never per-breakpoint px piles (observed field bug: headline larger on a 500px phone than a 700px tablet).
- Display line-height **0.85–1.0** (type as graphic block); body 1.4–1.6 (clarity wins).
- Display tracking **−0.01 to −0.04em**, tighter as size grows; labels/eyebrows 11–13px uppercase **+0.05 to +0.2em**, often mono.
- The core hierarchy device: extreme size gap between display and tracked micro-labels (spreads of 10–25× observed) — hierarchy through scale + tracking, not color or weight piles.
- Two families + optional mono, separated by *role* (voice vs reading vs meta). Kinetic/split type: hero and transitions only — never body, never nav.

### Color numbers

- Off-blacks `#0a0a0a`–`#141414` · warm papers `#f2f0ec`/`#f5f3ee`/`#faf9f6` (pure `#000`/`#fff` belongs to brutalism).
- Genre accents: acid green `#c5f74f`/`#d4ff3f` · signal orange `#ff4d00` · electric blue `#0047ff` · gold `#d4af37`.
- Pick the accent hue from the client's industry semiotics (hazard-red for construction, acid green for music tech), not a generic brand color. Near-duplicate hue families of one accent (5+ close reds inside one illustration) add texture without breaking the one-accent rule.
- Low chroma overall is why the single accent dominates without volume — a spot-color mechanism. Tokenized ramps/gradient taxonomies are the disciplined-SaaS variant: fixed gradient angle, rotating hue pair per product area.
- Define tokens in OKLCH; derive hover/tint ramps with `color-mix()`. Floors: 4.5:1 body, 3:1 large text and UI boundaries — in every ground the palette uses.

### Composition moves

- 12-col fluid grid, 24–32px gutters, 8px spacing base, scale 1.25/1.333 (1.618 display-only), round spacing to 4px multiples.
- Asymmetric balance (weight, not mirroring); negative space as an active element.
- Layering (image over type over index number) for depth without 3D; edge-pinned type makes the frame feel exceeded.
- Exposed structure: index numbers `01`–`04`, hairlines, mono metadata — rigor as ornament.
- Ghost layering: duplicate numeral/word behind itself, low opacity, small offset.
- Pinned sections (`position: sticky` / ScrollTrigger pin) for one-moment-per-view. Horizontal scroll: ONE bounded section max, visible arrow affordance, stacks vertically on mobile.
- Footer-as-destination: full-height final scene — closing statement, the terminal CTA (visually isolated from utility nav), one consistent CTA phrase repeated across all modules.

### Motion numbers

- Easings: expo-out `cubic-bezier(0.16,1,0.3,1)` (entrances) · quart-out `cubic-bezier(0.25,1,0.5,1)` (UI) · field signature `cubic-bezier(.19,1,.22,1)` (hovers). Linear only for marquees.
- Durations: 0.6–1.2s hero (dark-luxury stretches to 1.4s) · 0.3–0.6s micro · 0.5–0.7s scroll-triggered headings. Staggers 20–100ms; 60–100ms sweet spot.
- Reveal grammar: masked lines translating up into view; secondary elements settle one stagger-beat after the primary (follow-through).
- Follower lerp factor 0.05–0.15 (frame-rate-correct form in `motion-math.md`); two-part cursor = two factors (dot fast, ring slow), `mix-blend-mode: difference`. Applies only where motion temperature is weighted-smooth or cinematic — never in brutalist raw-instant.
- Scrub only where 1:1 coupling IS the experience; trigger-once for content reveals. Arbitrary mixing is the clearest unpolished-build tell.
- Transitions: View Transitions API first; an authored beat (wipe, inversion flash, logo hold), not a hard cut — unless the profile's temperature is raw-instant, where the hard cut is the beat.
- Preloaders must earn the delay: counter tied to REAL load progress, or a hero first-paint; two-tone logo crossfade is a proven cheap identity. Fake progress is an anti-pattern.

### Anti-patterns (with the reason)

1. **Whole-page scroll-jacking** — breaks keyboard/AT users outright; pin bounded sections instead.
2. **Multi-MB first paint** (hero video/3D bundle) — trades LCP for a flourish; award juries treat perf failure as disqualifying.
3. **Text living only in canvas/WebGL/video** — unselectable, uncrawlable, invisible to AT.
4. **Identical reveal on every element** — erases the hierarchy motion exists to create.
5. **Fake-progress preloaders** — added latency with no informational payoff.
6. **Kinetic type on body/nav** — fights readability, AT, and CLS simultaneously.
7. **Horizontal scroll as primary navigation** — high interaction cost, no desktop convention.
8. **Contrast sacrificed to vibe** — spend "quiet" on spacing and restraint, never on washing out type.
9. **Laggy custom cursor everywhere** — fine as flourish; failure in inputs/maps/precision contexts.
10. **Zero reduced-motion path** — the single most consistent failure across every field site studied; cheapest floor to meet, first thing to check.
11. **Grid violations without a grid** — reads as accident, not brutalism.
12. **Dial drift / token drift** — mixing motion temperatures mid-site, two spacing generations, near-duplicate hexes accreting. Consolidate; don't only add — drift undercuts exactly the "every pixel considered" feel this direction sells.
