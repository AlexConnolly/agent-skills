# Project numbers for "Nightfall at the March Castle" — the GROUND build.
#
# A private copy of the toolkit config, because several agents are building this
# scene at once and artconfig is global state. Nothing here is generic: the
# defaults ship tuned for a prop on a table and every one of them is wrong for
# 400 m of terrain read from a standing eye 90 m away.
#
# See demo/ART-DIRECTION.md §4.1 for the camera these numbers come from.
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))


# ---------------------------------------------------------------- where things go

OUT = os.environ.get('ART_OUT') or os.path.join(ROOT, '..', 'docs', 'models')
SHOTS = os.environ.get('ART_SHOTS') or os.path.join(HERE, 'shots')

# terrain.json — the one source of truth for ground height, sampled by the
# placement code so nothing floats. §6.3.
DATA = os.environ.get('ART_DATA') or os.path.join(ROOT, '..', 'docs', 'data')


# ---------------------------------------------------------------- scale

UNITS_PER_M = 1.0
FIGURE_H = 1.75 * UNITS_PER_M

# The shipped 1 m / 4 m grid lays an 18 m mat under a 400 m terrain, so the
# contact sheet shows a model floating over a postage stamp. checker_grid()
# derives its extent as GRID_STEP * 9.
GRID_STEP = 20.0 * UNITS_PER_M
GRID_MAJOR = 100.0 * UNITS_PER_M


# ---------------------------------------------------------------- the hero shot
#
# ART-DIRECTION §4.1, converted from Three.js to Blender (X_b = X_t,
# Y_b = -Z_t, Z_b = Y_t):
#
#     camera  Three (78.9, -1.0, 43.3)  ->  Blender ( 78.900, -43.300, -1.000)
#     target  Three ( 3.9,  9.3, -6.4)  ->  Blender (  3.900,   6.400,  9.300)
#
# which is 90.560 m of slant range, 89.973 m of it horizontal, on a bearing
# 33.5 deg south of due east, with the lens 10.3 m BELOW the target — hence the
# negative elevation. The camera is a standing person on the drove road, not a
# drone, and the ward floor is a metre above the lens.
HERO_ELEVATION_DEG = -6.5307
HERO_AZIMUTH_DEG = 56.4689

# A perspective scene, not an isometric game. 32 deg vertical on 16:9 works out
# at 54 deg horizontal; the contact sheet's iso_* frames are square, so 35.3 mm
# on a 36 mm sensor reproduces the horizontal field of view there and
# heroshot.py sets the real 16:9 framing itself.
HERO_ORTHOGRAPHIC = False
HERO_LENS = 35.33

# Fixed, not derived from the bounding box: shots.py would otherwise stand a
# 400 m terrain off at 2.4 km and render the hero shot as a smudge.
HERO_DISTANCE = 90.56

HERO_HEADINGS = (0.0, 90.0, 180.0, 270.0)


# ---------------------------------------------------------------- small renders
#
# Off. The "real pixels per metre" shot exists to check a prop that is drawn 40
# px wide. This model is drawn 1920 px wide from 90 m, so the hero render IS
# the real-size shot and a 10 000 px render of the same thing is not a check.
SMALL_RENDERS = ()


# ---------------------------------------------------------------- look

RES = 1000

# Faceted. Limestone breaks along bedding planes and the whole scene is read as
# silhouette and value, so a smooth normal buys nothing and costs the facets
# that make a rock shoulder read as rock.
SMOOTH_DEFAULT = False
CYL_SEGMENTS = 12

# Contact-sheet only; never reaches an exported model. Deliberately daylight:
# the night look is judged in heroshot.py, and a black render is no way to
# judge a landform.
SKY = 0x9DB0C0
SUN = 0xFFF4E0
GROUND = 0x8CA36B
GROUND_ALT = 0x9DB27C
GRID_LINE = 0xBFAF8E
FIGURE = 0x6F8CA6

SUN_ENERGY = 3.1

# The moon. Three.js DirectionalLight at (-115, 112, 115) -> Blender
# (-115, -115, 112): south-west, elevation 34 deg, behind the castle.
SUN_FROM = (-115.0, -115.0, 112.0)


# ---------------------------------------------------------------- export

EXPORT_YUP = True

# Ground budget: ~9k platform + ~18k outfield + ~6k ridge. §6.3 / §8.7.
TRI_BUDGET = 20000


# ---------------------------------------------------------------- the world
#
# Shared by build_ground.py and heroshot.py so there is one definition of where
# the camera is and what the levels are.

CAM = (78.9, -43.3, -1.0)          # Blender
CAM_TARGET = (3.9, 6.4, 9.3)       # Blender
CAM_FOV_V_DEG = 32.0
CAM_ASPECT = 16.0 / 9.0
