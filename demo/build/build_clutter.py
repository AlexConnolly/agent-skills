# Nightfall at the March Castle — asset group 8, outfield clutter and the
# wayside cross.
#
#   blender --background --python build_clutter.py
#   blender --background --python build_clutter.py -- wayside_cross
#
# Brief: demo/build/briefs/clutter.md, written first and committed verbatim.
# Spec:  demo/ART-DIRECTION.md section 5 group 8.
#
# THE WAYSIDE CROSS IS THE ONE PIECE HERE THAT IS READ CLOSE
#
# It stands 21 m from the lens, which at 1920 px across a 54 degree field is 90
# pixels per metre, and it is 2.8 m tall — about a fifth of the frame height,
# with its head crossing the horizon. It is the nearest object in the world and
# therefore the only one that tells a viewer how big the castle behind it is.
# Everything else in this group is read between 25 and 60 m and is silhouette
# and mass.
#
# So the cross is built at a different density from the rest of the file, and
# deliberately: independent fillet radii on the base steps because two hundred
# years of rain rounds a horizontal arris far more than an upright one; a
# revolved octagonal shaft with a real stop-chamfer at the foot; a prismatic
# Latin head with one arm broken short and an iron strap round the neck where
# it was set back on. It is the one asset in this group that should carry a
# baked map — 2.8 m on a 2048 gives 730 px/m — so the geometry here is built to
# be unwrapped, and the lichen and the moss belong to that pass, not this one.
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, 'art_props'))

import artconfig as cfg          # noqa: E402
import lib                       # noqa: E402
import props_common as pc        # noqa: E402


TIMBER = pc.TIMBER_NIGHT
STONE = 0x2E2E29          # weathered limestone, a shade above the rock kit
IRON = 0x14161A
HAY = 0x23241B


def mats():
    return {
        'stone': lib.hexmat('cross_stone', STONE, rough=0.94),
        'iron': lib.hexmat('cross_iron', IRON, rough=0.62, metal=0.55),
        'timber': lib.hexmat('timber_clutter', TIMBER, rough=0.88),
        'hay': lib.hexmat('hay_clutter', HAY, rough=0.98),
    }


def seat(obj):
    """Floor on z=0. Weathering, shear and displacement all move it."""
    lo = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    for v in obj.data.vertices:
        v.co.z -= lo
    return obj


def clip_corner(obj, seed, at_z, depth, span=0.5):
    """Knock a corner off, on a plane, between two heights.

    A worn step is not worn evenly: one corner has gone. Done by clipping
    vertices onto the plane rather than with a boolean, which on stacked
    overlapping solids returns an empty mesh."""
    rng = pc.Rng(seed)
    a = rng.uni(0, math.tau)
    n = (math.cos(a), math.sin(a), rng.uni(-0.35, -0.10))
    L = math.sqrt(sum(c * c for c in n))
    n = tuple(c / L for c in n)
    lo, hi = pc.bbox([obj])
    c = ((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5, at_z)
    proj = [sum((v.co[j] - c[j]) * n[j] for j in range(3))
            for v in obj.data.vertices]
    limit = max(proj) - depth
    for v, p in zip(obj.data.vertices, proj):
        if p > limit and at_z - span <= v.co.z <= at_z + span:
            v.co = tuple(v.co[j] - n[j] * (p - limit) for j in range(3))
    return obj


# ---------------------------------------------------------------- the cross

def wayside_cross():
    """0.9 x 0.9 x 2.8, 1 instance, 21 m from the lens at 18 % across.

    A weathered stone cross on a three-step base, the head broken and repaired,
    the shaft leaning about 4 degrees. Not a ringed cross: no circle joins the
    arms, because a ringed cross is the wrong region and reads as a tourist
    icon."""
    m = mats()
    parts = []

    # --- 1. the three-step calvary base ------------------------------------
    #
    # rounded_box, not box(chamfer=), and that is the whole reason the verb
    # exists: two hundred years of rain and boots round a horizontal arris far
    # more than an upright one, so the top edge of a step is a generous radius
    # and its corners a tight one. One radius on all twelve edges is a large
    # part of what makes a modelled stone read as CG at arm's length, and this
    # thing is read at arm's length by the standards of this scene.
    steps = [(0.92, 0.215, 0.000), (0.715, 0.195, 0.215),
             (0.535, 0.175, 0.410)]
    for i, (w, h, z) in enumerate(steps):
        s = lib.rounded_box('step%d' % i, (w, w * 0.98, h),
                            r_upright=0.018 + 0.006 * i,
                            r_horizontal=0.030 + 0.008 * i,
                            loc=(0, 0, z + h * 0.5), segments=1)
        # Worn hollow: the tread dips where feet and cart wheels have caught it.
        lib.displace(s, lambda co, nrm, zz=z + h: (
            0.0, 0.0,
            -0.016 * (1.0 + pc.noise3(co.x * 2.3, co.y * 2.3, i, 5))
            if co.z > zz - 0.02 else 0.0))
        s.data.materials.append(m['stone'])
        parts.append(s)
    # one corner of the bottom step gone
    clip_corner(parts[0], 5, 0.10, 0.16, span=0.14)

    # --- 2. the socket stone -----------------------------------------------
    #
    # revolve at 8 segments: an octagon is what a socket stone is, and the
    # chamfer from square to octagon is the join between it and the shaft.
    sock = lib.revolve('socket', [(0.248, 0.570), (0.248, 0.745),
                                  (0.184, 0.870), (0.166, 0.935),
                                  (0.166, 0.570)],
                       segments=8, close_outline=True, smooth=False)
    sock.data.materials.append(m['stone'])
    parts.append(sock)
    clip_corner(sock, 9, 0.83, 0.042, span=0.15)

    # --- 3. the shaft: square at the foot, stopped to an octagon ------------
    #
    # A real stop-chamfer, not a taper that looks like one: the foot is a
    # square block and the octagon starts above it, so the transition is a
    # visible event at 90 px/m rather than a smooth turned profile. The first
    # version was one revolve all the way down and `silhouette.png` showed a
    # lamp standard.
    foot = lib.box('shaft_foot', (0.318, 0.318, 0.245), loc=(0, 0, 1.020))
    foot.data.materials.append(m['stone'])
    parts.append(foot)
    shaft = lib.revolve('shaft',
                        [(0.000, 0.940),
                         (0.160, 0.940), (0.147, 1.215),
                         (0.139, 1.720), (0.130, 2.270),
                         (0.000, 2.280)],
                        segments=8, close_outline=False, smooth=False)
    shaft.data.materials.append(m['stone'])
    parts.append(shaft)

    # --- 4. the head: a Latin cross, one arm broken short -------------------
    #
    # prism, because a cross head is a flat shape you draw and then give
    # thickness to, and that is exactly what the verb is for.
    #
    # The arms span 0.72 m against a 0.21 m shaft, which at 90 px/m is 65 px
    # against 19. The first version used +/-0.30 on a 0.19 shaft and the head
    # read as a finial in `silhouette.png` — this whole object exists to be
    # recognised as a CROSS in one glance from 21 m, and a head that has to be
    # explained has failed.
    t = 0.128          # half width of the limb
    arm_z0, arm_z1 = 2.300, 2.566
    outline = [
        (-t, 2.110), (t, 2.110),                      # neck, into the shaft
        (t, arm_z0), (0.452, arm_z0 + 0.014),         # right arm out
        (0.446, arm_z1), (t, arm_z1),
        (t, 2.800), (-t, 2.792),                      # the head above the arms
        (-t, arm_z1),
        (-0.268, arm_z1 - 0.038),                     # LEFT ARM BROKEN SHORT:
        (-0.305, arm_z0 + 0.118),                     # a ragged fracture, not
        (-0.232, arm_z0 + 0.036),                     # a sawn end
        (-t, arm_z0),
    ]
    head = lib.prism('head', outline, 0.228, plane='xz', smooth=False)
    head.data.materials.append(m['stone'])
    parts.append(head)

    # --- 5. the iron strap round the neck ----------------------------------
    #
    # The repair is the story, and it has to read as a repair rather than as a
    # moulding: one band with the two ends lapped and riveted proud on the
    # front, sitting on the joint where the head was set back on the shaft.
    for j, (dx, dy, sx, sy) in enumerate(((0.0, 0.142, 0.304, 0.028),
                                          (0.0, -0.142, 0.304, 0.028),
                                          (0.142, 0.0, 0.028, 0.304),
                                          (-0.142, 0.0, 0.028, 0.304))):
        band = lib.box('strap%d' % j, (sx, sy, 0.082), loc=(dx, dy, 2.160))
        band.data.materials.append(m['iron'])
        parts.append(band)
    for j, (dx, dy, sx, sy) in enumerate(((0.0, 0.160, 0.118, 0.048),
                                          (0.160, 0.0, 0.048, 0.118))):
        lug = lib.box('strap_lug%d' % j, (sx, sy, 0.160), loc=(dx, dy, 2.160))
        lug.data.materials.append(m['iron'])
        parts.append(lug)

    obj = lib.merge_into('wayside_cross', parts)

    # --- 6. the lean, and the weather --------------------------------------
    #
    # About 4 degrees, from the top of the bottom step up, so the base stays
    # bedded in the ground and only the stones above it have moved. Sheared
    # rather than rotated, so the steps stay level and only the stack leans —
    # which is what actually happens when the ground under one side settles.
    tan = math.tan(math.radians(4.2))
    for v in obj.data.vertices:
        if v.co.z > 0.20:
            k = (v.co.z - 0.20)
            v.co.x += k * tan
            v.co.y += k * tan * 0.30
    # Rubbed arrises and a general unevenness. Small: 8 mm at 90 px/m is under
    # a pixel of silhouette, which is the right size for weathering that must
    # not turn the shaft into a sausage.
    lib.displace(obj, lambda co, nrm: (
        0.008 * pc.fbm3(co.x * 3.1, co.y * 3.1, co.z * 2.2, 3, 2),
        0.008 * pc.fbm3(co.x * 3.1 + 7, co.y * 3.1, co.z * 2.2, 4, 2),
        0.006 * pc.fbm3(co.x * 3.1, co.y * 3.1 + 7, co.z * 2.2, 5, 2)))
    return seat(obj)


# ---------------------------------------------------------------- the cart

def carriers_cart():
    """3.4 x 1.7 x 1.5, ~620 tris, 2 instances.

    A two-wheeled carrier's cart with shafts. The wheels must read as wheels in
    silhouette, which means the spokes have to be visible THROUGH the rim, so
    the rim is lib.ring — a real annulus with a real hole — and not a
    cylinder."""
    m = mats()
    parts = []
    R = 0.62

    def add(o, mat='timber'):
        o.data.materials.append(m[mat])
        parts.append(o)

    for side in (-1, 1):
        y = 0.66 * side
        rim = lib.ring('rim%d' % side, R - 0.075, R, 0.10,
                       loc=(0.0, y, R), rot=(math.pi / 2, 0, 0), segments=11)
        add(rim)
        add(lib.cyl('hub%d' % side, 0.10, 0.09, 0.20, loc=(0, y, R),
                    rot=(math.pi / 2, 0, 0), segments=7))

        def spoke(i, pos, angle):
            a = i / 6.0 * math.tau + 0.2 * side
            return lib.box('spoke%d_%d' % (side, i), (0.052, 0.052, R - 0.10),
                           loc=(math.cos(a) * (R - 0.05) * 0.5, y,
                                R + math.sin(a) * (R - 0.05) * 0.5),
                           rot=(0, -a + math.pi / 2, 0))

        for s in lib.array(spoke, 6, step=(0, 0, 0), seed=side + 3):
            add(s)

    add(lib.box('axle', (0.11, 1.50, 0.11), loc=(0, 0, R)))

    # body: a plank floor, two sides, a head and a tail, all sitting over the
    # axle the way a two-wheeled cart balances
    add(lib.box('floor', (2.30, 1.18, 0.075), loc=(0.10, 0, R + 0.20)))
    for side in (-1, 1):
        add(lib.box('side%d' % side, (2.30, 0.065, 0.42),
                    loc=(0.10, 0.575 * side, R + 0.44)))
    add(lib.box('head', (0.07, 1.18, 0.50), loc=(-1.02, 0, R + 0.48)))
    add(lib.box('tail', (0.07, 1.18, 0.38), loc=(1.22, 0, R + 0.42)))
    rng = pc.Rng(29)
    for k in range(4):
        x = -0.85 + k * 0.63
        for side in (-1, 1):
            add(lib.box('stake%d_%d' % (k, side), (0.06, 0.06, 0.52),
                        loc=(x, 0.575 * side, R + 0.50),
                        rot=(rng.uni(-0.04, 0.04), 0, 0)))
    # shafts, running forward from under the floor
    for side in (-1, 1):
        add(lib.box('shaft%d' % side, (1.55, 0.075, 0.075),
                    loc=(-1.75, 0.46 * side, R + 0.11),
                    rot=(0, 0.045, 0)))
    return lib.merge_into('carriers_cart', parts)


# ---------------------------------------------------------------- woodstack

def woodstack():
    """2.6 x 1.2 x 1.5, ~500 tris, 3 instances.

    Cordwood in courses with the end grain showing, and an untidy top course.
    A neat cube of firewood is the failure mode named in the brief; the top row
    is short, gapped and out of line, which is what stops it."""
    m = mats()['timber']
    parts = []
    rng = pc.Rng(37)
    courses = [(0.12, 6), (0.36, 6), (0.60, 6), (0.84, 5), (1.06, 3)]
    for ci, (z, n) in enumerate(courses):
        for i in range(n):
            y = -0.52 + i * (1.04 / max(1, n - 1)) if n > 1 else 0.0
            r = rng.uni(0.095, 0.135)
            L = 2.42 * rng.uni(0.92, 1.0) if ci < 4 else 2.42 * rng.uni(0.5, 0.9)
            o = lib.cyl('log%d_%d' % (ci, i), r, r * rng.uni(0.85, 1.0), L,
                        loc=(rng.uni(-0.09, 0.09), y + rng.uni(-0.03, 0.03),
                             z + rng.uni(-0.02, 0.02)),
                        rot=(0, math.pi / 2, rng.uni(-0.035, 0.035)),
                        segments=6)
            o.data.materials.append(m)
            parts.append(o)
    # two driven stakes holding the ends of the stack in
    for side in (-1, 1):
        o = lib.box('stack_stake%d' % side, (0.09, 0.09, 1.35),
                    loc=(1.22 * side, 0.0, 0.62),
                    rot=(0, 0.05 * side, 0))
        o.data.materials.append(m)
        parts.append(o)
    return seat(lib.merge_into('woodstack', parts))


# ---------------------------------------------------------------- tether post

def tether_post():
    """0.18 x 0.18 x 1.4, ~60 tris, 6 instances.

    A SPLIT oak post, not a sawn one: an irregular four-sided section, a
    weathered top that has gone to a ragged wedge, and an iron staple. Waist
    high on a figure."""
    m = mats()
    o = lib.prism('post', [(-0.085, -0.078), (0.090, -0.070),
                           (0.078, 0.086), (-0.080, 0.074)],
                  1.34, loc=(0, 0, 0.67), rot=(0.025, 0.05, 0.0),
                  plane='xy')
    o.data.materials.append(m['timber'])
    parts = [o]
    # the split top: a wedge off the head, the way a driven post frays
    top = lib.wedge('post_top', (0.17, 0.16, 0.16), loc=(0, 0.01, 1.36),
                    pinch=0.30)
    top.data.materials.append(m['timber'])
    parts.append(top)
    for k, (dy, w) in enumerate(((0.085, 0.020), (-0.085, 0.020))):
        s = lib.box('staple%d' % k, (0.16, w, 0.022), loc=(0, dy, 1.02))
        s.data.materials.append(m['iron'])
        parts.append(s)
    return seat(lib.merge_into('tether_post', parts))


# ---------------------------------------------------------------- hay heap

def hay_heap():
    """3.2 x 3.2 x 2.2, ~280 tris, 3 instances.

    A rick standing clear of the wet ground on staddle timbers, slumped rather
    than conical, with a rope over it. The air under it is the whole point: a
    cone sitting on the ground is a party hat."""
    m = mats()
    parts = []
    # staddles
    for sx in (-1, 1):
        for sy in (-1, 1):
            o = lib.box('staddle%d%d' % (sx, sy), (0.16, 0.16, 0.46),
                        loc=(0.95 * sx, 0.95 * sy, 0.23))
            o.data.materials.append(m['timber'])
            parts.append(o)
    for sy in (-1, 1):
        o = lib.box('bearer%d' % sy, (2.30, 0.14, 0.13),
                    loc=(0, 0.95 * sy, 0.52))
        o.data.materials.append(m['timber'])
        parts.append(o)
    deck = lib.box('rick_deck', (2.30, 2.20, 0.09), loc=(0, 0, 0.63))
    deck.data.materials.append(m['timber'])
    parts.append(deck)

    rick = lib.revolve('rick', [(0.00, 0.660), (1.52, 0.680), (1.60, 1.150),
                                (1.34, 1.560), (0.72, 1.960),
                                (0.00, 2.070)],
                       segments=10, close_outline=False, smooth=False)
    # Slump it: a rick settles unevenly and leans off the wind. Without this it
    # is a lathe-turned cone and reads as one.
    lib.displace(rick, lambda co, nrm: (
        0.16 * pc.fbm3(co.x * 0.9, co.y * 0.9, co.z * 0.7, 21, 2)
        + 0.06 * (co.z - 0.66),
        0.16 * pc.fbm3(co.x * 0.9 + 5, co.y * 0.9, co.z * 0.7, 22, 2),
        0.10 * pc.fbm3(co.x * 0.9, co.y * 0.9 + 5, co.z * 0.7, 23, 2)))
    rick.data.materials.append(m['hay'])
    parts.append(rick)

    rope = lib.profile('rope', lib.rect_section(0.035, 0.035),
                       [(-1.62, 0.05, 0.74), (-1.30, 0.03, 1.30),
                        (-0.55, 0.0, 1.90), (0.30, -0.02, 1.94),
                        (1.10, -0.02, 1.44), (1.55, 0.0, 0.80)],
                       close=True, smooth=False)
    rope.data.materials.append(m['timber'])
    parts.append(rope)
    return seat(lib.merge_into('hay_heap', parts))


# ---------------------------------------------------------------- driver

PIECES = {
    'wayside_cross': (wayside_cross, 360, 1),
    'carriers_cart': (carriers_cart, 620, 2),
    'woodstack': (woodstack, 500, 3),
    'tether_post': (tether_post, 60, 6),
    'hay_heap': (hay_heap, 280, 3),
}
ORDER = ['wayside_cross', 'carriers_cart', 'woodstack', 'tether_post',
         'hay_heap']


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
    print('group 8 in the scene: %d triangles  (section 5 says ~3 900)'
          % total)
    print()
    from props_common import hero_frame, px_per_metre
    d, f = hero_frame(57.8, 37.2)
    print('wayside_cross at three (57.8, ground, 37.2): %.1f m from the lens, '
          '%.1f %% across, %.0f px/m at 1920 wide' % (d, f, px_per_metre(d)))
    print('  2.8 m tall at %.0f px/m is %.0f px, which on a 1080-line frame is '
          '%.0f %% of the frame height' % (px_per_metre(d),
                                           2.8 * px_per_metre(d),
                                           2.8 * px_per_metre(d) / 1080 * 100))


if __name__ == '__main__':
    main()
