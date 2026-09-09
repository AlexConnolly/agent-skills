# Nightfall at the March Castle — asset group 6, the track and field-edge kit.
#
#   blender --background --python build_track.py
#   blender --background --python build_track.py -- wall_mod_a
#
# Brief: demo/build/briefs/track.md, written first and committed verbatim.
# Spec:  demo/ART-DIRECTION.md section 5 group 6, levels from section 6.1.
# (Section 8.8 calls this file build_edges.py. It is build_track.py because the
# track ribbon is the piece the group is actually about.)
#
# THE TRACK RIBBON IS THE POINT OF THIS GROUP
#
# Section 5 group 6 calls it the highest value-per-triangle decision in the
# ground plan, and the reason is a value difference rather than a shape: earth-
# wet at roughness 0.35 against turf-night at 1.0 picks up a long soft sheen
# from a moon that is behind everything else, so the track reads as a ribbon of
# slightly-lighter value leading the eye in from the bottom of the frame. It is
# the leading line of the picture.
#
# It is one sweep along a path that samples terrain.json, in two pieces: the
# outer approach stops at the bridge's outer abutment and the inner run starts
# at its inner one. It does NOT run over the deck, because two coincident
# surfaces are how you ship a flickering seam.
#
# THE WALL IS A KIT AND IS BUILT AS ONE
#
# 2 m pitch, 2.04 m of module so consecutive pieces overlap by 4 cm, the same
# battered cross-section at both ends, and the origin on the pitch centre so a
# 180 degree flip — which section 5 group 6 asks for as the main source of
# variety — leaves the module where it was. Nothing on it is distinctive: it is
# drawn 44 times, and a signature crack seen 44 times is worse than no detail.
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
# art_props/ is a private copy of the blender-model toolkit and is not tracked
# (see .gitignore); route.py, terrain.py and props_common.py are this project's
# own and sit here beside the build scripts, so a clean checkout still builds.
sys.path.append(HERE)
sys.path.append(os.path.join(HERE, 'art_props'))

import artconfig as cfg          # noqa: E402
import lib                       # noqa: E402
import props_common as pc        # noqa: E402
import route                     # noqa: E402
from terrain import Terrain      # noqa: E402


TERRAIN = Terrain()

TURF = pc.TURF_NIGHT
EARTH = pc.EARTH_WET
TIMBER = pc.TIMBER_NIGHT
STONE = 0x2A2B28


def mats():
    return {
        # The name matters: section 8.5's tune-up table dispatches on the
        # prefix, and `track_*` is the entry that sets roughness 0.35.
        'track': lib.hexmat('track_earth', EARTH, rough=0.35),
        'stone': lib.hexmat('wall_stone', STONE, rough=0.92),
        'timber': lib.hexmat('timber_field', TIMBER, rough=0.88),
    }


# ---------------------------------------------------------------- the ribbon

TRACK_W = 4.4
LIFT = 0.060           # the crown sits this far proud of the sampled ground
RUT_T = 1.05           # rut centres, metres either side of the crown
STATION = 2.8          # metres between sweep stations


def road_section(drop_l, drop_r, spread):
    """A 4.4 m cambered earth road with two ruts, closed underneath.

    Eleven points across the running surface and two under it. The two ruts are
    the piece the brief insists on: they are what holds the rut pools, and at
    40 m they read as two dark lines down the middle of a lighter ribbon.

    The two drops are measured PER SIDE from the terrain under each edge, not
    from one nominal thickness. A ribbon of constant depth laid across a slope
    lifts its downhill edge off the ground, and `track_down.png` showed exactly
    that where the road runs along the ditch's inner lip: a pale band hanging
    over the scarp with daylight under it."""
    top = [(-2.20, 0.000), (-1.86, 0.052), (-1.32, 0.044),
           (-RUT_T, -0.058), (-0.78, 0.030), (0.00, 0.078), (0.78, 0.030),
           (RUT_T, -0.058), (1.32, 0.044), (1.86, 0.052), (2.20, 0.000)]
    return top + [(2.20 + spread, -drop_r), (-2.20 - spread, -drop_l)]


def _resample(pts, step):
    """Even stations along a polyline. A catmull gives even PARAMETER, and the
    control points here are 5 m apart at the gate and 30 m apart out in the
    field, so by parameter the far end gets one station every 10 m and the near
    end one every 1.5 m — the opposite of what is wanted."""
    out = [pts[0]]
    carry = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        seg = math.dist(a, b)
        if seg < 1e-6:
            continue
        t = step - carry
        while t < seg:
            f = t / seg
            out.append(tuple(a[k] + (b[k] - a[k]) * f for k in range(len(a))))
            t += step
        carry = (carry + seg) % step
    out.append(pts[-1])
    return out


def _ribbon(name, control, bridge_end, ramp_len, parts, m):
    """One run of road: sweep a changing section along a terrain-sampled path.

    `bridge_end` is 0 for a run that starts at the bridge and -1 for one that
    ends there; over `ramp_len` metres from that end the road lifts from the
    ground to the deck level, which is the only fill anywhere on the track."""
    plan = _resample(lib.catmull(control, 8), STATION)
    # distance along, so the ramp can be measured in metres rather than in
    # station indices
    run = [0.0]
    for i in range(1, len(plan)):
        run.append(run[-1] + math.dist(plan[i - 1], plan[i]))
    total = run[-1]

    path, sections = [], []
    for i, (x, z) in enumerate(plan):
        g = TERRAIN.h(x, z)
        s = run[i] if bridge_end == 0 else total - run[i]
        k = max(0.0, min(1.0, 1.0 - s / ramp_len)) if ramp_len > 0 else 0.0
        k = k * k * (3.0 - 2.0 * k)
        y = g + LIFT + (route.DECK_INNER_Y - (g + LIFT)) * k
        fill = max(0.0, y - g - LIFT)
        # The unit vector across the road, so the ground under each edge can be
        # sampled rather than assumed level.
        j = min(i + 1, len(plan) - 1)
        h = max(i - 1, 0)
        tx, tz = plan[j][0] - plan[h][0], plan[j][1] - plan[h][1]
        n = math.hypot(tx, tz) or 1.0
        ex, ez = -tz / n, tx / n
        spread = fill * 1.15
        gl = TERRAIN.h(x - ex * (2.4 + spread), z - ez * (2.4 + spread))
        gr = TERRAIN.h(x + ex * (2.4 + spread), z + ez * (2.4 + spread))
        path.append(cfg.to_blender(x, y, z))
        sections.append(road_section(max(0.30, y - gl + 0.30),
                                     max(0.30, y - gr + 0.30), spread))
    o = lib.sweep(name, path, sections, close=True, smooth=False)
    o.data.materials.append(m)
    parts.append(o)
    return total


def track_ribbon():
    """4.4 m wide, ~155 m long, ~1 400 tris. Section 5 group 6.

    Two runs: the outer approach from the far east-south-east over the drover's
    knoll to the bridge, and the inner run from the bridge along the ditch's
    inner lip, up the batter and anticlockwise round the south side to the
    gate."""
    m = mats()['track']
    parts = []
    a = _ribbon('track_outer', list(reversed(route.outer_control())), -1, 5.0,
                parts, m)
    b = _ribbon('track_inner', route.inner_control(), 0, 13.0, parts, m)
    print('track_ribbon: outer %.1f m + bridge %.1f m + inner %.1f m = %.1f m'
          % (a, route.BRIDGE_LEN, b, a + b + route.BRIDGE_LEN))
    return lib.merge_into('track_ribbon', parts)


# ---------------------------------------------------------------- the wall kit

PITCH = 2.00
OVERLAP = 0.04
WALL_L = PITCH + OVERLAP


def _coursed(seed, courses, height, end_guard=0.92):
    """A displacement function that reads as laid stone.

    Steps at the course lines with a per-stone offset along the run, so the
    face breaks up into rectangles rather than rippling. Vertices near either
    end are left exactly where they are: the kit only tiles if both end
    sections are identical, and a displacement that moves them opens a slot at
    every joint."""
    def fn(co, nrm):
        if abs(co.x) > end_guard or abs(nrm.z) > 0.7:
            return 0.0
        course = math.floor(co.z / (height / courses) + 0.001)
        stone = math.floor((co.x + course * 0.37) / 0.34)
        n = pc.noise3(stone * 0.7, course * 1.3, seed, 5)
        return 0.035 * n - 0.012
    return fn


def wall_mod_a():
    """2.04 x 0.62 x 1.10, ~220 tris, 44 instances.

    Two battered faces of laid stone with a coping course set on edge. Chest
    high on a 1.75 m figure. Origin on the pitch centre at ground level, so
    placing one is setting x = i * 2.00 and a 180 degree flip leaves it where
    it was."""
    m = mats()['stone']
    parts = []
    # A PRISM, not box(taper=). box() tapers x and y together, so a module
    # battered from 0.62 to 0.43 across also loses 30 % of its LENGTH at the
    # top — and `wall_run.png` showed nine modules whose feet nearly touched
    # and whose tops stood 0.6 m apart, which is the kit failing at the only
    # thing a kit has to do. A prism holds the same section at every station
    # along the run, so the two end faces are identical and the modules mate.
    core = lib.prism('wall_core',
                     [(-0.310, 0.000), (0.310, 0.000),
                      (0.215, 0.920), (-0.215, 0.920)],
                     WALL_L, plane='yz')
    lib.displace(core, _coursed(11, 5, 0.92), cuts=2)
    core.data.materials.append(m)
    parts.append(core)

    rng = pc.Rng(23)

    def cope(i, pos, angle):
        # Set on edge along the top, leaning alternately, which is how a
        # drystone coping is actually built and what gives the top line its
        # saw-tooth against the sky.
        h = rng.uni(0.22, 0.30)
        return lib.box('cope%d' % i, (rng.uni(0.16, 0.24), 0.50, h),
                       loc=(pos[0], rng.uni(-0.03, 0.03), 0.90 + h * 0.42),
                       rot=(rng.uni(-0.22, 0.22), rng.uni(-0.10, 0.10),
                            rng.uni(-0.10, 0.10)))

    stones = lib.array(cope, 8, step=(0.262, 0, 0), start=(-0.918, 0, 0),
                       jitter=(0.02, 0, 0), seed=4)
    for s in stones:
        s.data.materials.append(m)
    parts += stones
    return lib.merge_into('wall_mod_a', parts)


def wall_mod_b():
    """2.04 x 0.62 x 0.55, ~150 tris, 12 instances, used in threes.

    The same wall fallen: the coping gone, the top courses tumbled to an uneven
    line, loose stones lying at the foot. Same footprint and the same mating
    section at both ends, so it drops into a run of wall_mod_a."""
    m = mats()['stone']
    parts = []
    # 0.2625 is not a guess: wall_mod_a batters 0.310 -> 0.215 over 0.92 m, so
    # at 0.46 its half-width is exactly 0.2625. A kit whose two modules disagree
    # about the batter is a kit with a step at every joint between them.
    core = lib.prism('fallen_core',
                     [(-0.310, 0.000), (0.310, 0.000),
                      (0.2625, 0.460), (-0.2625, 0.460)],
                     WALL_L, plane='yz')
    # The crest is broken by stones ADDED on top, not by dropping the vertices
    # of the core. Two attempts at the latter both failed the same way: a
    # subdivided prism only has vertex rings every 0.4-0.5 m, so any guard wide
    # enough to keep the end sections intact leaves the crest ramping down over
    # half a metre from each end — `iso_a.png` showed a wedge of rock rather
    # than a fallen wall, with two end faces that no longer matched
    # wall_mod_a's. Adding geometry keeps both mating faces exact by
    # construction, which is the one thing this module has to get right.
    lib.displace(core, _coursed(31, 3, 0.46), cuts=2)
    core.data.materials.append(m)
    parts.append(core)

    rng = pc.Rng(59)

    def cap(i, pos, angle):
        # What is left of the top courses: four blocks still up, one slipped
        # over the face, and gaps where the rest has gone.
        if i in (2, 5):
            return None
        slip = 0.30 if i == 4 else 0.0
        h = rng.uni(0.13, 0.21)
        return lib.box('capfall%d' % i, (rng.uni(0.20, 0.34), 0.44, h),
                       loc=(pos[0], slip, 0.44 + h * 0.42 - slip * 0.55),
                       rot=(rng.uni(-0.30, 0.30) + slip * 1.1,
                            rng.uni(-0.16, 0.16), angle))

    caps = lib.array(cap, 6, step=(0.318, 0, 0), start=(-0.795, 0, 0),
                     jitter=(0.05, 0, 0), turn=0.22, seed=8)
    for s in caps:
        s.data.materials.append(m)
    parts += caps

    def spill(i, pos, angle):
        s = rng.uni(0.13, 0.24)
        return lib.box('spill%d' % i, (s, s * rng.uni(0.6, 1.0),
                                       s * rng.uni(0.4, 0.8)),
                       loc=(pos[0], pos[1], s * 0.22),
                       rot=(rng.uni(-0.4, 0.4), rng.uni(-0.4, 0.4), angle))

    left = lib.array(spill, 4, step=(0.46, 0.0, 0.0), start=(-0.70, 0.44, 0),
                     jitter=(0.10, 0.16, 0.0), turn=math.pi, seed=6)
    right = lib.array(spill, 3, step=(0.58, 0.0, 0.0), start=(-0.55, -0.46, 0),
                      jitter=(0.10, 0.16, 0.0), turn=math.pi, seed=7)
    for s in left + right:
        s.data.materials.append(m)
    parts += left + right
    return lib.merge_into('wall_mod_b', parts)


# ---------------------------------------------------------------- hurdle

def hurdle():
    """1.80 x 0.10 x 1.05, ~160 tris, 24 instances.

    Hazel: vertical sails with horizontal rods woven in front of one and behind
    the next, and the two outer sails running on below the weave to be driven
    into the ground. The weave is the whole difference between this and a fence
    panel, and it is why the rods are swept paths rather than straight bars."""
    m = mats()['timber']
    parts = []
    sails = [-0.85, -0.42, 0.0, 0.42, 0.85]
    for i, x in enumerate(sails):
        drive = 0.14 if i in (0, 4) else 0.0
        o = lib.box('sail%d' % i, (0.045, 0.045, 1.02 + drive),
                    loc=(x, 0, (1.02 + drive) * 0.5 - drive),
                    rot=(0, pc.Rng(i).uni(-0.02, 0.02), 0))
        o.data.materials.append(m)
        parts.append(o)
    rng = pc.Rng(13)
    for j, z in enumerate((0.12, 0.36, 0.62, 0.90)):
        # in front of one sail, behind the next
        path = []
        for k, x in enumerate((-0.94, -0.85, -0.42, 0.0, 0.42, 0.85, 0.94)):
            side = 0.040 if (k + j) % 2 else -0.040
            path.append((x, side, z + rng.uni(-0.015, 0.015)))
        o = lib.profile('weaver%d' % j,
                        [(-0.026, -0.020), (0.026, -0.020), (0.0, 0.026)],
                        path, close=True, smooth=False)
        o.data.materials.append(m)
        parts.append(o)
    return lib.merge_into('hurdle', parts)


# ---------------------------------------------------------------- field gate

def field_gate():
    """3.20 x 0.14 x 1.30, ~200 tris, 2 instances, one hanging open.

    Five bars, a heavy hanging stile, a lighter head stile and the diagonal
    that runs from the BOTTOM of the hanging stile up to the head — which is
    the way a real gate is braced, and the way you can tell one from a ladder
    at a glance. The origin is on the hinge so scene code can swing it open
    with a yaw."""
    m = mats()['timber']
    parts = []
    L = 3.20

    def add(o):
        o.data.materials.append(m)
        parts.append(o)

    add(lib.box('harr', (0.13, 0.13, 1.30), loc=(0.0, 0, 0.65)))
    add(lib.box('head', (0.10, 0.10, 1.22), loc=(L - 0.05, 0, 0.61)))
    for k, x in enumerate((L * 0.36, L * 0.68)):
        add(lib.box('stile%d' % k, (0.075, 0.075, 1.20), loc=(x, 0, 0.60)))
    rng = pc.Rng(19)
    for k, z in enumerate((0.20, 0.46, 0.72, 0.98, 1.22)):
        h = 0.085 if k == 4 else 0.070
        add(lib.box('bar%d' % k, (L, h, h),
                    loc=(L * 0.5, 0, z + rng.uni(-0.012, 0.012))))
    # the brace, foot of the harr to the head
    span = math.hypot(L - 0.1, 0.96)
    o = lib.box('brace', (span, 0.065, 0.065), loc=(L * 0.5, 0, 0.70),
                rot=(0, -math.atan2(0.96, L - 0.1), 0))
    add(o)
    for k, z in enumerate((0.30, 1.10)):
        add(lib.box('strap%d' % k, (0.34, 0.05, 0.07), loc=(0.14, 0.05, z)))
    return lib.merge_into('field_gate', parts)


# ---------------------------------------------------------------- driver

PIECES = {
    'track_ribbon': (track_ribbon, 1400, 1),
    'wall_mod_a': (wall_mod_a, 220, 44),
    'wall_mod_b': (wall_mod_b, 150, 12),
    'hurdle': (hurdle, 160, 24),
    'field_gate': (field_gate, 200, 2),
}
ORDER = ['track_ribbon', 'wall_mod_a', 'wall_mod_b', 'hurdle', 'field_gate']


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def main():
    want = argv() or ORDER
    report = []
    rows = []
    total = 0
    for name in want:
        build, budget, inst = PIECES[name]
        lib.reset()
        obj = build()
        lib.export(name, report)
        tris = report[-1][1]
        lo, hi = pc.bbox([obj])
        rows.append((name, tris, budget,
                     '%.2f x %.2f x %.2f m' % (hi[0] - lo[0], hi[1] - lo[1],
                                               hi[2] - lo[2]),
                     'x%d' % inst))
        total += tris * inst
    lib.summarise(report)
    pc.budget_table(rows)
    print('group 6 in the scene: %d triangles  (section 5 says ~17 000)'
          % total)
    print()
    print('=== the kit rules, section 5 group 6 / SKILL.md ===')
    print('  pitch          %.2f m' % PITCH)
    print('  module length  %.2f m  (%.0f cm of deliberate overlap)'
          % (WALL_L, OVERLAP * 100))
    print('  origin         pitch centre, on the ground: place at x = i * %.2f,'
          ' flip alternates 180 deg about Z' % PITCH)
    print('  mating face    battered trapezoid, 0.62 m at the foot tapering to '
          '0.43 m, identical at both ends')
    print('  varies by      placement only: 180 deg flip, +/-2 cm, +/-1.5 deg,'
          ' and following the terrain')
    print()
    print('=== where these load, Three.js ===')
    print('  track_ribbon   (0, 0, 0)  — authored in world coordinates')
    print('  wall_mod_a/b, hurdle, field_gate  — instanced, origin on the '
          'ground, seated from terrain.json')
    print('  field_gate origin is the hinge; the open one gets a yaw')


if __name__ == '__main__':
    main()
