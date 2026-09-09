# Project numbers for "Nightfall at the March Castle", asset group 7.
#
# Retuned from the shipped default because nothing about the default sheet
# suits these four pieces. They are 26 to 44 m across, so the toolkit's
# half-metre grid is invisible under them; they are eleven per cent opaque, so
# a daylight sky washes them out completely; and they are read at two to seven
# degrees above the horizontal, so the toolkit's 30-degree hero elevation shows
# a plan shape that in the real frame is never seen at all.
#
# Edit this file. Do not edit lib.py or shots.py.
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))


# ---------------------------------------------------------------- where things go

# ART_OUT / ART_SHOTS point at a scratch directory while these assets are in
# development, so nothing lands in the repo until the scene is wired up.
OUT = os.environ.get('ART_OUT') or os.path.join(ROOT, '..', 'docs', 'models')
SHOTS = os.environ.get('ART_SHOTS') or os.path.join(HERE, 'shots')


# ---------------------------------------------------------------- scale

UNITS_PER_M = 1.0
FIGURE_H = 1.75 * UNITS_PER_M

# These are the largest assets in the scene apart from the ground itself. A
# half-metre checker under a 44 m slab is noise; two metres reads the depth of
# the mist and ten metres reads its plan.
GRID_STEP = 2.0 * UNITS_PER_M
GRID_MAJOR = 10.0 * UNITS_PER_M


# ---------------------------------------------------------------- the hero shot

# ART-DIRECTION 4.1: eye at Three.js (78.9, -1.0, 43.3). Worked out per piece,
# because for mist the elevation IS the shot:
#
#   the hollow, NE, ground -6.5, sheet top about -4.6, roughly 87 m away
#       -> 2.4 degrees above the horizontal
#   the ditch, water -6.0, sheet top about -5.2, nearest arc about 36 m
#       -> 6.7 degrees
#   a foreground wisp on the knoll, top about -2.3, 28 m away
#       -> 2.7 degrees
#
# So 5 degrees, and that is not a compromise between shape-reading and honesty
# -- it is the shot. A horizontal sheet at 5 degrees is nearly all its own
# edge, which is why the vertical alpha gradient and the skyline of the top
# surface are what these pieces are actually made of. top.png still exists if
# the plan ever needs checking.
#
# shots.py puts an opaque ground plane at z = 0 and the camera offset is
# distance * sin(elevation), so any positive elevation clears it. 5 works.
HERO_ELEVATION_DEG = 5.0
HERO_AZIMUTH_DEG = 56.5

# Orthographic. At 36 to 90 m a 44 m slab has some real perspective, but
# orthographic is what makes SMALL_RENDERS honest -- under a perspective camera
# shots.py cannot hold pixels-per-metre and the labels would lie.
# three_quarter.png is still perspective.
HERO_ORTHOGRAPHIC = True
HERO_LENS = 63.0          # 32 deg vertical on a 36 mm sensor, if ever needed

HERO_DISTANCE = None
HERO_HEADINGS = (0.0, 90.0, 180.0, 270.0)


# ---------------------------------------------------------------- small renders

# 1883 / distance pixels per metre for a 1080-line frame at 32 degrees vertical:
#
#   hollow sheets      87 m  ->  22 px/m   (1.2 m of depth is 26 px)
#   ditch sheets       36 m  ->  52 px/m   (0.9 m of depth is 47 px)
#   foreground wisps   28 m  ->  67 px/m   (0.4 m of depth is 27 px)
#
# 22 is the one that decides whether a sheet reads at all: at 22 px/m the whole
# vertical gradient of mist_sheet_a is 26 pixels tall, and if the top edge is a
# hard line it will be a hard line there.
SMALL_RENDERS = (
    ('ppm22', 22.0, 4),
    ('ppm52', 52.0, 2),
)


# ---------------------------------------------------------------- look

RES = 900

# Flat. ART-DIRECTION group 7 asks for it and it is right: a flat-shaded dome
# gives each facet its own value under the hemisphere fill, which reads as
# structure inside the mist. Smooth shading would make it a balloon. The
# softness comes from the per-vertex alpha, which interpolates whatever the
# normals do.
SMOOTH_DEFAULT = False
CYL_SEGMENTS = 8

# Contact sheet colours only -- none of this reaches an exported model.
#
#   sky-horizon #1C2C42 stands in for the HemisphereLight fill, which is what
#     actually lights these; the moon is behind the castle and does not reach
#     the hollow
#   moon-cold   #AFC8EC is the DirectionalLight
#   turf-night  #1A2419 and earth-wet #20211C are the ground
#
# GRID_LINE is deliberately dark. The default 0x3A4553 is brighter than an
# eleven-per-cent mist sheet over turf, so the ruler would read as the brighter
# object in every shot and the mist as a hole in it.
SKY = 0x1C2C42
SUN = 0xAFC8EC
GROUND = 0x1A2419
GROUND_ALT = 0x20211C
GRID_LINE = 0x2A3340
FIGURE = 0x39414B         # lifted off stone-dark so the figure survives 5 deg

# A moon, not a sun, and behind the castle: these sheets are lit almost
# entirely by the cold sky. Anything brighter and the mist competes with the
# fire, which section 2 forbids.
SUN_ENERGY = 1.6

# South-west, 34 degrees elevation (ART-DIRECTION 3.1). Blender is Z-up with +X
# east and +Y north, so south-west and up is
# (-cos34*cos45, -cos34*sin45, sin34) * 100.
SUN_FROM = (-58.6, -58.6, 55.9)


# ---------------------------------------------------------------- export

EXPORT_YUP = True

# The heaviest piece in this group is mist_sheet_a at about 200.
TRI_BUDGET = 240
