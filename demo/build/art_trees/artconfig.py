# Contact-sheet numbers for asset group 1, the tree and scrub kit.
#
# WHY THIS IS NOT art/artconfig.py
#
# artconfig.py holds the numbers the sheet is judged against, and the two
# quantities that matter most in it -- pixels per metre, and how much ground the
# grid covers -- are set by how far away the asset is. Groups 3 and 4 are
# emissive props at 36-104 m, half a metre across, and art/artconfig.py is
# rightly tuned for them: a 0.5 m grid step and renders at 26 and 18 px/m. This
# group is 1.2 to 16 m tall and is read from 60 to 300 m. On that sheet a 9 m
# oak crown overruns the grid entirely and there is no render at the distance
# the pine stand is actually seen from.
#
# So group 1 keeps its own config and shares the rest of the toolkit. lib.py,
# boxmodel.py and shots.py are imported from art/ unchanged; only this file
# differs, and build_trees.py and shots_trees.py put this directory ahead of
# art/ on sys.path to pick it up.
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))


# ---------------------------------------------------------------- where things go

OUT = os.environ.get('ART_OUT') or os.path.join(ROOT, '..', 'docs', 'models')
SHOTS = os.environ.get('ART_SHOTS') or os.path.join(HERE, 'shots')


# ---------------------------------------------------------------- scale

UNITS_PER_M = 1.0
FIGURE_H = 1.75 * UNITS_PER_M

# shots.py draws the checker out to GRID_STEP * 9, so a 1 m step covers 18 m --
# enough to hold an 11 m oak's 9 m crown with room to see it end. The major line
# is 5 m because the asset table is written in those terms ("11 h x 9 spread"),
# so a crown that overruns its brief is countable rather than measurable.
GRID_STEP = 1.0 * UNITS_PER_M
GRID_MAJOR = 5.0 * UNITS_PER_M


# ---------------------------------------------------------------- the hero shot

# The scene camera is a person standing on the drove road: eye at y = -1.0 with
# the outfield at -4.5, looking at trees 60-300 m off (ART-DIRECTION 4.1). A
# tree's mid-height therefore sits almost exactly on the lens axis, so the
# elevation these are really read from is a few degrees -- not the 35 of an
# isometric game. Judging a tree from above hides the one thing that matters
# about it, which is how the branch structure crosses the sky.
#
# 9 degrees rather than 0: shots.py stands the model on a ground plane at z = 0,
# and a camera at or below it renders the sheet black.
HERO_ELEVATION_DEG = 9.0

# The hero bearing, converted from the Three.js camera in ART-DIRECTION 4.1.
HERO_AZIMUTH_DEG = 56.5

HERO_ORTHOGRAPHIC = True
HERO_LENS = 63.0
HERO_DISTANCE = None
HERO_HEADINGS = (0.0, 90.0, 180.0, 270.0)


# ---------------------------------------------------------------- small renders

# A 1080-line frame at 32 degrees vertical is 1883 / distance pixels per metre.
#
#   nearest trees, both frame edges     60 m  ->  31 px/m
#   treeline and field boundaries      150 m  ->  12.5 px/m
#   the pine stand on the ridge    240-300 m  ->  7 px/m
#
# The last one is the real test for the pine and the yew: at 7 px/m a 16 m tree
# is 112 pixels tall and either the profile reads or the asset is decoration.
SMALL_RENDERS = (
    ('60m', 31.0, 3),
    ('150m', 12.5, 7),
    ('280m', 7.0, 12),
)


# ---------------------------------------------------------------- look

RES = 900

# Flat. These are read at 30-300 m at night; a smooth normal on a five-sided
# branch is mush at that size, and the evergreen masses want facets.
SMOOTH_DEFAULT = False

# 6 by default. A trunk asks for 8 explicitly and a twig asks for 3, so this
# only catches the odd primitive.
CYL_SEGMENTS = 6

# The scene's own night palette, so the sheet looks like the picture: sky-horizon
# for the fill, moon-cold for the key, turf-night for the ground. Everything
# unlit renders near black, which is correct -- these assets are silhouette and
# nothing else, and silhouette.png is where they get judged. Build with
# TREE_LOOK=1 when a join needs looking at.
SKY = 0x1C2C42
SUN = 0xAFC8EC
GROUND = 0x1A2419
GROUND_ALT = 0x20211C
GRID_LINE = 0x3A4553
FIGURE = 0x2A3340

SUN_ENERGY = 2.2

# The moon: south-west, 34 degrees up (ART-DIRECTION 3.1), which is behind the
# castle and behind every tree in the frame.
SUN_FROM = (-58.6, -58.6, 55.9)


# ---------------------------------------------------------------- export

EXPORT_YUP = True

# The heaviest piece in group 1 is tree_ash_bare at ~1300. Warn above 1400, so
# anything that drifts off its line in the asset table is flagged.
TRI_BUDGET = 1400
