# Brief — the ground

*Written before `build_ground.py`, and committed verbatim. Section references are
to `demo/ART-DIRECTION.md`.*

---

Build the land the castle stands in, at ten at night on the Welsh march in late
October, as three vertex-coloured meshes with no baked map anywhere: a shoulder
of limestone the castle was cut out of, the wet worked outfield around it, and
the distant ridge that keeps the whole picture off a table. The rock shoulder
(`ground_platform`) is a faceted irregular polygon in plan — a landform with
corners and re-entrants, never a rectangle and never an ellipse — about 96 × 80 m
across the level top and 110 × 94 m at the toe, its batter slumping and bulging
at roughly one in one-point-six, and the ditch is cut into that same mesh as a
negative feature of the ground rather than sitting on it as a separate object,
because a ditch is something dug out of a place and not something parked in one.
The outfield (`ground_outfield`) is a 400 × 400 m heightfield centred on the
castle whose shape is compositional rather than decorative: the drover's knoll
the camera stands on, falling gently back toward the castle so that the ditch and
the timber bridge stay visible over its brow; the hollow where cold air sinks and
the mist will pool and the ground goes black behind the breach; and otherwise a
quiet two-frequency undulation of about a metre so that nothing anywhere is flat.
The ridge (`ground_ridge`) is the least glamorous and most important piece in the
scene — a long swell of higher ground behind and around the castle, carrying the
pine stand, whose only job is to put a band very slightly lighter than black
behind the far walls where a dead-flat horizon would otherwise say *object on a
table*. Everything is read from one camera and one camera only, the hero still in
§4.1: a standing person's eye 1.7 m above the knoll crest, ninety metres out,
looking up at a castle whose ward floor is a metre above the lens — so judge
every decision from there, not from a plan and not from an isometric prop view,
and remember that the fog eats the far ground at 56 % by 200 m and 87 % by 300 m,
which means detail out there is wasted and *height* out there is not. Colour it
with `texlib.vertex_colour()` only: turf-night `#1A2419` over the level ground and
the shallow slopes, grading to a rock grey `#2A2B28` wherever the slope goes past
about 35° so the limestone breaks through the turf, dropping to `#101812` in the
ditch and the re-entrants where nothing but shadow lives, a wet band `#1B1D18`
through the bottom of the ditch above the waterline, a shade browner and drier
along the knoll crest where the drove road has worn it, and pushed toward
`#161C18` on the sour wet ground east of the ditch. It has to communicate a place
that has been walked, grazed, drained and dug for six hundred years, and it has to
do that in silhouette and value alone, because at night with the moon behind the
castle there is no surface to read.

**Levels — §6.1, exact, everything else in the scene is placed against them:**
ward floor and platform top `y = 0.0`; platform berm edge `0.0`, 6 m of level
ground outside every wall foot and 10 m outside the gate; platform toe `−4.5`;
outfield general `−4.5`; ditch bottom `−6.8`; ditch water surface `−6.0`;
drover's knoll crest `−2.7`, ESE, about 88 m out, 60 m across, with the camera
standing on it and its eye at `−1.0`; the hollow `−6.5`, NE; the distant ridge
`+6.0`, N and W, 240–320 m out, carrying the pine stand.

**Features that must be present and provable in a named render:**

1. `ground_platform` — a level top at 0.0 wide enough to give 6 m of berm outside
   every wall foot and 10 m outside the gate.
2. An irregular faceted plan with at least two re-entrants. Not a rectangle, not
   an ellipse, not a rounded-corner box.
3. A battered flank at about 1 : 1.6 falling exactly 4.5 m from the berm edge to
   the toe, slumped and bulged by coordinate-derived noise, not a clean cone.
4. The ditch, cut into the platform mesh, ringing the platform: bottom at −6.8,
   wide enough for a 12 m timber bridge to span it, with a scarp and a
   counterscarp of different steepness.
5. A gap or causeway in the ditch on the ESE where the bridge lands, and the
   ground on that line low enough that the water surface at −6.0 is visible from
   the camera's eye.
6. `ground_outfield` — 400 × 400 m, no edge of it visible from the hero camera.
7. The drover's knoll: crest −2.7 under the camera, about 60 m across, falling
   back toward the castle gently enough to keep the ditch and bridge in view.
8. The hollow, down to −6.5, wide enough to hold a 44 × 30 m mist sheet.
9. Two-frequency undulation of roughly ±1.2 m everywhere else, so no part of the
   field reads as a plane.
10. `ground_ridge` — a crest at exactly +6.0 sweeping from north round to west,
    beyond the outfield, standing clear above the platform's near shoulder in the
    hero frame so it is actually seen and not merely modelled.
11. Vertex colour on all three: turf, rock on the steep, black in the ditch, a wet
    band above the waterline, dry on the knoll crest, sour green-grey east of the
    ditch.
12. `docs/data/terrain.json` — one source of truth for the height of the ground,
    written by this script, sampled bilinearly by the placement code so nothing
    in the scene floats or is buried.

**Size against a person:** a 1.75 m figure standing on the platform toe has the
berm edge 4.5 m — two and a half of him — above his head, and standing in the
ditch bottom has it 6.8 m, nearly four of him, above. The knoll is a rise of 1.8 m
over 30 m; you would not call it a hill, you would notice you were walking up.

**Where it goes:** everything. The castle sits on the platform top at 0.0. Trees,
rocks, walls, hurdles and clutter are all seated from `terrain.json`. The ditch
water, the bridge and the mist sheets are all placed against the levels above.

**Triangle budget:** about 9 000 for the platform, about 18 000 for the outfield,
and whatever the ridge needs on top of that — under 35 000 for the three, in a
scene with 500 000 to spend and 234 000 already planned.

**It must not be:** a plane with a bump on it. Not a rectangular mesa. Not an
ellipse. Not a smooth-shaded lump — limestone breaks along bedding planes, so
facets and hard arrises, flat-shaded. Not a dead-flat horizon. Not a ditch that
reads as a groove scored into a lawn. And not a terrain that photographs well from
above and collapses from the one camera anybody will ever see it from.
