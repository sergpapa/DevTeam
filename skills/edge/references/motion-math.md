# Edge — motion math & algorithms reference

The creative-coding repertoire behind the direction's effects (Frank's Laboratory canon + Codrops/Awwwards circuit staples), with the actual math and the constants that make them feel right. Vanilla-first: most of this needs zero libraries.

## Easing, lerp, and springs (the feel layer)

**Named easings** (t ∈ [0,1]):
```js
const easeOutCubic = t => (--t)*t*t + 1;
const easeOutExpo  = t => t === 1 ? 1 : 1 - Math.pow(2, -10*t);
const easeInOutCubic = t => t < 0.5 ? 4*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1;
```
Expo/quint-out = decisive arrival (entrances, CTAs). InOut-cubic = floaty (scroll-linked). CSS `linear()` can now encode sampled spring curves natively.

**Lerp follow ("lag = luxury") — use the frame-rate-correct form:**
```js
// naive (breaks on 144Hz displays): value += (target - value) * k   // k ≈ 0.05–0.15
// correct — identical feel at any frame rate:
value += (target - value) * (1 - Math.exp(-lambda * dt));  // dt in seconds
// half-life of the gap = ln(2)/lambda; lambda ≈ 6–10 feels like k≈0.1 at 60fps
```
This drives every custom cursor, smooth-scroll, camera-follow, and parallax trail. Two-part cursors use two lambdas (dot fast, ring slow).

**Spring (damped harmonic oscillator)** — for anything that must inherit velocity (drag release, hover interrupts):
```js
// F = -stiffness*x - damping*v ; integrate each frame
a = (-stiffness * (pos - target) - damping * vel) / mass;
vel += a * dt;  pos += vel * dt;
```
UI-tuned starting point: stiffness 200, damping 12, mass 1–1.75. Tune with real interrupt gestures, not one play-through. Duration-eased tweens visibly "reset" on interrupt; springs don't.

## Noise & flow fields (organic motion)

**Why noise, not `Math.random()`:** noise is coherent — nearby inputs give nearby outputs — so motion looks continuous/organic. Default to **simplex** (fewer grid artifacts, cheaper in higher dimensions than classic Perlin).

**fBm (octave stacking)** — richer texture from any noise:
```glsl
float fbm(vec2 st){ float v=0., a=.5;
  for(int i=0;i<5;i++){ v += a*noise(st); st *= 2.0; a *= 0.5; } return v; }
```
4–6 octaves typical. **Domain warping** `fbm(p + fbm(p + fbm(p)))` gives liquid/marble looks at 2–3× cost.

**Flow field (the ambient-background workhorse):**
1. Grid of angles: `angle(col,row) = noise(col*inc, row*inc, t) * TWO_PI * mult`.
2. Particle looks up its cell: `(floor(x/cell), floor(y/cell))`.
3. Advect: `x += cos(angle)*speed; y += sin(angle)*speed`.
4. Recycle off-canvas particles to a random edge; draw trails by fading with a low-alpha fillRect instead of clearRect.
Regenerate the angle grid every ~30 frames, not per frame — noise evaluation is the bottleneck.

**Curl noise** — genuinely fluid-looking swirls (divergence-free by construction):
```
a = (noise(x, y+eps) - noise(x, y-eps)) / (2*eps)
b = (noise(x+eps, y) - noise(x-eps, y)) / (2*eps)
velocity = (a, -b)   // perpendicular gradient of a noise potential
```
~4 noise samples per particle per frame; use when "wavy" isn't enough and it must swirl like smoke/ink.

## Canvas2D particle canon

**Base architecture:** `Particle` class (`x,y,size,vx,vy`) + an `Effect` owner holding the array, mouse state, and resize handling; one `update()+draw()` pass per rAF tick.

**Text/image → particles (rasterize-and-seek):**
1. Draw text/logo to an offscreen canvas ONCE (at setup/resize, never per frame).
2. `getImageData`, walk pixels with a stride (every 3rd–5th), collect `{x,y}` where alpha > threshold as targets.
3. Each frame: `p.x += (p.target.x - p.x) * ease` (ease ≈ 0.05–0.1) — the lerp seek.
4. Mouse repulsion: if `dist(mouse,p) < radius`, push along the mouse→particle vector scaled `force/dist`; the seek pulls it back after.
Budget: hundreds of particles, not tens of thousands.

**Constellation / linking lines:** drifting particles; for each pair within `maxDist`, draw a line with `opacity = 1 - dist/maxDist`. Pairwise checks are O(n²) — see spatial hashing below. Layer two canvases (blurred front for glow, crisp back for lines) for the liquid variant.

**Parallax layers:** each background layer scrolls at `x -= delta * layer.speedFactor`, wrapping by modulo; draw the wrapped copy immediately adjacent to avoid seams.

## Shader / WebGL staples

**Image displacement (the hover/transition workhorse):**
```glsl
vec2 distortedUV = uv + (texture2D(dispMap, uv).r - 0.5) * strength;
gl_FragColor = texture2D(image, distortedUV);
```
Displacement source = grayscale map, noise, or a mouse-velocity "flowmap" that accumulates and fades — then intensity scales with gesture speed. Clamp strength near edges (UVs outside [0,1] smear).

**Iris/radial wipe with organic edge** (signature transition observed in the wild): radial mask from center + `snoise(uv * period + speed * time)` perturbing the mask edge + circular vignette. Reads as liquid/hand-crafted instead of a stock crossfade.

**RGB shift / chromatic aberration:** sample R/G/B at slightly different UV offsets along the to-mouse vector — strong "digital" punctuation; use sparingly.

**Gooey/metaball without WebGL:** SVG filter `feGaussianBlur` → `feColorMatrix` alpha `18 -7` (blur then threshold), or CSS `filter: blur(20px) contrast(30)`.

**Raymarching/SDF:** march rays by distance-to-scene steps; shapes blend via `min`/smooth-min — morphing blobs with no mesh. Hero-only cost: cap steps, render at reduced resolution and upscale.

**GLSL arithmetic staples:** `mix` (lerp), `smoothstep` (soft threshold — anti-aliased edges), `fract` (tiling). Write new shader work in TSL (Three.js) so it runs on both WebGPU and WebGL2.

## Scroll choreography math

- **Normalized progress:** `p = clamp((scrollY - start) / (end - start), 0, 1)` — everything maps from this. Remap with `gsap.utils.mapRange`/`interpolate`.
- **Scrub smoothing:** `scrub: 1` (seconds of lag) = the lerp-follow feel applied to a timeline playhead.
- **Skew-on-velocity:** `skew = clamp(scrollDelta * sensitivity, -maxSkew, maxSkew)`, tween back to 0 on stop. Always clamp — trackpad flings break unclamped skew.
- **Lenis + ScrollTrigger sync** (the one integration everyone gets wrong):
```js
const lenis = new Lenis();
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add(t => lenis.raf(t * 1000));
gsap.ticker.lagSmoothing(0);
```
- **Marquee:** duplicate content once (`[A][A]`), animate track `translateX(-50%)`, linear, infinite — the 50% point is an invisible modulo reset. Both copies must stay byte-identical or the seam jumps.
- **Split-text reveals:** GSAP SplitText (3.13+: free, aria built in, `autoSplit` re-splits on resize) with `yPercent: 100→0` inside masked line wrappers, stagger 0.02–0.08s, expo-out. Always `.revert()` on cleanup.
- **Variable-font axes:** drive `font-variation-settings` from scroll (pure CSS `animation-timeline: scroll()`) or cursor proximity (rAF-batched JS). It triggers reflow — headlines only, never paragraphs.

## The 60fps rules

1. **Animate `transform`/`opacity` only** in DOM land; everything else risks layout/paint per frame (including `font-variation-settings` — budget it).
2. **`will-change` discipline:** add just before animating, remove after; permanent will-change wastes GPU memory per layer.
3. **Offscreen canvas for one-time raster work** (text→particle maps) — never `getImageData` in the render loop.
4. **Cap DPR:** `Math.min(devicePixelRatio, 2)` — 3× phones render 9×/4× the pixels for nothing.
5. **Spatial hash for neighbor checks:** bucket particles into cells sized ≈ interaction radius; test same+adjacent cells only. Real-world: 203ms → 4ms/frame at 5k particles. Quadtree only when density is very uneven.
6. **IntersectionObserver-gate every rAF loop and ScrollTrigger** — off-screen canvases must not burn frame budget.
7. **`prefers-reduced-motion` is NOT automatic for JS:** the CSS media query silences only declarative animation. Check `matchMedia('(prefers-reduced-motion: reduce)')` in every rAF/IO-driven effect and bail to the static state.
8. **INP ≤ 200ms is the modern constraint:** long main-thread animation work during interactions now fails Core Web Vitals. Prefer CSS scroll-driven animations (off-main-thread) for simple scrubs; keep click handlers free of heavy tween setup.
