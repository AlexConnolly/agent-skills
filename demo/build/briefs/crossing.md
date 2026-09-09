# Brief — the crossing: bridge, causeway and ditch water

*Written before `build_crossing.py`, and committed verbatim. Section references
are to `demo/ART-DIRECTION.md`.*

---

Build the only way into the castle: a timber trestle bridge over the ditch on the
east-south-east, the earth-and-stone apron where the track finally meets the
castle's own causeway outside the gate, the black standing water in the bottom of
the ditch, and the pools of rainwater lying in the track ruts in the near
foreground — four pieces that between them have to say *you can get in, and only
here*, and that this way over a serious obstacle is worked, repaired and much
used rather than defended. The bridge is the piece that matters: it sits 47 %
across the hero frame, 36 metres out, dead centre of the picture and directly on
the eye path, with the bridge lantern on its post and the lantern's reflection in
the water underneath it, so it must read in pure silhouette as **oak trestles,
three bays, a plank deck, one plank missing near the middle, a handrail down one
side only and the stub of a broken one on the other** — a structure with light
and water visible through it, not a solid beam. It is timber and it is slightly
out of true: every plank a few millimetres off its neighbour and a degree or two
off square, the trestles raking rather than plumb, because the single thing that
separates a hand-built timber bridge from a CG one is that nothing on it is
parallel to anything else. The water is the opposite discipline — a dead-flat
mesh at `water-black` `#0A121A` with roughness 0.06 and no normal map, no
animation and no reflection probe, because on a windless cold night a still black
ditch that gives back one specular glint from the lantern and one from the moon
is better than any shader, and the rut pools are the same material and are worth
more than the ditch is because they are 12 to 45 metres from the camera in the
bottom 30 % of the frame where the eye enters the picture.

**The four pieces, from §5 group 5 — sizes and triangle budgets are the
table's:**

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `ditch_bridge` | 12.0 × 4.4 × 3.6 | ~900 | 1 | crosses the ditch ESE at `(48, −1.0, 24)`; 47 % across the hero frame, 36 m out |
| `causeway_apron` | 9.0 × 5.0 × 0.4 | ~180 | 1 | butts the castle's existing causeway at `(6, 0.2, 30)` |
| `ditch_water` | ring, 10 m wide | ~640 | 1 | follows the ditch, surface at `y = −6.0` |
| `rut_pool` | 2.4 × 0.9 × 0.02 | ~40 | 9 | in the track ruts, 12–45 m from the camera |

**Total ≈ 2 100 triangles.**

**Levels — §6.1, exact, and not negotiable, because the ground agent owns them:**
ditch bottom `−6.8`; ditch water surface `−6.0`; platform toe and general
outfield `−4.5`; berm and platform top `0.0`; **bridge deck `−1.0`**, one metre
below the castle datum so it silhouettes against the water and the ditch mist.
The trestle feet therefore stand on the ditch floor at `−6.8`, in 0.8 m of water,
and the abutments land on the ditch lips at `−4.5`.

**Features that must be present and provable in a named render:**

1. Three bays. Two abutments on the lips and two intermediate trestles standing
   in the ditch, and the trestles must actually reach the ditch floor — a leg
   that stops in mid-air is the fault this audit exists for.
2. A plank deck of individual planks, with **one plank missing** near the middle
   of the span so the gap shows daylight — or in this case water.
3. A handrail on one side for the full length, and on the other side nothing but
   a broken post stub or two. Not two handrails and not none.
4. Raking braces on the trestles. A trestle is triangulated or it is a table.
5. Light and water visible **through** the structure in `silhouette.png`. If the
   bridge reads as a solid bar, it has failed.
6. `causeway_apron` — a slab with a defined edge, kerbed with set stones, ramping
   from the track level up to the castle causeway top at `+0.2`, wider at the
   gate end.
7. `ditch_water` — a flat ring following the ditch with the surface at exactly
   `−6.0`, 10 m wide, passing under the bridge, and its plan parametric at the
   top of the script so it can be refitted to the ground agent's ditch in one
   line.
8. `rut_pool` — an irregular lens, 2 cm deep, whose outline is not an ellipse and
   not a rectangle, with the nine frozen positions computed from the track path
   rather than guessed, and three of them placed to catch the gate brazier and
   the bridge lantern.

**Size against a person:** a 1.75 m figure standing on the bridge deck has the
handrail at his hip and 5 metres of air and water below him. Standing on the
ditch floor beside a trestle leg, the deck is 5.8 m above him — over three of
him. The apron is five paces across.

**Where it goes:** the bridge, the apron and the water are one-offs placed in
world coordinates; nothing instances them. The rut pools are nine instances at
frozen positions along the track ribbon.

**It must not be:** a stone bridge, an arch, or a drawbridge. Not a modern
trestle either — no bolts, no steel, no uniform sawn timber. Not a solid parapet.
The water must not be a shader, must not ripple, must not be blue, and must not
be brighter than `stone-lit` anywhere.
