# Where the drove road goes, and where it crosses the ditch.
#
# ONE definition, imported by build_crossing.py and build_track.py, because the
# bridge has to land on the road and the road has to stop at the bridge. Two
# copies of this would be two roads.
#
# Everything here is THREE.JS metres (x east, y up, z south), section 0.2.
# Convert with artconfig.to_blender() at the point of use.
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)

from terrain import Terrain      # noqa: E402


# ---------------------------------------------------------------- the platform plan
#
# build_ground.py's PLAN, converted to Three (x, -y_blender), and its section
# bands. Copied rather than imported because build_ground.py is a Blender
# script that runs `import bpy` at the top; the numbers are the ground agent's
# and if they move, these move with them.

PLAN = [(43.0, 5.0), (43.5, -9.0), (43.5, -20.0), (44.0, -27.0), (38.0, -35.0),
        (28.0, -40.0), (15.0, -41.0), (7.0, -35.5), (-6.0, -40.0),
        (-19.0, -39.0), (-30.0, -35.0), (-38.0, -28.0), (-42.0, -17.0),
        (-45.0, -8.0), (-41.5, 0.0), (-45.0, 9.0), (-43.0, 18.0),
        (-43.0, 26.0), (-35.0, 36.0), (-18.0, 39.0), (-4.0, 42.5),
        (11.0, 42.5), (24.0, 38.0), (31.0, 33.5), (38.0, 30.5), (42.0, 18.0)]
PLAN_C = (1.0, 2.0)

D_BATTER = 7.2         # 0.0 -> -4.5 at 1:1.6
D_TOE = 10.4           # the level toe band ends here: the ditch's inner lip
D_SCARP = 13.8
D_FLOOR = 19.8         # the flat ditch floor, -6.8
D_LIP = 24.2           # the counterscarp lip: the ditch's outer edge


def boundary_radius(theta):
    """Distance from PLAN_C to the platform's top edge on a bearing."""
    d = (math.cos(theta), math.sin(theta))
    best = None
    n = len(PLAN)
    for i in range(n):
        a, b = PLAN[i], PLAN[(i + 1) % n]
        ax, az = a[0] - PLAN_C[0], a[1] - PLAN_C[1]
        ex, ez = b[0] - a[0], b[1] - a[1]
        den = d[0] * (-ez) - d[1] * (-ex)
        if abs(den) < 1e-9:
            continue
        t = (ax * (-ez) - az * (-ex)) / den
        s = (d[0] * az - d[1] * ax) / den
        if t > 0 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best):
            best = t
    return best


def polar(theta_deg, r):
    th = math.radians(theta_deg)
    return (PLAN_C[0] + math.cos(th) * r, PLAN_C[1] + math.sin(th) * r)


# ---------------------------------------------------------------- the crossing
#
# 26.0 degrees is not a guess. Section 5 group 5 wants the bridge at 47 % across
# the hero frame; walking the bearing round the ditch in 2 degree steps and
# asking terrain.json where the standing water starts and stops on each one
# puts the ditch's centre at 47.7 % of frame on this bearing and nowhere else.
# The camera's own bearing from PLAN_C is 27.9 degrees, so the road bends by two
# degrees over the last twenty metres, which is what roads do.
CROSSING_DEG = 26.0

# The ditch as the ground agent built it is 13.8 m from lip to lip (D_LIP -
# D_TOE), so section 5's 12.0 m bridge does not reach across it. 14.1 m does,
# in three bays of 4.70, landing 0.4 m inside each lip.
BRIDGE_INNER_R = boundary_radius(math.radians(CROSSING_DEG)) + D_TOE - 1.0
BRIDGE_LEN = 14.2
BRIDGE_OUTER_R = BRIDGE_INNER_R + BRIDGE_LEN
BRIDGE_W = 4.4
BAYS = 3

# Deck level. Section 5 says -1.0, and that number cannot be built: the lens is
# at y = -1.0 too (section 4.1), so a deck at -1.0 is EXACTLY at eye height and
# presents as a zero-height line, and the road cannot climb to it either — the
# ground at the ditch's outer lip is -3.0, and 2 m of embankment on the
# camera's own sight line is 2 m of embankment across the middle of the
# picture.
#
# What DOES decide the level is a visibility test against terrain.json as
# built. Marching the ray from the lens (y = -1.0, standing at r = 88.2 on
# ground about -2.7) toward the ditch on the four bearings 24-30 deg:
#
#     deck at -4.5   hidden behind the ground at r = 74
#     deck at -4.0   hidden behind the outer lip at r = 70
#     deck at -3.5   visible
#     deck at -3.0   visible, clear
#
# The eye is only 1.6 m above ground that runs almost level out to the ditch,
# so anything more than about 2 m down in the ditch is in the shadow of its own
# outer lip. (The same test says the ditch WATER at -6.0 is hidden on every one
# of those bearings, by a few centimetres over a 10 m stretch. Section 6.3
# wanted the knoll to fall back toward the castle at 1:14 to prevent exactly
# that; as built it falls at about 1:49. It is the ground's to fix, not the
# bridge's, and -2.95 is the right deck level either way — a steeper fall-back
# only makes it read better.)
#
# So: LEVEL at -2.95, flush with the outer lip and 1.55 m above the inner one,
# where it stands as a dark line above the ditch mist with its trestles going
# down into the dark. Overall 14.2 x 4.4 x 4.87 against the table's
# 12.0 x 4.4 x 3.6; the length is the ditch's, which is 13.8 m from lip to lip.
DECK_INNER_Y = -2.95
DECK_OUTER_Y = -2.95


def crossing_axis():
    """(origin, outward unit, left unit) for the bridge, in Three ground xz."""
    th = math.radians(CROSSING_DEG)
    u = (math.cos(th), math.sin(th))
    return PLAN_C, u, (-u[1], u[0])


def bridge_station(s):
    """A point on the bridge centreline. s runs 0 (inner) to 1 (outer)."""
    c, u, _ = crossing_axis()
    r = BRIDGE_INNER_R + s * BRIDGE_LEN
    return (c[0] + u[0] * r, c[1] + u[1] * r)


def deck_y(s):
    return DECK_INNER_Y + (DECK_OUTER_Y - DECK_INNER_Y) * s


# ---------------------------------------------------------------- the drove road
#
# (bearing in degrees about PLAN_C, offset OUTWARD from the platform's top edge)
#
# Polar rather than cartesian because everything the road has to respect — the
# toe band it runs along, the batter it climbs, the berm it crosses — is
# defined as a distance out from that edge, so in polar the route is legible
# and in x/z it is sixteen magic numbers.
#
# The bearings run anticlockwise from the crossing round the SOUTH side to the
# gate, which is section 5 group 5's flanking approach: an attacker walks the
# length of the south curtain with his shield arm on the wrong side.
# Offsets are measured OUT from the platform's top edge, so the bands read
# directly: over 10.4 is in the ditch, 7.2 to 10.4 is the level toe, 0 to 7.2
# is the batter, under 0 is the berm.
#
# The batter is crossed between 46 and 70 degrees, which is 20 m of travel for
# 4.5 m of climb — a shelf cut diagonally across the face at about 1:4.4.
# Straight up it would be 1:1.6, and a drove road is not a stair.
INNER_ROUTE = [
    (26.0, 9.60),      # off the bridge onto the ditch's inner lip
    (31.0, 9.20),
    (36.0, 8.60),
    (41.0, 8.00),
    (46.0, 7.20),      # the foot of the batter
    (52.0, 5.60),
    (58.0, 3.80),
    (64.0, 2.00),
    (70.0, 0.20),      # over the berm edge
    (76.0, -2.40),
    (82.0, -5.60),
]
# The last two are cartesian: the road turns north off the berm run and squares
# up to the gate, and a bearing about PLAN_C cannot say that.
INNER_TAIL = [(7.8, 33.6), (6.0, 30.4)]

# Out here the platform edge is irrelevant, so these are plain radii. The road
# runs out past the camera (r = 88.2) because the 24 s intro move in section
# 4.2 starts further back and looks along it.
OUTER_ROUTE = [
    (26.0, None),      # filled in from BRIDGE_OUTER_R
    (26.8, 75.0),
    (27.4, 81.0),
    (27.93, 88.2),     # the knoll crest: the camera stands here
    (28.8, 100.0),
    (29.8, 118.0),
    (30.6, 150.0),     # off the bottom of the frame, into the fog
]

TRACK_W = 4.4


def inner_control():
    return [polar(deg, boundary_radius(math.radians(deg)) + off)
            for (deg, off) in INNER_ROUTE] + INNER_TAIL


def outer_control():
    return [polar(deg, BRIDGE_OUTER_R if r is None else r)
            for (deg, r) in OUTER_ROUTE]


def print_summary():
    t = Terrain()
    c, u, v = crossing_axis()
    print('crossing bearing %.1f deg, inner r %.2f, outer r %.2f'
          % (CROSSING_DEG, BRIDGE_INNER_R, BRIDGE_OUTER_R))
    for s, label in ((0.0, 'inner abutment'), (1 / 3.0, 'trestle 1'),
                     (2 / 3.0, 'trestle 2'), (1.0, 'outer abutment')):
        x, z = bridge_station(s)
        print('  %-16s three (%6.2f, %6.2f)  ground %+6.2f  deck %+6.2f'
              % (label, x, z, t.h(x, z), deck_y(s)))
