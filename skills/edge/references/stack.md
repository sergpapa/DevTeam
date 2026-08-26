# Edge — the all-free stack (verified Aug 2026)

Hard rule: **free-for-commercial only.** "Free to try", "free for personal use", and export-gated editors are paid tools. Check the actual license page before adding anything; licensing facts below were verified against official sources in Aug 2026 — re-verify if much time has passed.

## Core stack

| Layer | Pick | License | Notes |
|---|---|---|---|
| Framework | **Astro** (content sites) / Next.js/Nuxt 3 (app-like) | MIT | Islands/SSR fixes the genre's classic "empty div for crawlers" failure. Real HTML first; hydrate effects on top. |
| Animation engine | **GSAP 3.13+** incl. ScrollTrigger, ScrollSmoother, **SplitText**, DrawSVG, MorphSVG, CustomEase, Flip | Free since May 2025 (Webflow acquisition) — proprietary no-charge license, NOT OSS; only forbidden use is building a competing no-code animation builder | The entire 2019 "Club GreenSock" paywall is gone. New SplitText: 50% smaller, aria built in, `autoSplit`. |
| Engine alternatives | **Motion** (motion.dev) — MIT, vanilla+React+Vue, WAAPI-accelerated · **anime.js v4** — MIT, springs/draggable/scroll | MIT | Zero-caveat licenses; GSAP still wins for complex timeline orchestration. |
| Smooth scroll | **Lenis** | MIT | Wraps native scroll (keyboard/AT keep working). Replaces Locomotive and every hand-rolled virtual-scroll rig. |
| Page transitions | **View Transitions API** (native, incl. cross-document MPA) | — | Chrome 111+/126+ (cross-doc), Safari 18/18.2+, Firefox 144+ same-doc. Progressive enhancement via `@supports`; replaces Barba/custom routers. |
| Scroll scrubbing | **CSS scroll-driven animations** (`animation-timeline: scroll()/view()`) | — | Chromium 115+, Safari 18+; Firefox still flagged → `@supports` with ScrollTrigger fallback. Off-main-thread = free INP headroom. |
| 3D scenes | **Three.js WebGPURenderer + TSL** (auto-fallback WebGL2) | MIT | WebGPU ≈95% coverage (Chrome 113+, Safari 26+, Firefox 141+ Win). Write shaders in TSL, not raw GLSL — runs on both backends. |
| Light WebGL effects | **OGL** (Unlicense) · **curtains.js** (MIT) — DOM-synced displacement planes · **Pixi.js** (MIT) — heavy 2D | free | Use these instead of full Three.js when the effect is an image-distortion layer, not a 3D world. |
| Vector animation | **Lottie / dotLottie** players + Bodymovin AE exporter | MIT | ⚠ The **Rive editor free tier cannot export .riv files** ("free to create, $9/mo to ship") — treat Rive as paid. Runtimes are MIT but useless without the editor. |
| Canvas effects | Vanilla Canvas2D (see `motion-math.md`) | — | Several award winners are pure Canvas2D. Cheapest tech that achieves the effect wins. |

## Modern CSS that replaces 2019 machinery (all safe, use freely)

`clamp()` fluid type (kills breakpoint piles) · container queries · `:has()` · OKLCH + `color-mix()` (perceptual token ramps) · CSS nesting · `linear()` easing (spring curves in pure CSS) · `text-wrap: balance` (headlines) · scroll snap · `overscroll-behavior` · `content-visibility` (long story pages render lazily) · native `<dialog>`/Popover (focus-trapped overlays for free) · `@property` and Anchor Positioning as progressive enhancement.

## Media rules (the anti-8MB-homepage kit)

- Images: **AVIF first**, WebP fallback via `<picture>`; explicit `width`/`height` always (CLS); `loading="lazy"` below the fold; `fetchpriority="high"` on the ONE hero/LCP image (never combined with lazy).
- Background video: poster image + `preload="metadata"` (or `none`) + IntersectionObserver play/pause + per-viewport `<source media>` + AV1 with H.264 fallback. Reduced-motion users get the poster, full stop.
- 3D/effect bundles: dynamic-import after first paint; static poster on constrained devices; `OffscreenCanvas`/worker for heavy scenes.
- Budgets on throttled mobile: **LCP < 2.5s · INP ≤ 200ms · CLS < 0.1** — award juries and search both grade on these now.

## Free font map (self-host woff2; never Adobe Fonts/Typekit — subscription-gated)

| Role | Free picks (license) | Replaces (paid) |
|---|---|---|
| Neo-grotesk workhorse | **Inter**, Archivo, Assistant (OFL) · **General Sans** (Fontshare FFL) | GT Walsheim ($720/family), Gilroy (ambiguous license — treat as unsafe) |
| Swiss grotesk | **Switzer** (Fontshare — built as the Suisse alternative), Inter, IBM Plex Sans | Suisse Int'l, Neue Montreal ("free" = personal-use only) |
| Display headline | **Clash Display** (Fontshare), **Space Grotesk** (OFL), Archivo Expanded | — |
| Heavy poster caps | **Bebas Neue**, **Anton**, **Archivo Black** (OFL) | Integral CF (commercial = paid) |
| Chunky display | **Unbounded**, **Bungee** (OFL) — hand-tune tracking | Grumpy Black 24 |
| Editorial serif | **Fraunces**, **Instrument Serif** (OFL) · **Butler** (confirmed free incl. commercial) | PP Editorial New, Didot-class |
| Mono (meta/labels/code) | **JetBrains Mono**, **IBM Plex Mono**, Space Mono (OFL) | — |

Sources: **Google Fonts** (license pre-vetted, gold standard) · **Fontshare** (ITF FFL — free commercial, can't resell the font file itself) · **Uncut.wtf** (curated indie, verify per font) · Font Squirrel (useful filter, always open the bundled license). Non-Latin scripts: prefer system stacks (e.g. Yu Gothic/Hiragino for JP) over multi-MB webfonts.

## Services

- **Hosting:** **Cloudflare Pages** (unlimited bandwidth, no commercial restriction) or **Netlify free** (explicitly allows commercial use; 100GB/mo). ⚠ **Vercel Hobby forbids commercial use**; GitHub Pages forbids transactional sites (pure showcase OK). Every "free" host is metered (build minutes, bandwidth, invocations) — state the limits when you recommend one, and never connect or deploy to the user's account yourself without approval (money rule, CLAUDE.md).
- **Content:** repo-native first — **Astro content collections / markdown**, or **Decap CMS** (MIT, free forever) when an editor UI is needed. Hosted free tiers that are genuinely usable: Sanity (10k docs), Prismic (unlimited docs, 1 user). **Payload** (MIT) when a real admin + relational content is required.
- **Analytics:** if needed, a lightweight self-hosted option (e.g. Umami/Plausible self-hosted, both OSS) beats resurrecting the GA tag graveyard every 2019 site still carries.

## Progressive-enhancement ladder (how to ship cutting-edge safely)

1. Server-rendered HTML with real content — works with zero JS.
2. CSS layer: fluid type, inversion, scroll-driven reveals, `linear()` springs — works in every modern browser, degrades silently.
3. JS layer: Lenis + GSAP choreography, gated behind `prefers-reduced-motion` checks.
4. GPU layer: WebGL/WebGPU signature moment, IntersectionObserver-gated, poster fallback.
5. Frontier layer (`@supports`/feature-detect): View Transitions, scroll-driven animations, Anchor Positioning, Speculation Rules (Chromium-only prefetch).

Each layer must leave the site fully usable if every layer above it fails to load.
