# Project numbers for "Nightfall at the March Castle", asset groups 3 and 4.
#
# Retuned from the shipped default for one reason: every piece in these two
# groups is a light source seen at night from ninety metres, and a daylight
# contact sheet tells you nothing at all about an emissive object. A brazier
# photographed at noon is a bucket. So the sky, the sun and the ground here are
# the scene's own numbers out of ART-DIRECTION.md sections 2 and 3, and the
# hero camera is the scene's own bearing.
#
# Edit this file. Do not edit lib.py or shots.py.
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))


# ---------------------------------------------------------------- where things go

# ART_OUT / ART_SHOTS point at a scratch directory while these assets are in
# development, so nothing lands in the repo until the scene is wired up. The
# fallback is where the published site loads from.
OUT = os.environ.get('ART_OUT') or os.path.join(ROOT, '..', 'docs', 'models')
SHOTS = os.environ.get('ART_SHOTS') or os.path.join(HERE, 'shots')


# ---------------------------------------------------------------- scale

UNITS_PER_M = 1.0
FIGURE_H = 1.75 * UNITS_PER_M

# No tile grid in this world. Half a metre reads a brazier leg and two metres
# reads a bonfire, which is the range these assets live in.
GRID_STEP = 0.5 * UNITS_PER_M
GRID_MAJOR = 2.0 * UNITS_PER_M


# ---------------------------------------------------------------- the hero shot

# ART-DIRECTION 4.1: camera at Three.js (78.9, -1.0, 43.3) looking at
# (3.9, 9.3, -6.4). Converted to this rig's target-to-camera bearing in
# Blender's Z-up frame, that is azimuth 56.5 degrees, elevation -6.5.
#
# The elevation is NEGATIVE in the real scene -- the ward floor is a metre
# above the lens. shots.py puts a ground plane at z = 0, so a negative
# elevation buries the camera under it and every shot renders black. 9 degrees
# is the lowest reading that still clears the ground, and it is close enough
# that the grazing view these props are actually seen at is what the sheet
# shows.
HERO_ELEVATION_DEG = 9.0
HERO_AZIMUTH_DEG = 56.5

# Orthographic, even though the scene camera is a 32-degree perspective: at 71
# to 104 m a one-metre prop has no perspective worth the name, and orthographic
# is what makes SMALL_RENDERS honest -- under a perspective camera shots.py
# cannot hold pixels-per-metre, so the labels would lie. three_quarter.png is
# still a perspective shot and still catches a bad join.
HERO_ORTHOGRAPHIC = True
HERO_LENS = 63.0          # 32 deg vertical on a 36 mm sensor, if ever needed

HERO_DISTANCE = None
HERO_HEADINGS = (0.0, 90.0, 180.0, 270.0)


# ---------------------------------------------------------------- small renders

# Measured off the hero camera, not guessed. A 1080-line frame at a 32 degree
# vertical field of view is 1883 / distance pixels per metre:
#
#   ward bonfire        71.2 m ->  26 px/m   (its 1.40 m of flame is 37 px)
#   gate brazier        74.9 m ->  25 px/m   (1.10 m of brazier is 28 px)
#   lit keep window    103.6 m ->  18 px/m   (a 2.10 m pane is 38 px)
#   bridge lantern      36.4 m ->  52 px/m   (0.34 m of lantern is 18 px)
#
# So 26 for everything in the ward and 18 for everything on the keep. If a
# piece does not read at ppm18 it does not read.
SMALL_RENDERS = (
    ('ppm26', 26.0, 8),
    ('ppm18', 18.0, 12),
)


# ---------------------------------------------------------------- look

RES = 900

# Faceted. Nothing here is seen closer than 36 m and a shard cluster wants
# facets to break the light against.
SMOOTH_DEFAULT = False
CYL_SEGMENTS = 8

# Contact sheet colours only -- none of this reaches an exported model. These
# are the scene's own palette so the sheet looks like the picture:
#
#   sky-horizon #1C2C42 stands in for the HemisphereLight fill
#   moon-cold   #AFC8EC is the DirectionalLight
#   turf-night  #1A2419 and earth-wet #20211C are the ground
#
# Everything unlit therefore renders near black, which is correct and is the
# whole point -- silhouette.png is where the shape gets judged, and the
# emissive parts are the only things meant to be visible in colour.
SKY = 0x1C2C42
SUN = 0xAFC8EC
GROUND = 0x1A2419
GROUND_ALT = 0x20211C
GRID_LINE = 0x3A4553      # the top of the stone-dark range: a visible ruler
FIGURE = 0x2A3340

# A moon, not a sun. Enough to separate a dark form from dark ground and no
# more; anything brighter and the cool mass starts competing with the fire,
# which is the one thing section 2 forbids.
SUN_ENERGY = 2.2

# The moon: south-west, 34 degrees elevation (ART-DIRECTION 3.1). Blender is
# Z-up with +X east and +Y north, so south-west and up is
# (-cos34*cos45, -cos34*sin45, sin34) * 100.
SUN_FROM = (-58.6, -58.6, 55.9)


# ---------------------------------------------------------------- export

EXPORT_YUP = True

# The heaviest piece in these two groups is the bonfire, at about 520.
TRI_BUDGET = 600
