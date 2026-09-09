# Brief — the track and field-edge kit

*Written before `build_track.py`, and committed verbatim. Section references are
to `demo/ART-DIRECTION.md`. §8.8 names this file `build_edges.py`; it is
`build_track.py` because the track ribbon is the piece the group is about.*

---

Build the things that turn a ground plane into worked, divided, long-inhabited
land: the drove road itself as one long swept ribbon, a proper modular drystone
field wall, a fallen run of the same wall, hazel hurdles for penning stock on the
wet ground east of the ditch, and a five-bar field gate with one of the two
hanging open. The track ribbon is the single highest value-per-triangle decision
in the whole ground plan and it is what the group is really for: a 4.4 m shallow
trapezoid section with **two rut depressions** swept along a 3D path that comes up
from the far east-south-east, over the drover's knoll the camera is standing on,
down to the timber bridge, across it, up onto the berm and then *anticlockwise
round the south side of the platform* to the gate — so it enters the bottom of
the hero frame, crosses the bridge at dead centre at 47 %, and sweeps left and
away under the whole south elevation to the gatehouse at 16 %. That is the
leading line of the picture. Its material is `earth-wet` `#20211C` at roughness
0.35, noticeably glossier than the `turf-night` `#1A2419` field either side, and
that difference is small in daylight and enormous at night, because the track
picks up a long soft sheen from a moon that is behind everything else and reads
as a ribbon of slightly-lighter value leading the eye in. The wall is a **kit**
and must be built as one: 2 m pitch, the same mating cross-section presented at
both ends, the origin on the pitch so placing a module is setting a position on a
line rather than solving an offset, and 4 cm of deliberate overlap so no joint
opens a slot when the run follows the terrain. It is drystone — two battered
faces of laid stone with a coping course set on edge along the top — and it is
seen 44 times, so it must carry **nothing distinctive**: no signature crack, no
one bright stone, all the variety coming from 180° flips, ±2 cm and ±1.5° jitter
and following the ground so the top line undulates.

**The five pieces, from §5 group 6 — sizes and triangle budgets are the
table's:**

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `track_ribbon` | 4.4 wide, ~180 long | ~1 400 | 1 | the whole approach |
| `wall_mod_a` | 2.0 × 0.62 × 1.10 | ~220 | 44 | drystone field wall, two boundaries |
| `wall_mod_b` (gapped) | 2.0 × 0.62 × 0.55 | ~150 | 12 | a fallen run, used in threes |
| `hurdle` | 1.80 × 0.10 × 1.05 | ~160 | 24 | stock fencing across the wet ground east of the ditch |
| `field_gate` | 3.2 × 0.14 × 1.30 | ~200 | 2 | five-bar, one hanging open |

**Total ≈ 17 000 triangles.**

**Levels — §6.1, exact, because the ground agent owns them:** outfield `−4.5`,
knoll crest `−2.7` at about 88 m ESE, bridge deck `−1.0`, berm and platform top
`0.0`, causeway apron top `+0.2`. The track path is defined against those and
against nothing else, and it must be resampled from `terrain.json` when that
exists.

**Features that must be present and provable in a named render:**

1. Two rut depressions running the whole length of the track surface, deep
   enough to hold a 2 cm pool and to read as two dark lines at 40 m.
2. A crown between the ruts and a verge either side — a cambered road section,
   not a flat strip.
3. The track stops at the bridge abutments and resumes on the far side. It does
   not run over the bridge deck, because two coincident surfaces are the classic
   way to ship a flickering seam.
4. The path visibly sweeps: over the knoll, down to the bridge, up onto the berm
   and round to the south. A straight line fails.
5. `wall_mod_a` — two battered faces of coursed laid stone, a coping course set
   on edge along the top, the same cross-section at both ends, and 2.04 m long
   on a 2.00 m pitch.
6. `wall_mod_b` — recognisably the same wall, fallen: the coping gone, the top
   courses tumbled to an uneven line, loose stones lying at the foot.
7. `hurdle` — hazel: vertical sails with horizontal rods **woven** in front of
   one sail and behind the next, and two pointed sails running below the weave
   to be driven into the ground. Not a fence panel.
8. `field_gate` — five horizontal bars, a heavy hanging stile, a lighter head
   stile, and a diagonal brace running from the bottom of the hanging stile up
   to the head, which is the way a real gate is braced and the way you can tell
   one from a ladder. Its origin is on the hinge so it can be swung open by a
   yaw in scene code.

**Size against a person:** the wall comes to a 1.75 m figure's chest and he
could step over the fallen run. A hurdle is hip-to-waist high on him. The gate is
just under his shoulder. He walks two abreast on the track with room to spare.

**Where it goes:** the track is a one-off in world coordinates. The wall runs on
two field boundaries with one stretch inside 25 m of the camera, the fallen
modules used in threes within those runs; the hurdles cross the wet ground east
of the ditch; the two gates go where the track crosses a boundary. Everything but
the track is instanced from `placement.json`, seated on `terrain.json`, jittered
and flipped per §8.6.

**Must not be:** a hedgerow — foliage is banned in this scene — or a
post-and-rail fence, which is too regular and reads modern. Not a mortared wall:
no visible joints, no capstones cemented on. Not a wall with a distinctive
feature. And the track must not be a flat grey stripe painted on the field.
