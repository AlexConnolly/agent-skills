# Brief — Group 1, the tree and scrub kit

This is the brief `build_trees.py` was written from. It was written first and
has not been edited since the script was authored, because the pairing of the
two is the whole claim: *every object in this scene was generated from a
one-paragraph brief by an AI using this skill, and every build script is in the
repo.*

---

## The paragraph

> Build the tree and scrub kit for a wet upland margin on the Welsh march in the
> last week of October, at night. Seven pieces: a bare oak, a bare ash, a
> hawthorn, a yew, a Scots pine, a gorse hummock and a fallen oak. **The trees
> are bare** — no leaves, no foliage mass, not one, ever; a bare tree is a
> branch structure, and a branch structure is a tapered section swept along a
> path, which is what this toolkit is best at. Only the yew and the pine carry
> mass, and that mass is a small number of chunky faceted lumps. These have been
> grazed by stock, shaped by a wind that has come out of the south-west for two
> hundred years, and cut at for firewood, so they are not a designed landscape:
> the crowns are lopsided, the boles are crooked, nothing below about nine
> hundred millimetres survives except the trunk, and every hawthorn leans the
> same way. They are read against a night sky from a person standing on a road
> sixty to three hundred metres away, so they are **pure silhouette** — flat
> near-black timber `#100D0A` at roughness 0.9, the yew a shade cooler and
> darker at `#0C1310`, no baked texture and no UVs at all. Each piece is
> instanced between eight and seventy times from one mesh, so nothing in any of
> them may be distinctive enough to read as a repeat: put the irregularity in
> seeded jitter spread evenly around the trunk, never in one memorable branch,
> and distribute the limbs through the full three hundred and sixty degrees so
> that turning an instance gives a different outline rather than the same tree
> from the side. **It must not be a lollipop.** No sphere on a stick, no
> individual leaves, no crown wider than 1.1 times the tree's height. If any
> single tree reads as a blob in a render the whole group is rejected, because a
> bad tree is the one thing that would tell a viewer this was not modelled by
> hand.

---

## The pieces, from the asset table in `ART-DIRECTION.md` §5, Group 1

| Piece | Size (m) | Tris | Instances | Method asked for |
|---|---|---|---|---|
| `tree_oak_bare` | 11 h × 9 spread | ~1 100 | 34 | `profile` trunk with `scales` taper; 5 primary limbs each splitting once into 3; 8-segment sections |
| `tree_ash_bare` | 14 h × 7 spread | ~1 300 | 16 | as oak, more upright, fewer heavier limbs, higher first fork |
| `tree_hawthorn` | 4.5 h × 5 spread | ~700 | 26 | a permanent lean away from the SW; low twisted crown |
| `tree_yew` | 7 h × 6 spread | ~620 | 10 | 5 overlapping faceted lumps on a short fat trunk, near-black |
| `tree_pine` | 16 h × 6 spread | ~1 150 | 20 | bare straight trunk to 10 m, then 4 flat plate-like crown masses |
| `scrub_gorse` | 1.2 h × 1.6 | ~110 | 70 | 3 overlapping bevelled lumps, no stems |
| `deadfall` | 5 long | ~240 | 8 | a fallen `tree_oak_bare` trunk with 3 limb stubs |

**Total ≈ 115 000 triangles**, the largest single consumer in the scene.

## The feature list the build is audited against

Every one of these must be provable in a *named* render before the kit is
accepted.

**Oak** — a short thick bole; a first fork low, between 2.5 m and 3.5 m; five
heavy primary limbs spread through the full circle, not fanned to one side; each
primary dividing once into three; sinuous limbs, not straight rods; fine
ramification at the crown edge; a spread of about 9 m against a height of 11 m,
so the crown is wider than it is tall above the fork.

**Ash** — a straight bole carried much higher than the oak's, first fork at
about 6 m; four steeply ascending primary limbs, heavier and fewer; branching in
opposite pairs; twigs that turn *upward* at their ends, which is the ash
signature; a narrow crown, 7 m against 14 m.

**Hawthorn** — a crooked zigzag bole; a browse line, with nothing but trunk
below 0.9 m; a low dense twiggy crown starting under 1.5 m; a lean toward the
north-east, away from the prevailing south-west wind, shared with every other
leaning thing in the scene; a flattened, wind-shorn top.

**Yew** — a short fat fluted trunk under 2 m to the first division; three or
more stems visibly reaching up *into* the masses, so it is not a shape on a
stick; five overlapping irregular faceted evergreen lumps, drooping and
asymmetric, none of them a recognisable sphere; a cooler, darker material than
the bare timber.

**Pine** — a long bare straight trunk carrying no crown below 10 m; a few dead
lower branch stubs on that bare length; four or five flat, plate-like crown
masses tiered up the top third, wider than they are deep in profile; a slight
lean and a slight sinuosity in the trunk, because a ridge-top pine is not a
mast.

**Gorse** — three or four overlapping angular hummocks that meet the ground with
no visible stem, total height about 1.2 m.

**Deadfall** — a trunk about 5 m long lying over; a root plate torn up at the
butt, which is what says *windthrown* rather than *sawn log*; three limb stubs;
the whole thing resting on the ground rather than floating or sunk.

## Must not be

- A lollipop, or a sphere on a stick.
- Foliage. No individual leaves. No leaf card, no leaf cluster, nothing.
- A crown wider than 1.1 × the tree's height.
- A memorable branch, a signature crack, or anything else that reads as a
  repeat across 34 instances.
- A potato: the yew and gorse masses are faceted and warped, not smoothed
  spheres.
- Fanned to one side: limbs on one bearing make every instance the same tree.

## Where they go and what they sit next to

Field boundaries, the ditch's outer lip, the knoll, and both frame edges of the
hero shot. One oak at the extreme left close enough that its upper limbs break
the top-left corner, one more at the extreme right and lower — those two are the
repoussoir. Never inside the castle footprint, never on the platform top, never
within 3 m of the track, never on a slope over 30°, and never in the 22° wedge
between the camera and the breach between 35 m and 80 m. The pine is **one stand
only**, on the ridge behind the castle at 240–300 m.

## The camera they are read from

A person standing on the drove road: eye height 1.7 m, 32° vertical field of
view, 60 m to the nearest tree and 300 m to the pine stand. That is 31 px/m at
the near edge and 7.5 px/m at the ridge. The moon is behind them all. There is
no readable surface at that distance under that light, which is exactly why they
carry no texture: what is being judged is the outline and nothing else.
