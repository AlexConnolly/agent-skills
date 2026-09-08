---
name: blender-model
description: Build or fix a 3D model in Blender — a prop, vehicle, building, character or piece of scenery — as parametric Python that exports to glTF. Delegates to the model-smith agent, which works a build → render → look → fix loop rather than writing geometry blind. Use for any request to make, change or improve a 3D model, mesh, or game asset.
allowed-tools: Agent, Read, Glob, Grep, Bash(blender:*), Bash(git:*)
---

# Making a model that reads

## Rule one: you do not do this yourself

**Always spawn the `model-smith` agent.** One per model. Do not write geometry
in the main loop, however small the change looks.

```
Agent(
  subagent_type: "model-smith",
  description:   "Build the <thing>",
  prompt:        "<the brief — see below>",
  run_in_background: false
)
```

The reason is not tidiness. This work is iterative improvement — do the work,
capture it, work out what to improve, do that — at least five times per model,
and that loop is mostly images. Run inline it fills the context of whatever
else you were doing, and you start skipping renders to save room. That is
exactly when the bad models get made.

Several unrelated models: several agents, in parallel, one each.

## Before the first model in a project

The toolkit needs to be reachable from the build script, and `artconfig.py`
needs your project's numbers in it. Either copy `scripts/` into the project as
`art/`, or add it to `sys.path`. Then set, in `artconfig.py`:

| Setting | What it is |
|---|---|
| `OUT` | where `.glb` files must land for your app to load them |
| `UNITS_PER_M`, `FIGURE_H` | what one unit means, and how tall your character is |
| `GRID_MAJOR` | your tile or block size, if you have one |
| `HERO_*` | your app's camera angle, if it is fixed |
| `SMALL_RENDERS` | the pixels-per-metre the object is actually seen at |
| `SMOOTH_DEFAULT`, `CYL_SEGMENTS` | far-off toon look, or close-up |

`OUT` is the one that fails silently. Point it somewhere the app does not load
from and every render shows you the previous build while you "fix" a model that
was already correct.

## What to put in the brief

The agent knows the loop. It does not know your intent, and it cannot infer
your taste. **Write more than you think you need to.** A paragraph gets you a
generic object; a detailed brief with a named art style and an explicit feature
list gets you the thing you were picturing.

This is not just a quality nicety. The agent's critique step audits the brief
one required element at a time, so **a brief with no feature list gives the
audit nothing to check** — and a model whose missing parts nobody enumerated is
exactly the model that ships with a wall or a cabin absent.

Give it:

- **What the thing is, and what it has to communicate.** "A tent. It has to say
  soldiers live here, not that a keep was built here." The second half is the
  part that does the work.
- **The art style, named.** Faceted low-poly read from a distance, or formed
  and smooth-shaded at arm's length? Stylised or accurate? Say what it should
  look like *as art* — a period, a game, a reference, a palette — not just what
  object it is. "A real Welsh castle, not a fantasy one" is worth a paragraph
  of adjectives.
- **The features you expect to see, as a list.** Name them. "A wall-walk with
  crenellations, a gatehouse, three towers of differing condition, a keep."
  Each becomes a line the agent must prove against a named render before it is
  allowed to stop.
- **How big, against a person.** "Waist high", "twice a man at the ridge" — not
  a number you guessed. If the project has a real figure height, say what it is
  and where it is defined.
- **Where it goes** — placed by hand, scattered, carried, instanced in its
  hundreds — and what it will sit next to.
- **The camera it is read from.** Detail below a fifth of a figure is wasted on
  a model seen from a long way up, and the defaults in `artconfig.py` assume a
  distant one.
- **Anything it must not be.** "Not a keep." "Not another woodpile." "Not a
  bathtub — if the topsides come out as parallel slab sides, keep working."
  Naming the failure mode is the single most effective line in a brief.

## What the loop is

The agent's own instructions carry it, but so you can tell whether it actually
did the work:

1. Check the thing does not already exist
2. Read the real dimensions out of the code, not out of comments
3. Author a `build_*.py` against `lib.py` / `boxmodel.py`, **Z-up**
4. `blender --background --python build_*.py -- <name>`
5. `blender --background --python shots.py -- <name>` and **`Read` the
   renders** — the hero shot at four headings, the three orthographics, the
   flat-black silhouette, and the small ones at real pixel size
6. Name the specific defect in the specific view
7. Patch that part; do not regenerate the function
8. Repeat. **Five passes minimum**, none counted unless a render was opened
9. Check it in place, at the distance the app draws it

## Why it is built this way

Three things are load-bearing, and they come from published work on getting
language models to produce decent geometry rather than from taste:

**Code is the model, not a mesh.** Parametric Python that a person can read and
re-run beats an exported blob: it can be edited in place, diffed, reviewed, and
regenerated at a new size. (3D-GPT; LL3M.)

**The render is the feedback, and there is no substitute.** Systems that render
the object and feed the picture back before editing produce dramatically better
results than ones that write geometry open-loop. LL3M uses multiple views and a
critic pass for exactly this. `shots.py` is that, minus the second model: the
agent renders and looks at its own work, because current models can see, and
the pipelines that needed a separate vision model to do the looking were
working around a limitation that no longer exists.

**Localised edits beat regeneration.** LL3M found that without the previous
code in context, refinement produces a fundamentally different asset rather
than a corrected one. Hence step 7.

**Play to the shape of the tool.** Language models are good at hard-surface,
architectural, primitive-assembly geometry and weak at organic form. Chunky
low-poly, vehicles, buildings and props are squarely in the first category. Do
not try to sculpt a face.

## What this toolkit cannot do

Know this before you start, so you do not spend passes discovering it:

- **No UVs and no textures.** Every surface is one flat PBR colour. There are
  no normal, roughness or albedo maps and no vertex colours.
- **No scatter, particle system or geometry nodes.** Instancing is a `for`
  loop placing real meshes.
- **No displacement or subdivision modifiers.** Shaping is destructive bmesh
  work: `warp`, `taper`, `bend`, `cut_at`, `bevel`.
- **No HDRI or global illumination** in the contact sheet. One sun, one flat
  sky, tuned for reading a silhouette rather than for a beauty render.

So **photorealism is out of scope**, and so is anything whose character lives
in its surface rather than its shape — leather, rust, moss, wood grain, dirt,
wear. If a brief asks for those, say so plainly and build the form well; what
you are producing is either a stylised asset or a blockout for a texturing
pipeline, and both are worth doing properly.

Irregularity and decay *can* be expressed geometrically. `Form.warp()` takes an
arbitrary per-vertex function, so a slumped wall line, a bowed tower or
crenellations eroded to uneven stumps are all reachable — deterministic
pseudo-noise from the coordinates keeps them reproducible. `repaint()` takes a
`(centre, normal)` test, so surfaces that face a particular way can take a
different colour. That is the honest extent of it.

## What is in the toolkit

`scripts/`, all documented in [reference.md](reference.md):

- **`boxmodel.py`** — `Form`, one mesh grown from a cube: extrude, inset, loop
  cut, bevel, taper, bend, warp, mirror. For anything organic or continuous.
- **`lib.py`** — primitives (`box`, `cyl`, `ring`, `torus`, `wedge`), swept
  forms (`profile`, `loft`), materials with correct sRGB→linear conversion,
  node hierarchy for animated parts, and glTF export with a triangle and
  ground-contact report.
- **`shots.py`** — the contact sheet. Fourteen renders per model.
- **`artconfig.py`** — every project-specific number, in one file.

Grow a form when the surface is continuous. Loft or sweep when the section is
known at every station — a hull, a pipe, a handrail. Trying to pull a boat out
of a cube with loop cuts fights the tool the whole way.

## Sources

- [LL3M: Large Language 3D Modelers](https://arxiv.org/html/2508.08228v1) —
  multi-view render → critique → refine, code as representation, shared code
  context for localised edits.
- [3D-GPT: Procedural 3D Modeling with LLMs](https://arxiv.org/abs/2310.12945)
  — procedural code over direct mesh generation.
- Blender Studio, *Step by Step — Low Poly Character Creation* — the box
  modelling workflow `boxmodel.py` implements.
