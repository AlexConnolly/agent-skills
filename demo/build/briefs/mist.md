# Brief — asset group 7: the ground mist sheets

Written before `build_mist.py`. Committed verbatim: this is the text the model
was built from.

Four translucent pieces, no bake, no textures, one material. They are the only
assets in the scene whose entire substance is alpha, so ART-DIRECTION §0.3(a) —
the castle's smoke shipping as solid pale cubes — is the failure mode being
guarded against, and the proof required is the material JSON read back out of
the exported `.glb`, not a Blender viewport.

---

## Group 7 — ground mist sheets

Cold wet air sinking into the low ground around a half-ruined Welsh march
castle a little after ten at night in late October, seen from a person's eye
height ninety metres out on a knoll — so every one of these is read almost
exactly edge-on, between two and seven degrees above the horizontal, and its
silhouette and its vertical gradient are the whole of it while its plan shape is
very nearly invisible. Build four flat lobed slabs that lie *on* the ground and
pool in it, in `mist-pale #5E7488` at roughness 1.0, flat shaded, every one of
them a closed solid with a domed undulating top, a low soft outer skirt and a
flat underside, and every one of them carrying a per-vertex alpha that is
strongest in the first quarter-metre above the ground and falls away to almost
nothing at the crown and at the outer rim, so that a sheet dissolves into the
air at its top and its edges instead of ending at a line: a `mist_sheet_a` 44 ×
30 × 1.2 m for the hollow north-east of the castle, an irregular twelve-lobed
pool whose top surface rises and falls by a third of its depth in two low
frequencies so its edge-on skyline is a soft lumpy band and not a straight one;
a `mist_sheet_b` 32 × 22 × 0.9 m for the ditch, the same substance but drawn out
along a curved arc so that it follows the ring of the ditch rather than sitting
in it as a blob, swelling and thinning along its length and torn thin at both
ends; a `mist_sheet_c` 26 × 18 × 0.6 m for the treeline and the field
boundaries, a long shallow streak with a kink in it, thinner and lower than the
other two because it is lying against a hedge bank rather than filling a
hollow; and a `mist_wisp` 9 × 5 × 0.4 m for the near foreground under thirty
metres, a small torn rag of the same stuff, low and ragged in plan, thin enough
that the ruts and the wayside cross read straight through it. Twenty instances
in all — five, five, four and six — rotated, scaled and seated differently, at
`transparent: true`, `opacity: 0.11`, `depthWrite: false`, `side:
THREE.DoubleSide`, `fog: true`, back-to-front render order frozen from the hero
camera; they are meant to overlap and accumulate, three layers reading as 0.30,
and the per-vertex alpha multiplies that so a single sheet is a wash and the
place two sheets cross is a bank.

**Sizes against a person:** a 1.75 m figure stands with `mist_sheet_a` at
mid-thigh to waist, `mist_sheet_b` at the knee, `mist_sheet_c` at mid-calf and
`mist_wisp` at the ankle. Every instance's top must stay below 2.4 m above its
local ground — the moment the camera can be inside a sheet the illusion dies.

**It must not be:** a visible disc; a card facing the camera; a flat grey plane
floating above the ground; a solid pale slab (that is the castle's smoke bug and
it is the specific thing this asset exists to not repeat); a replacement for the
scene's `FogExp2(0x16243A, 0.0045)`, which is a global wash and cannot make a
hollow thicker than the field around it; or bright — nothing cool in this scene
is allowed above the value of `stone-lit #6A7787`.
