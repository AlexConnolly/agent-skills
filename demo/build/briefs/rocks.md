# Brief — the rock and outcrop kit

*Written before `build_rocks.py`, and committed verbatim. Section references are
to `demo/ART-DIRECTION.md`.*

---

Build the rock the castle is cut out of, as five faceted flat-shaded pieces that
are instanced sixty-two times over the platform batter, the ditch sides, the
knoll crest and the near foreground, so that a viewer reads the platform as a
shoulder of limestone the walls were quarried out of and not as a mound of earth
somebody piled up. Limestone is the whole instruction: it is a bedded rock that
breaks along its bedding planes and along near-vertical joints at right angles to
them, so every piece here wants **flat cleavage faces, sharp arrises and a
visible horizontal grain of two to four beds**, each bed stepping in or out a
little from the one under it, with the joints running through them — it is a
stack of slabs that has been shoved and weathered, never a lump. Build them the
way the toolkit is good at: a `Form` grown from a box, loop-cut at the bedding
planes and at the joints, `warp()`ed with pseudo-noise derived from the vertex
coordinates so the result is reproducible, bevelled just enough at 3 to 6
centimetres to take the CG razor off an arris without rounding it, and left flat
shaded. Colour them with `texlib.vertex_colour()` and nothing else — no baked
map, no UVs, no image files — grading a grey-brown limestone `#3A3A34` on the
lit upward faces down to `#191C18` in the crevices and on the downward faces,
with a green-grey `#232A1E` creeping up the bottom 20 to 30 centimetres where the
turf meets the stone, because at night with the moon behind the castle there is
no surface to read and all four of those colours exist to make the *form* legible
rather than to look like stone up close. They are seen from a standing eye ninety
metres out on a bearing 33.5° south of due east, at between 20 and 90 metres, so
between 22 and 90 pixels per metre — the outcrops read as silhouette against the
turf and the boulders as small hard shapes with a moonlit top face, and neither
carries any detail finer than about ten centimetres.

**The five pieces, from §5 group 2 — sizes and triangle budgets are the table's:**

| Piece | Size (m) | Tris | Instances | Where |
|---|---|---|---|---|
| `rock_outcrop_a` | 6.0 × 4.0 × 2.4 | ~380 | 9 | the platform's batter, breaking through the turf |
| `rock_outcrop_b` | 3.6 × 3.0 × 1.6 | ~260 | 14 | ditch sides, knoll crest |
| `boulder_a` | 1.8 × 1.4 × 1.2 | ~150 | 18 | scattered, and 3 in the foreground under 25 m |
| `boulder_b` | 1.1 × 0.9 × 0.7 | ~110 | 16 | ditto |
| `scree_run` | 8.0 × 3.0 × 0.6 | ~340 | 5 | below the outcrops, continuous with the castle's own rubble spill |

**Total ≈ 9 500 triangles across 62 instances.**

**Features that must be present and provable in a named render:**

1. Two to four bedding planes visible as horizontal steps in the silhouette of
   every outcrop, not merely as shading.
2. At least one near-vertical joint face on each outcrop — a flat plane running
   from the top of the piece to the bottom, at an angle to the bedding.
3. Sharp arrises. A bevel you can see is a bevel that is too big.
4. The outcrops narrower at the top than at the base, the way a weathered bed
   sequence stands when the softer courses have gone.
5. `scree_run` is loose broken rock, not a slab: individual angular chips of
   varying size lying at their angle of repose, thinning at the edges to
   nothing, so it can butt the castle's own rubble spill without a seam.
6. Every piece sits flat on `z = 0` with no gap and no burial — these are
   instanced from `terrain.json` heights and a floating rock is the fault that
   §9.4 rejects the scene for.
7. Vertex colour on all five: lit rock on the up faces, near-black in the
   crevices, green-grey at the foot.

**Size against a person:** a 1.75 m figure standing beside `rock_outcrop_a` has
it up to his chest and three and a half of him long; `boulder_a` comes to his
knee; `boulder_b` is a thing he would step over. `scree_run` is ankle to
shin-deep loose stone he would pick his way across.

**Where it goes:** instanced from `docs/data/placement.json`, seated on
`terrain.json` heights, tilted with the terrain normal up to 12°. Nine large
outcrops break out of the platform batter between the berm edge and the toe;
fourteen smaller ones sit on the ditch sides and the knoll crest; the boulders
scatter through the outfield with three of each within 25 m of the camera; the
scree runs sit below the outcrops.

**Must not be:** potatoes. Not spheres, not smoothed lumps, not anything that
came out of `sphere()`. No individually distinctive feature anywhere — a
particular crack or a bright face on a piece used eighteen times reads as a
repeat and is worse than no detail at all, so **all** the variety lives in the
seeded placement jitter and none of it in the geometry. And not granite: no
rounded tors, no exfoliation, no boulders sitting on top of each other.
