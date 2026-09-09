# Project numbers for "Nightfall at the March Castle" — the PROPS builds.
#
#   build_rocks.py     group 2  rock and outcrop kit
#   build_crossing.py  group 5  bridge, causeway apron, ditch water, rut pools
#   build_track.py     group 6  track ribbon, drystone wall kit, hurdles, gate
#   build_clutter.py   group 8  wayside cross, cart, woodstack, posts, hay
#
# A private copy, because four agents are building this scene at once and
# artconfig is global state. Nothing here is the shipped default: the toolkit
# ships tuned for one prop on a table under an isometric game camera, and this
# scene is a low grazing perspective camera at night on a 400 m landscape.
#
# See demo/ART-DIRECTION.md sections 2, 4.1, 5 and 6.1 for where every number
# below comes from.
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))


# ---------------------------------------------------------------- where things go
#
# Scratch, NOT the repo. The repo holds the build scripts and the briefs; the
# .glb files are output and are rebuilt by make.py.
SCRATCH = os.path.join(os.environ.get('LOCALAPPDATA', '/tmp'), 'Temp',
                       'nightfall_props')
OUT = os.environ.get('ART_OUT') or os.path.join(SCRATCH, 'models')
SHOTS = os.environ.get('ART_SHOTS') or os.path.join(SCRATCH, 'shots')

# texlib writes its bakes here; nothing in these four scripts bakes, but
# texconfig is imported by texlib for vertex_colour().
MODELS = OUT


# ---------------------------------------------------------------- scale

UNITS_PER_M = 1.0
FIGURE_H = 1.75 * UNITS_PER_M

# checker_grid() derives its extent as GRID_STEP * 9, so 2 m squares lay a 36 m
# mat — big enough for a 12 m bridge and a 9 m apron to sit on with room to
# read the ground contact, small enough that a 1.1 m boulder is not a speck.
# The 10 m majors are the scale the eye actually counts in at this distance.
GRID_STEP = 2.0 * UNITS_PER_M
GRID_MAJOR = 10.0 * UNITS_PER_M


# ---------------------------------------------------------------- the hero shot
#
# The scene camera (section 4.1) is a standing person's eye 1.7 m up, ninety
# metres out, looking UP at the castle: elevation -6.5 deg. That is the right
# angle for judging the castle and the wrong one for judging a prop, because a
# 1.1 m boulder seen from dead level shows no top surface at all and every
# decision about its bedding planes becomes unjudgeable.
#
# 15 deg is the compromise, and it is not arbitrary: it is roughly the angle
# from the camera's eye down to the near foreground props on the knoll (the
# wayside cross at 22 m, the rut pools at 12-45 m), which are the pieces in
# these four groups that are read closest and matter most.
HERO_ELEVATION_DEG = 15.0
HERO_AZIMUTH_DEG = 56.4689          # the hero bearing, 33.5 deg S of due E

# A perspective scene, not an isometric game. 32 deg vertical on 16:9 works out
# at 54 deg horizontal, and the contact sheet's iso_* frames are square, so
# 35.33 mm on a 36 mm sensor reproduces that horizontal field of view.
HERO_ORTHOGRAPHIC = False
HERO_LENS = 35.33

HERO_HEADINGS = (0.0, 90.0, 180.0, 270.0)

# shots.py parks a perspective camera at six times the model's size, which on a
# 54 deg lens puts a 6 m rock across 16 % of the frame and makes every
# judgement about its bedding a judgement about forty pixels. These four groups
# run from a 0.7 m boulder to a 180 m track ribbon, so no single number is
# right; the driver sets it per model.
#
#   ART_DIST=13 blender --background --python shots.py -- rock_outcrop_a
#
# The real size the piece is seen at is not lost by this — that is what
# SMALL_RENDERS above is for, and those are rendered at true pixels per metre
# whatever the framing distance.
HERO_DISTANCE = (float(os.environ['ART_DIST'])
                 if os.environ.get('ART_DIST') else None)


# ---------------------------------------------------------------- small renders
#
# (label, pixels per metre, upscale). At 1920 px across a 54 deg horizontal
# field, pixels per metre = 1884 / distance, so:
#
#     wayside cross    22 m   86 px/m
#     ditch bridge     36 m   52 px/m
#     near wall run    25 m   75 px/m
#     boulders         40 m   47 px/m
#     hurdles          60 m   31 px/m
#     far outcrops     85 m   22 px/m
#
# Two shots bracket that: the near foreground, and the far end of the field.
SMALL_RENDERS = (('26px', 26.0, 8), ('80px', 80.0, 3))


# ---------------------------------------------------------------- look

RES = 900

# Faceted. Limestone breaks along bedding planes, drystone is laid stone, and
# the whole scene is read as silhouette and value under a moon that is behind
# it. A smooth normal buys nothing here and costs the facets that make rock
# read as rock. Individual close-up pieces override this per object.
SMOOTH_DEFAULT = False

# 8 is the shipped default and is right for a 1 m boulder at 40 m. The wayside
# cross and the cart wheels ask for more at their own call sites.
CYL_SEGMENTS = 8

# Contact-sheet only; never reaches an exported model. Deliberately brighter
# than the night scene: a black render is no way to judge a shape, and the
# night look is judged in props_shots.py under the real palette.
SKY = 0x9DB0C0
SUN = 0xFFF4E0
GROUND = 0x8CA36B
GROUND_ALT = 0x9DB27C
GRID_LINE = 0xBFAF8E
FIGURE = 0x6F8CA6

# 3.1 is the shipped value and it is tuned for an albedo around 0.5. This
# scene's palette tops out at stone-lit 0x6A and the rock sits at 0x3A, which
# is 4.5 % linear reflectance, so at 3.1 the contact sheet shows a black blob
# and no judgement about form is possible from it. The night VALUES are judged
# in props_shots.py under the real palette; this sheet exists to judge SHAPE.
SUN_ENERGY = 9.5

# The moon, at the real bearing. Three.js DirectionalLight (-115, 112, 115)
# -> Blender (-115, -115, 112): south-west, elevation 34 deg. Judging which
# face catches the light against any other direction is judging a scene that
# does not exist.
SUN_FROM = (-115.0, -115.0, 112.0)


# ---------------------------------------------------------------- export

EXPORT_YUP = True

# The heaviest single piece in these four groups is the track ribbon at ~1400.
# summarise() flags anything over this; the per-piece budgets from section 5
# are printed by each build script against its own table.
TRI_BUDGET = 1600


# ---------------------------------------------------------------- the world
#
# Section 6.1, verbatim, in Three.js metres. THE GROUND AGENT OWNS THESE.
# Nothing in these four scripts may invent a level; it reads it from here.
WARD = 0.0                  # ward floor, castle base, platform top
BERM = 0.0                  # 6 m of level ground outside every wall foot
TOE = -4.5                  # bottom of the platform batter
OUTFIELD = -4.5             # general field level
DITCH_BOTTOM = -6.8
DITCH_WATER = -6.0          # 0.8 m of standing water
KNOLL_CREST = -2.7          # ESE, ~88 m out; the camera stands here
HOLLOW = -6.5               # NE, where the mist pools
RIDGE = 6.0                 # N and W, 240-320 m

# Section 4.1, converted to Blender (X_b = X_t, Y_b = -Z_t, Z_b = Y_t).
CAM = (78.9, -43.3, -1.0)
CAM_TARGET = (3.9, 6.4, 9.3)
CAM_FOV_V_DEG = 32.0
CAM_ASPECT = 16.0 / 9.0


def to_blender(x, y, z):
    """Three.js metres -> Blender metres. Everything in ART-DIRECTION from
    section 0.2 onward is Three.js unless it says Blender, and getting this
    backwards puts the whole crossing on the wrong side of the castle."""
    return (x, -z, y)


def bearing_to(x, z):
    """The compass bearing of a Three.js ground point, as a Blender-plane unit
    vector. Used to lay the bridge radially across the ditch."""
    bx, by = x, -z
    n = math.hypot(bx, by) or 1.0
    return (bx / n, by / n)
