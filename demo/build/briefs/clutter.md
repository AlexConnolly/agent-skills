# Brief — the outfield clutter and the wayside cross

*Written before `build_clutter.py`, and committed verbatim. Section references
are to `demo/ART-DIRECTION.md`.*

---

Build the human traces in the outfield — the things that say people come and go
along this road and have for generations, and that stop the near half of the
picture being an empty field. Five pieces: a wayside cross, a carrier's cart, a
woodstack, a tether post and a hay heap on staddle timbers. **The wayside cross
is the narrative object and the whole group is really about it.** It stands 22
metres from the hero camera at 18 % across the frame, which is closer than
anything else in the world, so it is the one object that establishes the scale of
everything behind it: 2.8 m tall, occupying about a fifth of the frame height,
with its head crossing the horizon line and silhouetting against the dark base of
the castle and the mist lying in the ditch. It is a **weathered stone cross on a
three-step base, the head broken and repaired, the shaft leaning about 4°**, and
it has stood in the rain for two hundred years: the arrises are rubbed round, the
steps are worn hollow where feet and cartwheels have caught them, one step corner
is gone, the socket stone is chipped, and where the head was broken off it has
been set back on with an iron strap round the neck — the repair is the story and
it must be legible in silhouette at 86 pixels per metre. It is **not** a Celtic
ringed cross, which is the wrong region and reads as a tourist icon, and it is
not clean, not symmetrical, and not new. The other four are quieter and are read
between 25 and 60 metres: a two-wheeled carrier's cart with spoked wheels and
shafts, one lying tipped on its side by the bridge with the shafts up in the air
and one standing on the berm outside the gate; a stack of cordwood with the logs
individually visible and an untidy top course; a split oak tether post with an
iron staple; and a hay heap standing clear of the wet ground on staddle timbers,
slumped and roped down.

**The five pieces, from §5 group 8 — sizes and triangle budgets are the
table's:**

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `wayside_cross` | 0.9 × 0.9 × 2.8 | ~360 | 1 | `(57.8, ground, 37.2)` — 22 m from the camera, 18 % across, head crossing the horizon |
| `carriers_cart` | 3.4 × 1.7 × 1.5 | ~620 | 2 | one tipped by the bridge, one on the berm outside the gate |
| `woodstack` | 2.6 × 1.2 × 1.5 | ~500 | 3 | outside the gate, by the bake-house, on the berm |
| `tether_post` | 0.18 × 0.18 × 1.4 | ~60 | 6 | by the bridge and the gate |
| `hay_heap` | 3.2 × 3.2 × 2.2 | ~280 | 3 | in the field, on staddle timbers |

**Total ≈ 3 900 triangles.**

**Placement constraint beats the coordinate.** The cross must (a) sit on the
track, (b) put its head above the horizon line, and (c) not overlap the gatehouse
or the great tower. If the exact coordinate fails any of those once the terrain
is final, move it and keep the constraints.

**Features that must be present and provable in a named render:**

1. `wayside_cross` — three distinct steps of a calvary base, each smaller than
   the one below it, with the top of each worn and the arrises rubbed round.
2. A socket stone the shaft is set into, wider than the shaft, chamfered from
   square to octagonal.
3. A tapering shaft, square at the foot and stopped to an octagon above it,
   leaning about 4° from vertical.
4. A Latin cross head — an upright with two short arms and a taller head — one
   arm **broken short** with a rough fracture, and an **iron strap** round the
   neck where the head was set back on.
5. Not a ring. No circle joining the arms anywhere.
6. `carriers_cart` — two wheels with real holes and real spokes, an axle, a
   plank body with side rails, and two shafts. The wheels must read as wheels in
   silhouette, which means the spokes must be visible through the rim.
7. `woodstack` — individual logs with visible end grain discs, stacked in
   courses, the top course untidy and not level.
8. `tether_post` — a split post, not a sawn one: an irregular section, a
   weathered top, and an iron staple.
9. `hay_heap` — standing on four staddle timbers with air under it, slumped
   rather than conical, with a rope over the top.

**Size against a person:** a 1.75 m figure standing beside the wayside cross has
the head of it a foot above his own head and the top step at his shin. The cart
body comes to his thigh and its wheels to his hip. The woodstack is chest high.
The tether post is waist high. The hay heap on its staddles is half as tall
again as he is.

**Where it goes:** the cross is a one-off on the track at 22 m. The carts, the
woodstacks, the posts and the hay heaps are instanced from `placement.json`,
seated on `terrain.json`.

**Fidelity:** the cross is 2.8 m and inside 25 m of the camera, so it is the one
asset in this group that should carry a properly baked map — a 2048 gives 730
px/m, trivially inside budget — and the geometry here must be built to be
unwrapped and baked by `blender-texture`, with lichen in the joints and moss on
the north face done there and not faked with geometry here. Everything else in
the group is flat PBR `timber-night` `#100D0A` with no UVs at all.

**Must not be:** a ringed cross, a clean cross, a symmetrical cross, or a
crucifix with a figure on it. Not a modern farm trailer with pneumatic tyres.
Not a neat cube of firewood. Not a smooth-shaded cone of hay sitting on the
ground.
