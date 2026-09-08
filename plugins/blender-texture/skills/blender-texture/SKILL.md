---
name: blender-texture
description: Texture, skin, weather or age a 3D model in Blender — procedural materials built from placement masks, baked down to real glTF textures. Delegates to the material-smith agent, which works a bake → render → look → fix loop rather than tuning a node graph blind. Use for any request to texture, skin, weather, rust, moss, dirty up or re-material a model.
allowed-tools: Agent, Read, Glob, Grep, Bash(blender:*), Bash(git:*)
---

# Skinning a model so it reads as a thing that has existed

Companion to `blender-model`, which makes the shape. This one gives it a
surface. Either works alone; together they are a pipeline.

## Rule one: you do not do this yourself

**Always spawn the `material-smith` agent.** One per model.

```
Agent(
  subagent_type: "material-smith",
  description:   "Skin the <thing>",
  prompt:        "<the brief — see below>",
  run_in_background: false
)
```

The reason is the same as for modelling: this is iterative improvement, at
least five times, and the loop is mostly images. Run inline it fills the
context of whatever else you were doing and you start skipping renders.

## What the pipeline actually is

glTF carries image textures wired into a Principled BSDF. **It does not carry
procedural nodes.** A noise-and-ramp material renders beautifully in Blender
and arrives in the engine as flat grey.

So: build procedurally → unwrap → **bake to images** → rewire → export. The
bake is not an optimisation, it is the only way the material leaves Blender.
`texlib.bake_set()` and `apply_baked()` do it, and `texlib.export()` prints the
embedded image count so a silent failure cannot ship.

## What to put in the brief

As with modelling, write more than you think you need to. The agent audits its
own work against the layers you name, so a vague brief gives it nothing to
check.

- **What the surface is, in words.** "Limestone ashlar, weathered fifty years."
  A material is a claim about history — say what happened to it.
- **The layers, and where each one sits.** "Damp and mossy in the bottom two
  metres and on the north face. Bleached where the sun hits. Lichen in the
  joints." Each becomes a mask the agent must show you.
- **The palette**, if the project has one. Materials drift off a palette faster
  than models do.
- **How close it is seen**, which sets the map size and the texel density.
- **What it must not look like.** "Not a green smear." "Not brand new."

## Why masks are the whole game

A material is a base surface plus things that sit on it *in particular places*.
Moss low down and on the shaded side; rust around fixings; dirt in the
crevices; wear on the edges that get handled. Those placements are what make a
surface read as weathered rather than as tinted, and every one of them is a
mask.

Which is why the contact sheet renders **each mask on its own, in grey**. "The
moss is wrong" is not actionable; "the moss mask covers the whole south wall
instead of the bottom two metres" is. Nine times out of ten the surface is fine
and the placement is not.

The other shot that decides things is **raking light**. Under flat front light
a painted-on suggestion of texture and real relief look identical. Under a
light skimming the surface they do not.

## Choosing a mask

| Mask | Reaches for |
|---|---|
| `mask_height(lo, hi)` | What gravity and weather decide — damp plinths, tide marks, snow |
| `mask_facing(dir)` | The shaded or weather side. Moss goes north |
| `mask_cavity(dist)` | Inside corners. **The one that works on flat-faced low-poly** |
| `mask_curvature()` | Concave creases — needs real curvature, gives nothing on flat faces |
| `mask_edges(r)` | Exposed corners: rubbed paint, polished metal |
| `mask_noise`, `mask_voronoi` | Breaking up anything too even |

Coherent beats random: a mask driven by one noise field puts its patches in
runs, the way real staining goes, where per-face randomness gives an even
speckle that reads as noise rather than weather.

## The cheap route, when UVs are not worth it

`texlib.vertex_colour(obj, fn)` writes per-vertex colour, which glTF carries as
`COLOR_0`. No UVs, no bake, no image files. It cannot hold detail finer than
the mesh, but unlike a per-face material assignment it **interpolates** — which
is the difference between a damp band that fades out and a row of green
rectangles.

## What this cannot do

No image-based source textures — everything is procedural or baked from
procedural. No hand-painting, no photo scans, no decals or transfers, no UV
seam editing beyond what smart projection gives you. Displacement is fake:
bump and normal maps only, so a silhouette stays as smooth as it was modelled.

## Sources

- [LL3M](https://arxiv.org/html/2508.08228v1) and
  [3D-GPT](https://arxiv.org/abs/2310.12945) — render → critique → refine, and
  code as the representation. The same argument applies to a surface as to a
  shape.
