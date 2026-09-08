# blender-model

Teaches an agent to build 3D models in Blender as parametric Python that
exports to glTF, working a **build → render → look → fix** loop against a
rendered contact sheet.

## Why a loop, and not a better prompt

Geometry has a property most code does not: it can be completely wrong in a way
that is invisible in the source. All of these read perfectly as Python —

- heights authored into Y when Blender is Z-up, so the prop lies on its back
- a rotation sign inverted on two parts at once, so an A-frame splays into a trough
- a size taken from a comment rather than the constant the app actually uses
- a part origin off the joint, so a limb swings from the elbow

None of them are subtle once you see a picture. So the agent renders and looks
at its own work, at least five times, and does not count a pass in which it did
not open a render.

This follows [LL3M](https://arxiv.org/html/2508.08228v1) and
[3D-GPT](https://arxiv.org/abs/2310.12945): code as the representation rather
than a mesh blob, multi-view render → critique → refine, and localised edits
rather than regeneration — without LL3M's separate vision model, which was
working around a limitation that no longer exists.

## Install

```
/plugin marketplace add AlexConnolly/agent-skills
/plugin install blender-model@connolly-skills
```

Or copy `skills/blender-model/` into `~/.claude/skills/` and
`agents/model-smith.md` into `~/.claude/agents/`.

**Requires** [Blender](https://www.blender.org/download/) 4.x or 5.x on `PATH`.
Nothing else — the toolkit imports only Blender's own modules.

## Set up a project

Copy `skills/blender-model/scripts/` into the project as `art/`, then edit
`artconfig.py`. That file holds every project-specific number so `lib.py` and
`shots.py` stay identical everywhere:

```python
OUT = os.path.join(ROOT, 'public', 'models')   # where your app loads .glb from
UNITS_PER_M = 1.0                              # what one Blender unit means
FIGURE_H = 1.75 * UNITS_PER_M                  # your character's height
GRID_MAJOR = 4.0 * UNITS_PER_M                 # your tile size
HERO_ELEVATION_DEG = 35.264389682754654        # your camera, if it is fixed
SMALL_RENDERS = (('60px', 15.0, 6),)           # the px/m you are seen at
```

`OUT` is the one that fails silently. Point it somewhere the app does not load
from and every render shows you the previous build.

## Use it

```
/blender-model a hay barn, open on the long side, twice a man to the eaves
```

Or let it fire on its own — the skill description triggers on any request to
build, fix or improve a 3D model.

Give it: what the thing is and what it must communicate, how big against a
person, where it goes and what it sits next to, the camera it is read from, and
anything it must not be.

## Running the toolkit by hand

```bash
blender --background --python art/build_props.py -- prop_hedge
blender --background --python art/shots.py       -- prop_hedge
```

`ART_OUT` and `ART_SHOTS` override the configured paths, for CI or for trying a
build without touching your app's assets.

## What is in it

| File | |
|---|---|
| `scripts/boxmodel.py` | `Form` — one mesh grown from a cube. Extrude, inset, loop cut, bevel, taper, bend, warp, mirror. |
| `scripts/lib.py` | Primitives, swept forms (`loft`, `profile`), materials with sRGB→linear conversion, node hierarchy, glTF export with a triangle and ground-contact report. |
| `scripts/shots.py` | The contact sheet. Fourteen renders per model. |
| `scripts/artconfig.py` | Every project-specific number. |
| `skills/blender-model/reference.md` | Full API reference. |
| `agents/model-smith.md` | The sub-agent that runs the loop. |

Grow a `Form` when the surface is continuous. Loft or sweep when the section is
known at every station — a hull, a pipe, a handrail. Trying to pull a boat out
of a cube with loop cuts fights the tool the whole way.

## The contact sheet

`shots.py` renders the **exported glb**, not the live scene, because the axis
convention only goes wrong at export.

| Shot | For |
|---|---|
| `iso_a..d.png` | Your app's projection at four object headings. The decision-making shots. |
| `iso_clean.png` | The same, without the grid and the scale figure. |
| `silhouette.png` | Flat black on white. Nothing to hide behind. |
| `iso_<n>px_x<N>.png` | Rendered at the real pixels-per-metre, then upscaled nearest-neighbour. The upscale adds no information — that is the point. |
| `front/side/top.png` | Orthographic. Proportion, symmetry, ground contact. |
| `three_quarter.png` | Perspective. Where a bad join shows. |

It prints the bounding box in metres, in tiles, and as a multiple of your
figure height, plus the triangle count and a warning if the model is sunk into
or floating above the ground.

The 1.75 m scale figure standing beside the model is the most useful thing in
the sheet. Sizing errors do not show up in code and do not show up in an
isolated render. They show up next to a person.
