# Nightfall at the March Castle — art direction

The specification other agents build from. Nothing here is code. Everything here
must be buildable by `blender-model` and `blender-texture` from a written brief,
because the whole point of the page is:

> Every object in this scene was generated from a one-paragraph brief by an AI
> using this skill. Every build script is in the repo.

If a decision in this document cannot survive that sentence, it is a bad
decision and should come back to me rather than be quietly faked.

---

## 0. Read this before anything else

### 0.1 Why night is not a mood choice

It is the fidelity budget turned into an art direction.

The castle is 71 m across and bakes to **14.7 texels per metre** on a 4096 map.
At the hero camera the great south-east tower is 45 m away and 10.3 m wide,
which puts about 550 screen pixels across 151 texels — **3.6 screen pixels per
texel**. In daylight that is a visibly soft, smeared wall and the demo dies on
the first screenshot.

At night that surface is in shadow, lit only by a cold hemisphere fill, and
nobody reads it at all. What they read instead is **silhouette, mass, and
emissive light** — the three things this toolkit is unambiguously good at.

So the rules that follow are not stylistic preferences. They are the budget:

1. **The elevation facing the camera is unlit.** The moon is behind the castle.
   Every camera-facing stone surface sits between `#151D29` and about `#3A4553`.
2. **Nothing bright is a texture.** Everything bright is emissive geometry or a
   point light. Those cost no texels.
3. **Anything carrying a baked map that comes within 25 m of the camera must be
   under 8 m in its longest dimension, or be a modular kit.** (4096 ÷ 512 px/m.)
4. **Anything read purely as silhouette carries no baked map at all** — flat PBR
   colour, or `texlib.vertex_colour()`. That is most of this scene by area.

### 0.2 Coordinates — get this right first

The build scripts are **Blender, Z-up, metres**: `+X` east, `+Y` north, `+Z` up.
The ward floor of the castle is `Z = 0`.

The glTF exporter converts on the way out, so in **Three.js** the same world is
`X_three = X_blender`, `Y_three = Z_blender`, `Z_three = −Y_blender`. Which
means:

| Three.js | is | Compass |
|---|---|---|
| `+X` | `+X` Blender | **east** |
| `+Y` | `+Z` Blender | **up** |
| `+Z` | `−Y` Blender | **south** |

**Every number in this document from here on is Three.js metres unless it says
"Blender".** Build scripts must convert back. Landmarks:

| Feature | Three.js (x, y, z) |
|---|---|
| Ward centre / world origin | `(0, 0, 0)` |
| Gatehouse passage mouth (south wall) | `(6, 2.1, 27.5)` |
| Gate drum tops | `(0.4, 15.2, 23.8)` and `(11.6, 15.2, 23.8)` |
| Machicolated gate head (top of frame-left mass) | `(6, 16.8, 28.4)` |
| **SE great tower** axis, 19.4 m tall | `(28.8, 0→19.4, 21.3)` |
| **East-wall breach**, wall down to 1.4 m | `(28.8, 1.4, −2.0)` |
| Breach spoil heap, outside the wall | `(31.6, 0, −2.0)` |
| **NE broken tower**, jagged staves ~12 m | `(28.8, 0→12, −21.3)` |
| **Keep**, turrets 23.4 m — tallest thing in the world | `(−9.5, 0→23.4, −6.5)` |
| Keep chimney head | `(−14.9, 23.5, −9.1)` |
| Keep top-storey windows ×3, facing camera | `(−14.5 / −9.5 / −4.5, 14.5, 1.1)` |
| Hall, thatched, ridge 8.9 m | `(−23.6, 0→8.9, 7.5)` |
| Hall door (faces east, into the ward) | `(−19.7, 1.5, 6.3)` |
| Hall windows ×5 (face east) | `(−19.7, 5.6, 12.3 / 9.1 / 5.9 / 2.7 / −0.5)` |
| Bake-house oven + flue | `(23.6, 0→3.1, 16.6)` |
| Chapel, slate, ridge 6.4 m | `(14, 0→6.4, −11)` |
| Stable range, thatched | `(−4, 0→5.6, −16.9)` |
| Well, with its beam | `(1.5, 0→2.8, 1.0)` |
| Stair up to the wall-walk | `x −2.2→14, z 19.1` |
| SW tower — knee-high stump and a heap | `(−28.8, 0→4.4, 21.3)` |
| NW leaning square turret | `(−28.8, 0→14, −21.3)` |
| S mural turret | `(−14, 0→12.3, 23.6)` |
| W mural drum | `(−27.9, 0→12.6, 1.0)` |
| Causeway apron outside the gate | `(6, 0.2, 29.6)` |

### 0.3 Two defects in the existing castle that must be fixed at source

Both are build-script changes. Neither is hand-editing a model, so the claim
holds.

**(a) The smoke is opaque.** `build_castle.py` gives the hearth puffs
`alpha=0.34`, but `skin_castle.py` replaces that material with an opaque
`simple('smoke', …)` and `apply_baked()` rebuilds a Principled with no alpha.
The shipped `.glb` therefore has three clusters of solid pale-grey cubes
floating over the roofs. At night they would be the brightest thing in frame.

*Fix:* add a fourth merge group `vapour` in `build_castle.py`, sibling to
`masonry` / `fittings` / `ward`. `skin_castle.py` skips it entirely — no
unwrap, no bake — and gives it a flat translucent material. Then rebuild the
plumes to the spec in asset group 3.

**(b) The lit openings are not lit.** Every window and arrow loop is the
`opening` material, near-black, baked into the `fittings` atlas. It cannot be
made emissive without re-baking. Do not re-bake — add separate emissive plates
in front of them (asset group 4). That is cheaper, more controllable from scene
code, and it lets us light six openings out of forty.

### 0.4 Emissive materials never go through the bake

`texlib.apply_baked()` builds a fresh Principled wired to base colour,
roughness, normal and metallic. **There is no emission channel.** Any object
that must glow is a flat `lib.material(name, rgba, emissive=…)` and is excluded
from the texture pass. If an asset needs both a baked surface and a glowing
part, split it into two objects.

Note also that `lib.material()` drives Emission Color from the same RGBA as
Base Color. **Paint a fire mesh the colour you want it to glow.**

---

## 1. The picture

A little after ten at night, the last week of October, on the Welsh march.
It has rained and stopped; the sky has cleared to a hard cold black-blue and a
gibbous moon sits low in the south-west, out of frame behind the castle's left
shoulder. You are standing on a low knoll ninety metres out on the drove road,
looking west-north-west and slightly up at a castle that has been half dead for
sixty years and is still, obstinately, somebody's home. The moon is behind it,
so the whole east elevation facing you is a single unlit mass — a black
cut-out, forty feet of curtain wall with the moon showing only as a cold wire
along the merlon caps and one bright crescent down the west flank of the great
tower. Two thirds of the way across the frame that mass is broken: the east
wall has come down to a stub, rubble spilling out into the ditch, and through
the gap comes the light of a fire burning in the ward. Not a beacon, not a
siege — a household fire, orange, low, throwing the shadows of the stable range
across the inside of the far wall. Three chimneys are drawing. Two windows high
in the keep are lit and one of them is half shuttered. There is a brazier in
the gate passage and a lantern on the bridge post, and the ruts in the track
where you are standing hold enough standing water to give both of them back.
Mist is lying in the ditch and in the hollow beyond, knee deep, and the plumes
from the hearths rise eight or ten metres, flatten under the cold air, and
drift away north-east into the dark half of the sky.

**What it is about:** occupancy in a ruin. Not a garrison, not a monument — a
household of perhaps thirty people farming and sleeping inside the shell of
something that was built to hold an army. The subject of the picture is *the
light*, and the castle is the enormous cold thing the light is inside. Every
composition and lighting decision below serves that one sentence.

**What it is not about:** war. No siege lines, no torches on the walls, no
banners lit from below, no watchfires on every tower. The gatehouse is the only
part being kept up and that is the only martial note we get. The rest is
domestic: a bake-house, a woodpile, a cart, a hurdle pen, a wayside cross.

---

## 2. The palette

Two families and a hard rule. Nothing outside these.

### The cool mass — everything by area

| Name | Hex | Where it lives |
|---|---|---|
| `sky-zenith` | `#080D18` | top of the sky dome |
| `sky-horizon` | `#1C2C42` | horizon band, and the fog colour when lifted |
| `fog` | `#16243A` | `FogExp2` colour |
| `moon-cold` | `#AFC8EC` | the directional light, and the rim on merlon caps |
| `stone-lit` | `#6A7787` | limestone where the moon actually reaches it |
| `stone-dark` | `#151D29` | the camera-facing elevations — ambient only |
| `turf-night` | `#1A2419` | field, berm, knoll |
| `earth-wet` | `#20211C` | track, ruts, ditch sides |
| `timber-night` | `#100D0A` | bare trees, bridge, hurdles, cart |
| `mist-pale` | `#5E7488` | ground mist sheets and the smoke plumes |
| `water-black` | `#0A121A` | ditch water, rut pools |

### The warm life — five steps of one fire

| Name | Hex | Where it lives |
|---|---|---|
| **`fire-core`** | **`#FFD08A`** | **the one bright thing** — inside brazier baskets and the heart of the bonfire, nowhere else |
| `fire-flame` | `#FF9A3C` | flame shards standing above the core |
| `fire-spill` | `#FF7A2E` | the colour of the big fires' point lights |
| `tallow` | `#FFBE6A` | window panes, lantern panes — dimmer, yellower, steadier than fire |
| `ember` | `#B23A16` | coals, the underside of a plume, the deepest warm step |

### The rule

**`fire-core` is the only thing in the scene allowed to be bright.** Everything
cool is capped at the value of `stone-lit` (`0x6A` = 0.42). If a cool surface in
the render is brighter than that, the fault is exposure or a stray light, and it
must be fixed rather than lived with.

Build a debug key into the viewer that clamps and false-colours anything over
0.45 luminance. If anything but the fires lights up, the shot is wrong.

---

## 3. The lighting plan

### 3.1 The moon

South-west, elevation 34°, which is astronomically right for a waxing gibbous
moon at 22:00 in late October and — more usefully — puts it **behind and to the
camera's left**. It therefore lights:

- the **south** elevation (gatehouse front, south curtain) — heavily
  foreshortened at frame left, so it reads as one bright edge exactly where we
  want the "kept up" note;
- the **west** flanks of round towers — from an ESE camera these appear as thin
  bright crescents down the **left** side of each tower, which is the only rim
  light in the picture;
- **upward-facing** surfaces — merlon caps, wall-walk, roof slopes, the tops of
  the rubble heaps. This is what draws the castle's outline for the viewer.

It does **not** light the east elevation, which is the whole camera-facing mass.
That is deliberate.

The moon disc itself is **out of frame** (34° elevation against a frame top of
about 22°, and 78° off the view bearing). Its glow lobe in the sky shader still
lifts the left-hand sky, which is what silhouettes the gatehouse.

```
DirectionalLight   colour #AFC8EC   intensity 0.85
position (−115, 112, 115)   target (0, 6, 0)
castShadow: true
```

### 3.2 Ambient

```
HemisphereLight   sky #2A3E58   ground #0D1319   intensity 0.55
```

A hemisphere, not an `AmbientLight`. The difference is that upward-facing
surfaces pick up cold sky and downward-facing surfaces go to near-black, which
does most of the work of making unlit geometry read at all. An ambient light
flattens the whole castle to a uniform grey and kills the scene.

### 3.3 Fog

```
scene.fog = new THREE.FogExp2(0x16243A, 0.0045)
```

At the castle (90 m) that is a 9 % wash — just enough aerial perspective to sit
it behind the foreground. At the treeline (200 m) it is 56 %, and at the distant
ridge (300 m) it is 87 %, so the far ground dissolves without a hard edge.
Linear fog gives a visible onset plane on a ground this large; exponential
squared does not.

Ground mist is **not** fog — global fog cannot do a layer. It is geometry
(asset group 7).

### 3.4 Dynamic light budget

**One shadow-casting light, seven point lights, no shadows on any of them.**

That is the affordable envelope: `MeshStandardMaterial` recompiles per
light-count but seven point lights plus a directional plus a hemisphere is
routine at 1080p, whereas a single shadow-casting point light costs six
cube-map faces and would double the draw calls on its own.

Create all eight lights up front and never add or remove one at runtime — that
triggers a shader recompile and a visible hitch.

The discipline is: **emissive materials do the look, point lights do the
spill.** An emissive material does not illuminate its neighbours; without a
point light beside it a brazier is an orange sticker on a black wall.

| # | What | Three.js position | Colour | Intensity | Distance | Job |
|---|---|---|---|---|---|---|
| 1 | **Ward bonfire** | `(24.0, 1.6, −2.0)` | `#FF7A2E` | 26 | 32 | The picture. Sits just inside the breach so its light escapes through the gap and rakes the spoil heap outside |
| 2 | Gate-passage brazier | `(6.0, 2.2, 26.2)` | `#FF9A3C` | 9 | 18 | Lights the passage vault and the causeway; the frame-left anchor |
| 3 | Wall-walk brazier over the gate | `(6.0, 11.6, 22.0)` | `#FF9A3C` | 6 | 15 | Puts a warm top-note on the gatehouse so it is not purely a moon silhouette |
| 4 | Bake-house oven | `(23.6, 1.8, 16.6)` | `#FF7A2E` | 6 | 14 | Second warm point inside the ward, visible over the south wall as a glow on the smoke |
| 5 | Hall doorway | `(−19.6, 2.2, 6.3)` | `#FFBE6A` | 5 | 18 | Never directly seen. Its job is to light the *far* side of the ward so the breach reads as depth, not a hole |
| 6 | Keep window | `(−9.5, 14.6, 1.5)` | `#FFBE6A` | 3 | 10 | Warms the ashlar around the lit windows so they are set into stone rather than stuck on |
| 7 | Bridge lantern | `(48.0, −0.4, 24.0)` | `#FFD08A` | 3.5 | 12 | Foreground. Its reflection in the ditch water is the whole reason it exists |

Tune every intensity against the final exposure; these are starting values, not
gospel. Decay is `2` (physically correct falloff) on all of them.

### 3.5 Flicker

Each of lights 1–4 and 7 gets `I(t) = I₀ · (1 + 0.07 sin(2.3t + φ) + 0.05
sin(3.7t + ψ) + 0.04 sin(0.9t + χ))`, with a per-light phase, and a ±3 cm
position jitter on the same signal. Drive the matching material's
`emissiveIntensity` from the *same* value so the light and the flame agree —
that agreement is what sells it. Light 6 (the window) does **not** flicker;
a candle behind a shutter is steady, and the contrast between a steady window
and a restless fire is worth having.

### 3.6 Emissive sources (material, not light)

| Source | Material | Colour | `emissiveIntensity` | Count |
|---|---|---|---|---|
| Bonfire heart | `emis_fire_core` | `#FFD08A` | 6.0 | 1 |
| Brazier basket cores | `emis_fire_core` | `#FFD08A` | 4.5 | 4 |
| Flame shards | `emis_fire_flame` | `#FF9A3C` | 3.0 | 5 groups |
| Lantern panes | `emis_tallow` | `#FFBE6A` | 2.2 | 6 |
| Cresset bowls | `emis_fire_flame` | `#FF9A3C` | 3.5 | 4 |
| Lit window plates | `emis_tallow` | `#FFBE6A` | 1.6 | 6 |
| Oven mouth | `emis_ember` | `#B23A16` | 2.5 | 1 |

Build these in Blender at `emissive=1.0` and let the Three.js material tune-up
table set the real intensity by material name. `KHR_materials_emissive_strength`
does round-trip correctly, but keeping the number in scene code means the whole
lighting balance is tunable without a Blender rebuild, which will matter more
than you think on pass four.

---

## 4. The camera

### 4.1 The hero still

```
position   (78.9, −1.0, 43.3)
target     ( 3.9,  9.3, −6.4)
fov        32          (vertical; horizontal works out at 54°)
aspect     16 : 9
near 0.5   far 900
up         (0, 1, 0)
```

Ninety metres out on a bearing 33.5° south of due east, **eye height 1.7 m above
the crest of the knoll** — a person standing on the drove road, not a drone. The
camera sits at `y = −1.0` because the outfield is 4.5 m below the castle datum
and the knoll lifts it to −2.7. **The ward floor is a metre above the lens.**
You are looking up at the castle, which is the entire reason for a low camera.

The axis is tilted 6.5° up, which puts the flat horizon at 70 % down the frame:

| Frame band | Contents |
|---|---|
| 0 – 13 % | empty sky |
| 13 – 70 % | the castle mass and the skyline |
| 70 – 100 % | knoll, track, ruts, mist, wayside cross |

Where things land horizontally (0 % = left edge):

| | Across | Note |
|---|---|---|
| Gatehouse | 16 % | moonlit front, the only bright architecture |
| SE great tower | 32 % | tallest near mass; top sits 13 % from the frame top |
| Keep turrets | 42 % | highest point in the world, 28 % from the frame top |
| Ditch bridge | 47 % | 36 m away, low in frame |
| **The breach and the bonfire** | **66 %** | the brightest thing, on the right third |
| NE broken tower | 85 % | jagged, low, closes the right edge |
| Wayside cross | 18 % | 22 m away, head crossing the horizon line |

### 4.2 The slow move (optional, but do it)

A single 24-second one-way push, cubic ease-in-out, no loop, holding on the hero
frame at the end.

```
start   position (92.0,  1.5, 52.0)   target (6.0, 11.0, −5.0)
end     position (72.0, −1.6, 39.0)   target (3.0,  8.6, −7.0)
```

The camera comes **in and down**. The SE tower grows and slides left, the breach
opens up, the keep rises against the sky, and the wayside cross enters at the
left. Under 3° of actual rotation — a slow move should be almost entirely
translation, because rotation at this focal length reads as a pan and breaks the
spell.

Add a ±0.25 m vertical bob on a 33 s period so the held frame never feels
frozen.

### 4.3 Interaction

`OrbitControls`, tightly fenced, so a visitor can look but cannot find the ugly
angles:

```
target locked to (3.9, 9.3, −6.4)
minDistance 55        maxDistance 130
minPolarAngle 80°     maxPolarAngle 94°
minAzimuthAngle / maxAzimuthAngle: hero bearing ±38°
enablePan false       enableDamping true, dampingFactor 0.05
```

Any user input cancels the intro move. A "reset view" key returns to the hero.

---

## 5. The asset list

Eight groups beyond the castle, thirty-nine pieces. The two ground meshes are
specified separately in §6 but are built the same way and are part of the claim.

Every group gets its own `build_*.py` and its own one-paragraph brief committed
verbatim beside it in `demo/build/briefs/`. That pairing is what makes the pitch
checkable, so it is not optional.

---

### Group 1 — Tree and scrub kit

**What it must communicate:** late autumn on a wet upland margin. Trees that
have been grazed, wind-shaped and cut at for firewood, not a designed landscape.
Against a night sky they are pure silhouette, and that is the point.

**The decision that makes this work: the trees are bare.** It is the last week
of October. A bare tree is a *branch structure*, and a branch structure is a
tapered section swept along a path — which is exactly `lib.profile(name,
section, path, scales=…)`. That is hard-surface parametric work, the toolkit's
strongest suit. A summer tree is a foliage mass, which is its weakest. Choosing
the season is choosing to win.

Only the evergreens carry mass, and evergreen mass is a small number of chunky
faceted lumps, which is also fine.

| Piece | Size (m) | Tris | Instances | Where | Method |
|---|---|---|---|---|---|
| `tree_oak_bare` | 11 h × 9 spread | ~1 100 | 34 | field boundaries, ditch outer lip, both frame edges | `profile` trunk with `scales` taper; 5 primary limbs each splitting once into 3; 8-segment sections |
| `tree_ash_bare` | 14 h × 7 spread | ~1 300 | 16 | in the middle distance where height is wanted | as oak, more upright, fewer heavier limbs, higher first fork |
| `tree_hawthorn` | 4.5 h × 5 spread | ~700 | 26 | scattered in the field, on the knoll, in the ditch | `Form.bend()` a permanent lean away from the SW; low twisted crown |
| `tree_yew` | 7 h × 6 spread | ~620 | 10 | two by the wayside cross, the rest at the treeline | 5 overlapping faceted lumps on a short fat trunk. Near-black |
| `tree_pine` | 16 h × 6 spread | ~1 150 | 20 | **one stand only**, on the ridge behind the castle at 240–300 m | bare straight trunk to 10 m, then 4 flat plate-like crown masses |
| `scrub_gorse` | 1.2 h × 1.6 | ~110 | 70 | ditch sides, platform toe, the knoll's near face | 3 overlapping beveled lumps, no stems |
| `deadfall` | 5 long | ~240 | 8 | field, one across the ditch | a fallen `tree_oak_bare` trunk with 3 limb stubs |

**Total ≈ 115 000 triangles.** The largest single consumer in the scene, and
worth it — this is what makes the ground read as a place.

**Materials:** flat PBR, `timber-night` `#100D0A`, roughness 0.9, **no baked
texture and no UVs at all.** A bare tree at 60–250 m under a moon behind it has
no readable surface. Give the yews a shade cooler and darker (`#0C1310`) so the
evergreen mass separates tonally from the bare structure.

**Placement:** never inside the castle footprint, never on the platform top,
never within 3 m of the track polyline, never on a slope over 30°, and — the
rule that matters — **never on the sight line between the camera and the
breach.** Leave a 22° wedge clear on the hero bearing between 35 m and 80 m.

**Must not be:** a lollipop. No sphere on a stick. No individual leaves, ever.
No crown wider than 1.1× the tree's height. No two instances at the same
rotation or scale. If any single tree reads as a green blob in a render, the
whole group is rejected — a bad tree is the one thing that would tell a viewer
this was not modelled by hand, and it must not appear.

---

### Group 2 — Rock and outcrop kit

**What it must communicate:** the castle is cut from the rock it stands on. The
platform is not a mound of earth someone piled up; it is a shoulder of
limestone, and the same rock breaks the turf all round it.

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `rock_outcrop_a` | 6.0 × 4.0 × 2.4 | ~380 | 9 | the platform's batter, breaking through the turf |
| `rock_outcrop_b` | 3.6 × 3.0 × 1.6 | ~260 | 14 | ditch sides, knoll crest |
| `boulder_a` | 1.8 × 1.4 × 1.2 | ~150 | 18 | scattered, and 3 in the foreground under 25 m |
| `boulder_b` | 1.1 × 0.9 × 0.7 | ~110 | 16 | ditto |
| `scree_run` | 8.0 × 3.0 × 0.6 | ~340 | 5 | below the outcrops, and continuous with the castle's own rubble spill |

**Total ≈ 9 500 triangles.**

Built with `Form` from a box: bevel, then `warp()` with coordinate-derived
pseudo-noise, flat-shaded. Vertex-coloured via `texlib.vertex_colour()` —
grey-brown rock darkening in the crevices and greening at the base. **No baked
maps**; the foreground boulders are only 1.8 m and could carry one, but they
sit in shadow and there is nothing to gain.

**Must not be:** potatoes. Limestone breaks along bedding planes and joints, so
these want **flat cleavage faces and sharp arrises** — beveled boxes warped a
little, not lumpy spheres smoothed a lot. This is a thing the toolkit does
extremely well and a thing that goes badly wrong the moment someone reaches for
`sphere()`.

---

### Group 3 — Fire, lamp and plume kit  *(emissive)*

**What it must communicate:** somebody keeps these lit. They are maintained
objects — a basket that gets refilled, a lantern someone carries out — not set
dressing.

| Piece | Size (m) | Tris | Instances | Emissive | Where |
|---|---|---|---|---|---|
| `brazier` | 0.62 ⌀ × 1.10 h | ~350 | 4 | yes | gate passage `(6, 0, 26.2)`; gate wall-walk `(6, 10.4, 22.0)`; hall door `(−19.0, 0, 6.0)`; ward `(12, 0, 8)` |
| `bonfire` | 2.6 ⌀ × 1.40 h | ~520 | 1 | yes | **the ward, just inside the breach, `(24.0, 0, −2.0)`** |
| `lantern` | 0.22 × 0.22 × 0.34 | ~180 | 6 | yes | bridge post, causeway post ×2, hall door, well beam, gate arch |
| `cresset` | 0.34 ⌀ × 0.50 | ~140 | 4 | yes | gatehouse front ×2, SE tower ×1, gate passage ×1 |
| `lamp_post` | 0.16 × 0.16 × 2.4 | ~90 | 3 | no | carries the lanterns on the causeway and bridge |
| `plume_tall` | 2.5 ⌀ × 13 h | ~420 | 1 | no (translucent) | keep chimney, `(−14.9, 23.5, −9.1)` |
| `plume_low` | 1.8 ⌀ × 8 h | ~300 | 2 | no (translucent) | hall ridge `(−24.8, 8.9, 3.5)`, oven flue `(23.6, 3.1, 16.6)` |

**Total ≈ 4 100 triangles.**

**The braziers and the bonfire.** Iron tripod or a ring of set stones, a shallow
fire-basket, and a fire mass inside it: 4–6 overlapping tapered shards standing
up out of a low glowing bed. The **bed** is `fire-core` at 4.5–6.0. The
**shards** are `fire-flame` at 3.0. Two intensities is what stops it reading as
a lamp. Do not attempt a flame *shape* — a shard cluster read at 45 m through
bloom is entirely convincing and a modelled flame is not.

**The plumes.** These are the scene's only large soft shapes and they matter.
A plume is a `profile()` sweep: a circular section along a path that **rises
vertically for 8–10 m, then bends over 30° and drifts north-east**, with
`scales` widening from 0.5 to 4.0 along the path. Cold clear night, so the air
is stable and the plume flattens under an inversion rather than climbing.
Faceted, 8-segment section, flat-shaded. Material `mist-pale` `#5E7488`,
`alpha 0.13`, `depthWrite: false` set in the loader.

Backlit by a SW moon and underlit by the fires below them, the plumes read as
pale grey columns against the dark half of the sky. Three of them, at three
heights, on the same drift bearing. That is one of the best things in the frame.

**Wind is from the south-west at about 8 km/h.** Everything that leans — plumes,
hawthorns, the banner already on the keep — leans the same way. Consistency here
is free and its absence is instantly legible.

**Must not be:** a torch on every wall. Four braziers, one bonfire, six
lanterns, four cressets in a castle this size is *already generous*; the moment
it becomes a dozen the picture stops being a household and starts being a film
set. And the lanterns must not be modern — a horn lantern is an iron frame with
four cloudy panes, not a glass box.

---

### Group 4 — Lit-opening plates and shutters  *(emissive)*

**What it must communicate:** these are rooms with people in them. Six lit
openings out of about forty. Restraint *is* the asset.

Small plates that sit 25 mm proud of the castle's existing dark openings, so a
black hole becomes a lit window. Sizes are taken from `build_castle.py` and must
match the openings they cover.

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `pane_window` | 1.40 × 0.06 × 2.10 | 12 | 2 | keep top-storey, `(−14.5, 14.5, 1.1)` and `(−4.5, 14.5, 1.1)` |
| `pane_hall` | 0.10 × 1.05 × 1.40 | 12 | 2 | hall, `(−19.6, 5.6, 12.3)` and `(−19.6, 5.6, 9.1)` |
| `pane_loop` | 0.44 × 0.06 × 1.45 | 12 | 1 | gate drum loop, `(13.2, 9.4, 26.4)` |
| `pane_lancet` | 0.10 × 1.20 × 2.40 | 12 | 1 | chapel west window, `(11.3, 3.2, −11)` |
| `shutter` | 0.72 × 0.05 × 2.10 | ~90 | 2 | timber, half open, partly occluding the two keep panes |

**Total ≈ 250 triangles.** The cheapest asset in the scene and one of the two or
three most important.

**The shutter is the whole trick.** A bare lit rectangle reads as a decal. A lit
rectangle with a timber shutter swung across two thirds of it, throwing a hard
shadow edge across the light, reads as a window in a wall in a building someone
lives in. Both keep windows get one, at different angles.

Also add one **`pane_passage`**: a `1.9 × 0.06 × 2.6` plate set 4 m back inside
the gate passage at `(6, 1.4, 24.0)`, `emis_tallow` at 1.2. It makes the gateway
read as a way through rather than a black slot, and from the hero camera it is
seen at an acute angle, which is exactly right.

**Must not be:** a grid. No two lit openings on the same elevation at the same
height, no lit arrow loops except the one, nothing lit in the ruined north and
west ranges, nothing lit in the broken NE tower. The distribution should say:
they use the keep's top floor, the hall's near end, the chapel and the gate. The
other thirty-four openings are cold and empty, and their being cold is what
makes the six warm ones mean something.

---

### Group 5 — The crossing: bridge, causeway and ditch water

**What it must communicate:** you can get in, and only here. A worked, repaired,
much-used way over a serious obstacle.

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `ditch_bridge` | 12.0 × 4.4 × 3.6 | ~900 | 1 | crosses the ditch on the ESE at `(48, −1.0, 24)`; **47 % across the hero frame, 36 m out** |
| `causeway_apron` | 9.0 × 5.0 × 0.4 | ~180 | 1 | butts the castle's existing causeway at `(6, 0.2, 30)` |
| `ditch_water` | ring, 10 m wide | ~640 | 1 | follows the ditch, surface at `y = −6.0` |
| `rut_pool` | 2.4 × 0.9 × 0.02 | ~40 | 9 | in the track ruts, 12–45 m from the camera |

**Total ≈ 2 100 triangles.**

**The approach is flanking, and that is both historically right and
compositionally essential.** The drove road comes up from the east, crosses the
ditch by timber bridge on the east-south-east, climbs onto the berm, and runs
*anticlockwise round the south side of the platform* to the gate — so an
attacker walks the length of the south curtain with his shield arm on the wrong
side. It also means the track enters the bottom of the hero frame, crosses the
bridge at dead centre, and sweeps left and away under the whole south elevation
to the gate at 16 %. That is the leading line of the picture and there is no
better one available.

**The bridge:** oak trestles, three bays, a plank deck, one plank missing near
the middle, a handrail on one side only and a stub of a broken one on the other.
Built from `box` and `profile`. Deck at `y = −1.0`, one metre below the castle
datum, so it silhouettes against the water and the ditch mist.

**The water:** flat mesh, `water-black` `#0A121A`, **roughness 0.06**,
metalness 0. With no environment map it shows almost nothing but specular
glints from the bridge lantern and the moon — which is precisely the effect
wanted. Do not give it a normal map, do not animate it, do not add a reflection
probe. A dead-still black ditch on a windless cold night is better than a
shader.

**The rut pools** are the same material, 2 cm deep, and they are worth more than
the ditch because they are 12–45 m from the camera in the bottom of frame. Three
of them should be positioned to catch the gate brazier and the bridge lantern.
Place them by eye against the hero frame, then freeze the placement.

**Must not be:** a stone bridge, an arch, or a drawbridge. Timber, patched,
slightly out of true.

---

### Group 6 — Track and field-edge kit

**What it must communicate:** this land is worked and divided, and has been for
a long time. Edges are what turn a ground plane into fields.

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `track_ribbon` | 4.4 wide, ~180 long | ~1 400 | 1 | the whole approach, swept with `profile()` |
| `wall_mod_a` | 2.0 × 0.62 × 1.10 | ~220 | 44 | drystone field wall, two boundaries |
| `wall_mod_b` (gapped) | 2.0 × 0.62 × 0.55 | ~150 | 12 | a fallen run, used in threes |
| `hurdle` | 1.80 × 0.10 × 1.05 | ~160 | 24 | stock fencing across the wet ground east of the ditch |
| `field_gate` | 3.2 × 0.14 × 1.30 | ~200 | 2 | five-bar, one hanging open |

**Total ≈ 17 000 triangles.**

**The wall is a proper modular kit** and the only asset here that should carry a
baked texture, because at 2 m a 2048 map gives 1 024 px/m — vastly inside
budget — and there is one stretch of it within 25 m of the camera. Follow the
kit rules in `SKILL.md`: 2 m pitch, mating cross-section at both ends,
**origin on the connection face**, and 4 cm of deliberate overlap so no joint
opens a slot when the modules follow the ground. Build `wall_mod_a` properly and
prove it in a close render before building `wall_mod_b`.

Vary it by *placement*, not by geometry: rotate alternate modules 180°, jitter
each by ±2 cm and ±1.5°, and follow the terrain height so the top line
undulates. Do not put a distinctive crack in a module that appears 44 times.

**The track ribbon** is a `profile()` sweep — a 4.4 m shallow trapezoid section
with two rut depressions, along a 3D path that samples the terrain height. Its
material is `earth-wet` at **roughness 0.35**, noticeably glossier than the
`turf-night` field either side. That difference is small in daylight and enormous
at night: the track picks up a long soft sheen from the moon and reads as a
ribbon of slightly-lighter value leading into the frame. It is the single
highest value-per-triangle decision in the ground plan.

**Must not be:** a hedgerow (that is foliage, and foliage is banned), or a
post-and-rail fence (too regular, reads modern). Drystone and hazel hurdle only.

---

### Group 7 — Ground mist sheets

**What it must communicate:** cold air sinking into wet hollows. It sits in
layers with a top surface, it pools where the ground is low, and it is knee to
chest deep — not a general haze.

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `mist_sheet_a` | 44 × 30 × 1.2 | ~200 | 5 | the hollow NE of the castle, `y 0.6 → 2.2` |
| `mist_sheet_b` | 32 × 22 × 0.9 | ~180 | 5 | in the ditch, following the ring |
| `mist_sheet_c` | 26 × 18 × 0.6 | ~160 | 4 | along the treeline and the field boundaries |
| `mist_wisp` | 9 × 5 × 0.4 | ~90 | 6 | the near foreground, under 30 m, thin |

**Total ≈ 3 700 triangles, 20 instances.**

Flat lobed slabs — irregular convex-ish plan with 9–13 lobes, warped, flat
shaded, very slightly domed on top. Material `mist-pale` `#5E7488`,
roughness 1.0.

Loader settings, which are as important as the geometry:

```
transparent: true    opacity: 0.11    depthWrite: false
side: THREE.DoubleSide     fog: true
renderOrder assigned back-to-front from the hero camera, frozen
```

They overlap and accumulate; three layers at 0.11 gives 0.30. Rotate and scale
every instance differently and never let two sit at the same height.

**Must not be:** a visible disc, a card facing the camera, or anything that
reaches the camera's own height (the moment the camera is inside a mist sheet
the illusion dies). Keep every instance's top below `y = 2.4` relative to its
local ground. Keep them out of the point-light ranges of the fires — a mist
slab lit from inside by a point light looks like a glowing plastic sheet.

---

### Group 8 — Outfield clutter and the wayside cross

**What it must communicate:** people come and go along this road, and they have
for generations. This group is entirely about human traces and it is what stops
the outfield being empty.

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `wayside_cross` | 0.9 × 0.9 × 2.8 | ~360 | 1 | **`(57.8, ground, 37.2)` — 22 m from the camera, 18 % across, head crossing the horizon** |
| `carriers_cart` | 3.4 × 1.7 × 1.5 | ~620 | 2 | one tipped by the bridge, one on the berm outside the gate |
| `woodstack` | 2.6 × 1.2 × 1.5 | ~500 | 3 | outside the gate, by the bake-house, on the berm |
| `tether_post` | 0.18 × 0.18 × 1.4 | ~60 | 6 | by the bridge and the gate |
| `hay_heap` | 3.2 × 3.2 × 2.2 | ~280 | 3 | in the field, on staddle timbers |

**Total ≈ 3 900 triangles.**

**The wayside cross is the narrative object and it earns its own paragraph.**
A weathered stone cross on a three-step base, the head broken and repaired, the
shaft leaning about 4°. It is 22 m from the hero camera and 2.8 m tall, so it
occupies about a fifth of the frame height at the left, with its head crossing
the horizon line and silhouetting against the dark base of the castle and the
mist in the ditch. It is the closest object in frame and therefore the one thing
that establishes scale for everything behind it. **It is at 2.8 m and under 25 m
from the camera, so it is the one asset in this group that must carry a properly
baked map** (2048 gives 730 px/m — trivially inside budget). Weather it: lichen
in the joints, moss on the north face, the arrises rubbed round.

**Placement constraint beats the coordinate.** The cross must (a) sit on the
track, (b) put its head above the horizon line, and (c) not overlap the
gatehouse or the great tower. If the exact coordinate above fails any of those
once the terrain is final, move it and keep the constraints.

**Must not be:** a Celtic ringed cross (wrong region and it reads as a tourist
icon), or clean. It has stood in the rain for two hundred years.

---

## 6. The ground

The thing that decides whether this is a place or a model on a plane. Three
meshes, none of them textured with a baked map, all of them vertex-coloured.

### 6.1 Levels — fix these first, everything references them

| Datum | `y` | Notes |
|---|---|---|
| Ward floor, castle base, platform top | **0.0** | the castle build already sits here |
| Platform berm edge | 0.0 | 6 m of level ground outside every wall foot; 10 m outside the gate |
| Platform toe (bottom of the batter) | −4.5 | batter falls at 1 : 1.6 |
| Outfield, general | −4.5 | |
| Ditch bottom | −6.8 | |
| **Ditch water surface** | **−6.0** | 0.8 m of standing water |
| Drover's knoll crest (ESE, ~88 m out) | −2.7 | **the camera stands here**, eye at −1.0 |
| The hollow (NE, mist pools here) | −6.5 | |
| Distant ridge (N and W, 240–320 m) | +6.0 | carries the pine stand |

The distant ridge is not optional. Without it the castle's far side silhouettes
against a dead-flat horizon and the whole image reads as an object on a table.
With it, the base of the far walls sits against a slightly-lighter-than-black
band at about `y = +1.2` in the hero frame, which is exactly where a horizon
should sit relative to a building.

### 6.2 `ground_platform` — the rock the castle stands on

Roughly 96 × 80 m at the top, ~110 × 94 m at the toe. Built as a `Form` from a
box: `cut_at()` the plan into an irregular polygon (**not** a rectangle and
**not** an ellipse — a rock shoulder has facets and re-entrants), then `warp()`
the batter with coordinate-derived noise so it slumps and bulges. The ditch is
cut into the same mesh as a negative feature; it is a property of the ground,
not a separate object.

**~9 000 triangles.**

**No baked texture.** At 96 m a 4096 map yields 43 px/m and the answer to that
is not a bigger map, it is not needing one. Use `texlib.vertex_colour()`, which
glTF carries as `COLOR_0` and which *interpolates*, so a grass-to-rock
transition fades instead of stepping at a polygon edge:

- `turf-night` `#1A2419` on the level top and the shallower batter
- graded toward rock grey `#2A2B28` where the slope exceeds ~35°
- darkening to `#101812` in the ditch and the re-entrants
- a wet band `#1B1D18` in the bottom 1.2 m of the ditch, above the waterline

That is four colours driven by height and slope, no UVs, no bake, no image
files, and it is completely convincing at night.

### 6.3 `ground_outfield` — the land to the horizon

400 × 400 m, centred on the castle, built with `lib.loft()` — 96 stations of 96
points each, which is literally a heightfield and exactly what `loft` is for.
Roughly **18 000 triangles** at 4.2 m post spacing.

Its shape is not decorative; it is compositional:

- **the drover's knoll**, ESE, crest −2.7 at 88 m out, 60 m across, falling back
  toward the castle at 1 : 14 so the ditch and the bridge stay visible from the
  camera on its crest;
- **the hollow**, NE, down to −6.5, where the mist pools and the ground goes
  black behind the breach;
- **the ridge**, N and W, rising to +6.0 at 240–320 m, carrying the pine stand;
- otherwise a gentle two-frequency undulation, ±1.2 m, so nothing is flat.

Vertex-coloured: `turf-night` `#1A2419`, darker in the hollows, a shade browner
and drier on the knoll crest, with the wet ground east of the ditch pushed
toward `#161C18`.

**The height function must have one source of truth.** `build_ground.py` writes
`docs/data/terrain.json` — the station grid, the extents and the heights — and
the JavaScript samples it bilinearly to seat every instanced tree, rock, wall
module and hurdle. Do not reimplement the height function in JS. Floating trees
and half-buried walls are the single most common way a scene like this falls
apart, and they are entirely avoidable.

### 6.4 What sits on it

The castle already provides its own ward floor (`ward` mesh) at `y = 0.09→0.2`,
so the platform top and the ward do not fight. Check the seam at the wall feet
in a render before accepting the platform: the toolkit's export report prints
ground contact, and a 5 cm gap under a curtain wall is visible at this camera.

---

## 7. Composition notes

**The frame is 16:9 and the castle occupies 16 % to 85 % of its width.** Both
edges are held by trees, and the top 13 % is empty sky.

**The tonal plan runs left to right.** The moon is off-frame to the left, so the
sky-glow lobe lifts the left edge; the gatehouse therefore silhouettes *dark
against light*. The right of the frame has the darkest sky, and the breach and
the bonfire sit there — *light against dark*. That gives one reversal of
contrast across the picture, which is worth more than any amount of local
detail, and it happens for free once the moon is placed.

**The skyline is a rhythm, not a line.** Reading left to right at the hero
framing: the pine stand far behind → the gatehouse's machicolated head (28.8 %
from the frame top) → a dip along the south curtain merlons → **the SE great
tower** (13 % from the top, the tallest near mass, capped with a gapped
crenellation ring) → a long low run of east curtain → **the keep turrets** rising
behind it at 28.1 % → the drop into the breach → **the NE broken tower's jagged
staves** at the right edge, low → bare oak branches beyond. Three vertical
events at three heights, a ragged terminator on the right, and organic branch
texture closing both edges.

**The eye path,** which is what the placement is actually for:

1. enters bottom-centre on the **track**, wet and slightly lighter than the field
2. runs up to the **bridge lantern** at 47 % and its reflection in the water
3. is deflected left by the **track's sweep** under the south wall
4. lands on the **gate brazier** and the moonlit **gatehouse** at 16 %
5. climbs the moonlit merlon caps back to the right
6. snags on the **lit keep windows** at 42 %
7. drops right and down into the **breach and the bonfire** at 66 % — the
   brightest thing, and the last stop
8. exits through the **NE tower's broken rim** at 85 %

The two brightest points in the image — the gate brazier at 16 % and the bonfire
at 66 % — sit near the two vertical thirds. That is not a coincidence and it
should not be tuned away.

**The lower 30 % must stay low-value.** Knoll, track, mist and the wayside cross,
all between `#0A121A` and `#20211C`, with three rut pools as the only accents.
If the foreground starts competing, darken it — the picture is about light
escaping from a wall, and anything that pulls the eye down before step 7 is
working against it.

**Negative space.** Do not fill the sky. Do not add birds, do not add clouds
beyond the sky shader's faint band near the horizon, do not put a torch on the
NE tower to "balance" the right side. The right side is meant to be empty and
dark; that is what makes the breach bright.

**Repoussoir.** One bare oak at the extreme left, close enough that its upper
limbs break the top-left corner and run out of frame. One more at the extreme
right, lower. These frame the shot and they cost 2 200 triangles.

---

## 8. The Three.js scene plan

Concrete enough to implement directly.

### 8.1 Stack

Plain ES modules, no bundler, `three` vendored at a pinned version under
`docs/vendor/three/`. Everything on the page is readable source, which is part
of the pitch. GitHub Pages serves from `main` → `/docs`.

### 8.2 Renderer and post

The order matters and is easy to get backwards. **Bloom runs before tone
mapping**; if it runs after, the bloom is a washed grey halo instead of a hot
core.

```
renderer = WebGLRenderer({ antialias: false, powerPreference: 'high-performance' })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.outputColorSpace = SRGBColorSpace
renderer.toneMapping = NoToneMapping          // OutputPass does it
renderer.shadowMap.enabled = true
renderer.shadowMap.type = PCFSoftShadowMap

target = new WebGLRenderTarget(w, h, { type: HalfFloatType, samples: 4 })
composer = new EffectComposer(renderer, target)   // MSAA via samples, not FXAA
composer.addPass(new RenderPass(scene, camera))
composer.addPass(new UnrealBloomPass(new Vector2(w, h), 0.55, 0.5, 0.85))
const out = new OutputPass()
out.toneMapping = ACESFilmicToneMapping
renderer.toneMappingExposure = 1.10
composer.addPass(out)
```

**Bloom threshold 0.85 is the discipline made mechanical.** With the emissive
intensities in §3.6, only the fires and lantern panes cross it. Moonlit stone
peaks around 0.35 and never blooms. If anything cool starts glowing, the fault
is upstream.

ACES rolls the fire cores off to white-hot without clipping to a flat orange
plate and desaturates the highlight the way a real flame does. If the fires clip
too early in practice, swap `OutputPass` to `NeutralToneMapping` before touching
the exposure.

**Do not** use `antialias: true` on the renderer when using a composer — it does
nothing. The `samples: 4` on the render target is what gives MSAA.

### 8.3 Sky

`scene.background` is a `BackSide` sphere of radius 700 with a small
`ShaderMaterial`:

- vertical gradient `sky-zenith #080D18` → `sky-horizon #1C2C42`, `pow(1−y, 3)`
- a soft glow lobe around the moon direction, `pow(max(dot(d, moonDir), 0), 8)`
  at 0.35 strength in `moon-cold`
- a hash-based star field, threshold high enough for maybe 400 visible stars,
  fading out below 12° elevation and inside the moon lobe
- clamp the whole thing at 0.30 luminance so it can never fight the fires

**Be honest about this on the page.** The sky is scene code, not a generated
object; the claim is about the objects in the world, and the sky shader is
thirty lines of GLSL sitting in the repo like everything else.

### 8.4 Lights

Exactly as §3. Additionally:

```
moon.shadow.mapSize = (2048, 2048)
moon.shadow.camera = Orthographic(left −75, right 75, top 62, bottom −62,
                                  near 60, far 340)
moon.shadow.bias = −0.0006
moon.shadow.normalBias = 0.35
moon.shadow.radius = 3
```

A 150 × 124 m box at 2048 gives 13.7 shadow texels per metre — soft, which is
correct for moonlight and correct for hiding the resolution.

**Nothing in the scene moves.** After the first rendered frame:

```
renderer.shadowMap.autoUpdate = false
```

That is a large, free performance win. The flickering point lights do not cast
shadows, so nothing invalidates the map. Set it back to `true` for one frame if
the tree placement is ever regenerated at runtime.

`castShadow` on the castle, platform, trees, rocks, walls, bridge and cross.
`receiveShadow` on the platform, outfield, track, castle and water. **Not** on
the mist (a shadowed translucent slab is a grey stain) and **not** on the
emissive assets.

### 8.5 Material tune-up on load

A single `tuneMaterials(root)` pass walking every loaded scene, dispatching on
material name. This is where the look is controlled, because it can be edited
and reloaded in a second rather than rebuilt in Blender in a minute.

| Name prefix | What it does |
|---|---|
| `emis_*` | set `emissive` from the table, `emissiveIntensity` from §3.6, `toneMapped: true` |
| `mist_*`, `plume_*` | `transparent`, `opacity` per §3.6/7, `depthWrite: false`, `side: DoubleSide`, `renderOrder` frozen back-to-front |
| `water_*` | `roughness: 0.06`, `metalness: 0.0`, `envMapIntensity: 0` |
| `track_*` | `roughness: 0.35` |
| everything else | `envMapIntensity: 0.25`, `shadowSide: FrontSide` |

Keep the table in `docs/js/materials.js` as plain data. It is the tuning
surface for the entire scene and it should be the first place anyone looks.

Optional and worth trying once the rest is right: generate a tiny PMREM
environment from the sky shader and give the stone `envMapIntensity: 0.4`. It
replaces some of the hemisphere fill with a directional cold sheen and can make
the moonlit faces read better. Drop it if it lifts the shadows.

### 8.6 Instancing and placement

One `InstancedMesh` per kit piece — trees, rocks, wall modules, hurdles, gorse,
tether posts, woodstacks. Roughly 15 instanced meshes, which is 15 draw calls
for about 150 000 triangles.

Everything not instanced (castle, ground, bridge, water, mist, fires, cross) is
a plain `Mesh`.

Mist is **not** instanced: 20 transparent objects need individual
`renderOrder`.

**Placement is deterministic and frozen.**

1. `mulberry32` seeded with a fixed constant. Never `Math.random()` — the hero
   shot must be reproducible from a cold load, or every screenshot is a
   different picture.
2. Candidate positions from a jittered grid, then rejected against: inside the
   castle footprint; on the platform top; within 3 m of the track polyline;
   inside the ditch (except gorse and mist); slope over 30°; **inside the 22°
   sight wedge from the camera to the breach between 35 m and 80 m**.
3. Height from `terrain.json`, sampled bilinearly. Normal from the same, so
   things on a slope tilt with it — up to 12°, then clamp.
4. Random yaw, scale 0.82–1.24, and a ±1.5° lean on the wind bearing.
5. Write the accepted transforms once to `docs/data/placement.json` and load
   that thereafter. Regeneration becomes a build step, not a page load, and the
   hero framing stops drifting every time someone touches the rules.

### 8.7 Performance envelope

| | |
|---|---|
| Triangles on screen | ~234 000 (castle 27k, ground 27k, trees 115k, everything else 65k) |
| Draw calls | ~40 |
| Dynamic lights | 1 directional (1 shadow map, frozen) + 1 hemisphere + 7 point |
| Textures | castle 3 × (4096 + 2 × 2048), wall module 2048, wayside cross 2048 |
| Target | 60 fps at 1080p on integrated graphics |

There is headroom to 500k. If it is wanted, spend it on more trees on the ridge
and a second stand at the right edge — not on subdividing anything.

Degrade path, in order: `pixelRatio` to 1 → bloom resolution to quarter → tree
instances to 60 → shadow map to 1024 → drop bloom entirely (the scene still
reads; the fires just go flat).

Total download target **under 25 MB**, dominated by the castle's baked maps.

### 8.8 File layout

```
demo/
  ART-DIRECTION.md              this document
  build/                        THE PROOF — every build script lives here
    artconfig.py                project numbers for blender-model
    texconfig.py                project numbers for blender-texture
    briefs/
      castle.md  ground.md  trees.md  rocks.md  fires.md
      openings.md  crossing.md  edges.md  mist.md  clutter.md
    build_castle.py             existing, + the `vapour` merge group fix
    skin_castle.py              existing, + skip `vapour`
    build_ground.py             platform, outfield, ditch → also writes terrain.json
    build_trees.py
    build_rocks.py
    build_fires.py              braziers, bonfire, lanterns, cressets, plumes
    build_openings.py           lit plates and shutters
    build_crossing.py           bridge, causeway apron, water, rut pools
    build_edges.py              track ribbon, wall kit, hurdles, gates
    build_mist.py
    build_clutter.py            cross, cart, woodstack, posts, hay
    make.py                     runs every build + skin, prints the triangle table
  docs/                         the published site
    index.html
    js/
      main.js                   boot, loop, resize
      scene.js                  renderer, composer, sky, fog
      lights.js                 the moon, the hemisphere, the seven, the flicker
      materials.js              the by-name tune-up table
      place.js                  seeded PRNG, rejection rules, InstancedMesh builder
      terrain.js                bilinear sampler over terrain.json
      camera.js                 hero framing, the 24 s move, fenced OrbitControls
    models/*.glb
    data/terrain.json  data/placement.json
    vendor/three/
```

`make.py` printing a triangle-count table per asset is what keeps the budget
honest across ten build scripts written by ten different agents.

---

## 9. Acceptance

Before this ships, all of these must be true.

1. Every asset group has a `build_*.py` and a brief in `build/briefs/`, and the
   brief was written **before** the script. No asset was hand-edited after
   export. No `.glb` in `docs/models/` was produced by anything but a script in
   `build/`.
2. `make.py` runs clean from an empty `docs/models/` and reproduces the scene.
3. Nothing cool exceeds 0.45 luminance in the hero render. Check with the debug
   clamp, not by eye.
4. Nothing floats and nothing is buried. Every instanced asset sits on the
   sampled terrain height; the export ground-contact report is clean for every
   asset.
5. No tree reads as a blob at any distance. This is the one failure that would
   give the game away.
6. The hero frame is reproducible from a cold page load, byte for byte, because
   placement is frozen.
7. The breach is the brightest thing in the picture and the gate brazier is the
   second. If anything else is competing, it is wrong.
