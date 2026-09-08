# Group 1 -- the tree and scrub kit.
#
#   blender --background --python build_trees.py -- [name ...]
#
# Built from demo/build/briefs/trees.md, which was written first.
#
# THE ONE DECISION EVERYTHING ELSE FOLLOWS FROM: the trees are bare. It is the
# last week of October. A bare tree is a branch structure, a branch structure is
# a tapered section swept along a path, and that is `lib.profile` with `scales`
# -- hard-surface parametric work, which is what this toolkit is best at. A
# summer tree is a foliage mass, which is what it is worst at. Only the yew and
# the pine carry mass, and that mass is a handful of chunky faceted lumps.
#
# Everything is seeded, so a rebuild is byte-identical. The irregularity is
# spread evenly round the trunk on purpose: each piece is instanced 8-70 times
# from one mesh, and anything distinctive -- a memorable branch, a signature
# kink -- reads as a repeat, which is worse than no detail at all.
#
# TREE_LOOK=1 in the environment swaps the near-black timber for a mid grey.
# The shipped material is #100D0A, which renders as a flat black shape under the
# contact sheet's sun and tells you nothing about how limbs join; the grey is
# for looking at joins during a build pass and never reaches docs/models. It
# changes no geometry. Run without it for anything that ships.
import os
import sys
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
# art_trees/ first: it holds only artconfig.py, this group's own viewing
# distances. Everything else comes from the shared toolkit in art/.
sys.path.insert(0, os.path.join(HERE, 'art_trees'))
sys.path.insert(1, os.path.join(HERE, 'art'))

import bpy                                          # noqa: E402
import mathutils                                    # noqa: E402
import artconfig as cfg                             # noqa: E402
import lib                                          # noqa: E402


TAU = math.tau
LOOK = os.environ.get('TREE_LOOK') == '1'

# ART-DIRECTION.md section 2. timber-night for everything bare; the yew and the
# pine crown a shade cooler and darker so the evergreen mass separates tonally
# from the branch structure in front of it.
TIMBER = 0x100D0A
EVERGREEN = 0x0C1310

# Wind has come out of the south-west for two hundred years. In Blender that is
# -X -Y, so everything that leans, leans toward +X +Y.
WIND_BEARING = math.radians(45.0)


def palette():
    if LOOK:
        return (lib.hexmat('timber_night', 0x9C907E, rough=0.9),
                lib.hexmat('timber_evergreen', 0x55705C, rough=0.88))
    return (lib.hexmat('timber_night', TIMBER, rough=0.9),
            lib.hexmat('timber_evergreen', EVERGREEN, rough=0.88))


# ---------------------------------------------------------------- path helpers

def sph(az, el):
    """A unit vector from a compass bearing and an elevation, both radians."""
    return mathutils.Vector((math.cos(el) * math.cos(az),
                             math.cos(el) * math.sin(az),
                             math.sin(el)))


def resample(path, count):
    """Re-space a dense spline onto `count` points of equal arc length.

    `lib.catmull` gives as many points as (control points - 1) * n, which is
    never the number of rings a branch's triangle budget allows. Resampling
    decouples the smoothness of the curve from the cost of the sweep, and it
    puts the rings at even intervals so the taper below reads as a taper rather
    than as a step."""
    pts = [mathutils.Vector(p) for p in path]
    segs = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(segs) or 1e-9
    out = [tuple(pts[0])]
    for k in range(1, count - 1):
        want = total * k / (count - 1)
        run = 0.0
        for i, s in enumerate(segs):
            if run + s >= want:
                out.append(tuple(pts[i].lerp(pts[i + 1], (want - run) / max(s, 1e-9))))
                break
            run += s
        else:
            out.append(tuple(pts[-1]))
    out.append(tuple(pts[-1]))
    return out


def taper_radii(r0, r1, n, power=1.25):
    """A branch's radius at each station.

    Constant radius is the single thing that makes a swept tube read as a pipe
    cleaner rather than as wood, so nothing here is swept without one of
    these."""
    return [r1 + (r0 - r1) * (1.0 - i / float(n - 1)) ** power for i in range(n)]


def circle(r, seg):
    return lib.circle_section(r, seg)


def lobed(r, seg, lobes=5, depth=0.16, phase=0.0):
    """A circle pulled in and out: a fluted bole, a buttressed root collar."""
    out = []
    for i in range(seg):
        a = i / float(seg) * TAU
        k = r * (1.0 + depth * math.cos(lobes * a + phase))
        out.append((math.cos(a) * k, math.sin(a) * k))
    return out


def stem(name, path, radii, seg, section=None, smooth=False):
    """Sweep a tapering section along a path. The whole kit is made of these."""
    r0 = radii[0]
    sect = section(r0, seg) if section else circle(r0, seg)
    scales = [r / r0 for r in radii]
    return lib.profile(name, sect, path, close=True, scales=scales, smooth=smooth)


def limb(name, p0, az, el, length, r0, r1, seg, stations, rng,
         lift_in=0.0, lift_out=0.0, bow=0.36, wob=0.0, power=1.25, drift=0.0):
    """One branch, and the path it took.

    `az`/`el` aim the chord from base to tip. `lift_in` and `lift_out` are how
    much steeper the branch leaves its parent and how much flatter it ends,
    which is what puts the arch in an oak limb and the upturn in an ash twig --
    a straight rod between two points is the other half of the pipe-cleaner
    problem. `wob` throws the two interior control points off the plane so no
    branch is a flat arc."""
    p0 = mathutils.Vector(p0)
    chord = sph(az, el)
    p1 = p0 + chord * length
    d0 = sph(az + rng.uniform(-drift, drift), el + lift_in)
    d1 = sph(az + rng.uniform(-drift, drift), el + lift_out)
    c1 = p0 + d0 * (length * bow)
    c2 = p1 - d1 * (length * bow)
    if wob:
        side = chord.cross(mathutils.Vector((0.0, 0.0, 1.0)))
        if side.length < 1e-6:
            side = mathutils.Vector((0.0, 1.0, 0.0))
        side.normalize()
        up = side.cross(chord).normalized()
        for c in (c1, c2):
            c += side * rng.uniform(-wob, wob) * length
            c += up * rng.uniform(-wob, wob) * length
    dense = lib.catmull([tuple(p0), tuple(c1), tuple(c2), tuple(p1)], n=12)
    path = resample(dense, stations)
    obj = stem(name, path, taper_radii(r0, r1, stations, power), seg)
    return obj, path


def along(path, f):
    """A point a fraction of the way along a path, by arc length."""
    return mathutils.Vector(resample(path, 33)[max(0, min(32, int(round(f * 32))))])


# ---------------------------------------------------------------- surface relief

def noise3(x, y, z):
    """Three octaves of deterministic pseudo-noise, roughly -1..1.

    Coordinate-derived so a rebuild is identical, and low enough in frequency
    that it makes lobes rather than fuzz -- at 7 px/m fuzz is invisible and
    lobes are the whole silhouette."""
    return (math.sin(x * 3.1 + y * 1.7 + z * 2.3) * 0.52
            + math.sin(x * 7.3 - y * 5.1 + z * 4.7) * 0.30
            + math.sin(x * 13.7 + y * 11.3 - z * 9.1) * 0.18)


def lump(name, at, radii, relief=0.26, freq=2.1, seed=0.0, subdiv=1):
    """A chunky faceted mass: an evergreen crown lobe, a gorse hummock.

    An icosphere squashed and pushed about by `noise3`, so what comes out is an
    irregular lobe rather than a ball. The squash and the relief are baked into
    the vertices instead of going on the object scale, so the noise keeps the
    same wavelength in every axis and a flattened plate does not end up with
    stretched lobes."""
    obj = lib.sphere(name, 1.0, loc=at, subdiv=subdiv, smooth=False)
    rx, ry, rz = radii

    def fn(co, _n):
        k = 1.0 + relief * noise3(co.x * freq + seed,
                                  co.y * freq + seed * 1.7,
                                  co.z * freq + seed * 2.9)
        return (co.x * rx * k - co.x, co.y * ry * k - co.y, co.z * rz * k - co.z)

    lib.displace(obj, fn)
    return obj


# ---------------------------------------------------------------- measurement

def world_bounds(objs):
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for o in objs:
        if o.type != 'MESH':
            continue
        m = o.matrix_world
        for v in o.data.vertices:
            w = m @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def tris(objs):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
               for o in objs if o.type == 'MESH')


def fit_height(obj, target):
    """Scale the finished piece uniformly to the height in the asset table.

    Uniform, and about an origin already on the ground, so proportion and
    ground contact both survive it -- this sets the tree's age, not its shape.
    Everything above is authored at roughly the right size so this is a
    correction of a few per cent, and the printed factor is the check on
    that."""
    lo, hi = world_bounds([obj])
    h = hi[2] - lo[2]
    k = target / h if h > 1e-6 else 1.0
    obj.scale = (k, k, k)
    bpy.context.view_layer.update()
    return k


def sit_on_ground(obj):
    """Drop or lift the piece so its lowest vertex is exactly z = 0."""
    lo, _hi = world_bounds([obj])
    obj.location = (obj.location[0], obj.location[1], obj.location[2] - lo[2])
    bpy.context.view_layer.update()
    return obj


def bend_mesh(obj, bearing, amount, z0, z1):
    """A permanent set away from the prevailing wind.

    This is `Form.bend()` -- the same quadratic-with-height push -- but a tree
    here is fifty separate swept objects rather than one grown form, so there is
    no Form to call it on. Applying it to the merged mesh at the end instead is
    the same curve and keeps every branch attached: bending the paths as they
    were authored would move a parent without moving the children already
    hanging off it."""
    dx, dy = math.cos(bearing) * amount, math.sin(bearing) * amount
    co = [0.0] * (3 * len(obj.data.vertices))
    obj.data.vertices.foreach_get('co', co)
    for i in range(0, len(co), 3):
        t = max(0.0, min(1.0, (co[i + 2] - z0) / max(1e-6, z1 - z0)))
        co[i] += dx * t * t
        co[i + 1] += dy * t * t
    obj.data.vertices.foreach_set('co', co)
    obj.data.update()
    return obj


# ================================================================ the pieces

def tree_oak_bare(timber, _evergreen):
    """11 m tall, 9 m spread. A hedgerow oak: a short thick bole, a low fork,
    heavy sinuous limbs spread through the whole circle.

    Two kinds of primary limb, which is what stops it being a lollipop -- two
    risers that carry the height and three spreaders that arch out and flatten.
    Five identical limbs at one angle is a parasol."""
    rng = random.Random(1041)
    parts = []

    fork = 3.35
    trunk_pts = [(0.0, 0.0, 0.0), (0.06, -0.05, 0.30), (0.10, -0.02, 0.85),
                 (0.05, 0.09, 1.70), (-0.04, 0.11, 2.45),
                 (-0.09, 0.05, 2.95), (-0.11, 0.02, fork)]
    trunk_r = [0.455, 0.320, 0.296, 0.276, 0.256, 0.240, 0.226]
    parts.append(stem('oak_bole', trunk_pts, trunk_r, 8))

    def trunk_at(z):
        for i in range(len(trunk_pts) - 1):
            a, b = trunk_pts[i], trunk_pts[i + 1]
            if a[2] <= z <= b[2]:
                t = (z - a[2]) / max(1e-6, b[2] - a[2])
                return mathutils.Vector((a[0] + (b[0] - a[0]) * t,
                                         a[1] + (b[1] - a[1]) * t, z))
        return mathutils.Vector(trunk_pts[-1])

    # Two risers and three spreaders, interleaved round the circle so no
    # heading gets both risers and no heading gets none.
    kinds = ['rise', 'spread', 'rise', 'spread', 'spread']
    n = 0
    for i, kind in enumerate(kinds):
        az = i * TAU / 5.0 + rng.uniform(-0.36, 0.36)
        z0 = 2.62 + 0.17 * i + rng.uniform(-0.10, 0.10)
        p0 = trunk_at(min(z0, fork))
        if kind == 'rise':
            el = math.radians(rng.uniform(56, 64))
            length = rng.uniform(4.5, 5.1)
            lift_in, lift_out = math.radians(10), math.radians(-16)
            r0, r1 = 0.185, 0.085
        else:
            el = math.radians(rng.uniform(17, 27))
            length = rng.uniform(3.0, 3.5)
            lift_in, lift_out = math.radians(30), math.radians(-20)
            r0, r1 = 0.200, 0.090
        prim, path = limb('oak_p%d' % i, p0, az, el, length, r0, r1, 5, 5, rng,
                          lift_in=lift_in, lift_out=lift_out, bow=0.40,
                          wob=0.075, power=1.15, drift=0.22)
        parts.append(prim)

        # Three secondaries per primary: two off the shaft, one carrying on
        # from the tip so the limb keeps dividing instead of stopping dead.
        for j, (f, fan) in enumerate(((0.52, -1.0), (0.78, 1.0), (1.0, 0.0))):
            s0 = along(path, f)
            s_az = az + fan * rng.uniform(0.42, 0.78) + rng.uniform(-0.14, 0.14)
            s_el = el + math.radians(rng.uniform(-14, 26) if kind == 'spread'
                                     else rng.uniform(-24, 10))
            s_len = rng.uniform(1.75, 2.45) * (1.0 if f < 1.0 else 1.15)
            sec, spath = limb('oak_s%d_%d' % (i, j), s0, s_az, s_el, s_len,
                              0.085, 0.038, 4, 4, rng,
                              lift_in=math.radians(20), lift_out=math.radians(-14),
                              bow=0.38, wob=0.10, power=1.1, drift=0.3)
            parts.append(sec)

            # Twigs. These are what the silhouette is actually made of: the
            # outline of a bare oak is thirty fine tips, not five heavy limbs.
            for k, (tf, tfan) in enumerate(((0.60, -1.0), (1.0, 0.55))):
                if n >= 27:
                    break
                t0 = along(spath, tf)
                t_az = s_az + tfan * rng.uniform(0.45, 0.95)
                t_el = s_el + math.radians(rng.uniform(-26, 30))
                tw, _ = limb('oak_t%d_%d_%d' % (i, j, k), t0, t_az, t_el,
                             rng.uniform(0.95, 1.5), 0.038, 0.016, 3, 3, rng,
                             lift_in=math.radians(16), lift_out=math.radians(-10),
                             bow=0.34, wob=0.13, power=1.0, drift=0.35)
                parts.append(tw)
                n += 1

    obj = lib.merge_into('tree_oak_bare', parts, mat=timber)
    return obj, 11.0


def tree_ash_bare(timber, _evergreen):
    """14 m tall, 7 m spread. A straight bole carried to 6 m, four heavy
    ascending limbs, and the ash's own signature -- opposite pairs, and twigs
    that turn up at the ends."""
    rng = random.Random(2207)
    parts = []

    fork = 6.15
    trunk_pts = [(0.0, 0.0, 0.0), (0.05, 0.04, 0.34), (0.09, 0.02, 1.15),
                 (0.06, -0.06, 2.35), (-0.01, -0.08, 3.55),
                 (-0.06, -0.03, 4.65), (-0.07, 0.03, 5.45), (-0.05, 0.06, fork)]
    trunk_r = [0.430, 0.312, 0.288, 0.264, 0.240, 0.218, 0.200, 0.185]
    parts.append(stem('ash_bole', trunk_pts, trunk_r, 8))

    top = mathutils.Vector(trunk_pts[-1])
    # One of the four is the leader carrying straight on up. An ash does not
    # fork into equals; it keeps a dominant stem.
    spec = [(math.radians(78), 5.6, 0.170),
            (math.radians(58), 4.9, 0.150),
            (math.radians(54), 4.6, 0.145),
            (math.radians(62), 4.4, 0.140)]
    for i, (el, length, r0) in enumerate(spec):
        az = i * TAU / 4.0 + rng.uniform(-0.30, 0.30)
        p0 = top - mathutils.Vector((0, 0, rng.uniform(0.0, 0.55)))
        prim, path = limb('ash_p%d' % i, p0, az, el, length, r0, 0.070, 6, 6, rng,
                          lift_in=math.radians(-6), lift_out=math.radians(12),
                          bow=0.38, wob=0.055, power=1.2, drift=0.18)
        parts.append(prim)

        # Opposite pairs, at two stations up the limb.
        for j, f in enumerate((0.46, 0.74)):
            s0 = along(path, f)
            for s, side in enumerate((-1.0, 1.0)):
                s_az = az + side * rng.uniform(0.55, 0.85)
                s_el = el + math.radians(rng.uniform(-22, -6))
                sec, spath = limb('ash_s%d_%d_%d' % (i, j, s), s0, s_az, s_el,
                                  rng.uniform(1.5, 2.1), 0.068, 0.030, 4, 5, rng,
                                  lift_in=math.radians(-4), lift_out=math.radians(20),
                                  bow=0.36, wob=0.09, power=1.1, drift=0.25)
                parts.append(sec)
                for k, tf in enumerate((0.58, 1.0)):
                    t0 = along(spath, tf)
                    t_az = s_az + rng.uniform(-0.9, 0.9)
                    t_el = s_el + math.radians(rng.uniform(-8, 28))
                    tw, _ = limb('ash_t%d_%d_%d_%d' % (i, j, s, k), t0, t_az, t_el,
                                 rng.uniform(0.8, 1.25), 0.030, 0.013, 3, 4, rng,
                                 lift_in=math.radians(-10),
                                 lift_out=math.radians(34),
                                 bow=0.34, wob=0.10, power=1.0, drift=0.3)
                    parts.append(tw)

        # A tip continuation, so the four limbs do not all stop at one radius.
        e0 = along(path, 1.0)
        end, _ = limb('ash_e%d' % i, e0, az + rng.uniform(-0.4, 0.4),
                      el + math.radians(rng.uniform(-6, 12)),
                      rng.uniform(1.3, 1.8), 0.068, 0.026, 4, 4, rng,
                      lift_in=0.0, lift_out=math.radians(22), bow=0.35,
                      wob=0.08, power=1.1, drift=0.2)
        parts.append(end)

    obj = lib.merge_into('tree_ash_bare', parts, mat=timber)
    return obj, 14.0


def tree_hawthorn(timber, _evergreen):
    """4.5 m tall, 4.8 m spread. Grazed, wind-shorn and crooked: a zigzag bole,
    a browse line at 0.9 m, a dense low twiggy crown and a permanent lean to the
    north-east away from the south-westerly."""
    rng = random.Random(3313)
    parts = []
    LEAN, Z0, Z1 = 0.95, 0.45, 4.4

    bole = [(0.0, 0.0, 0.0), (0.10, 0.07, 0.28), (0.05, -0.09, 0.62),
            (0.16, 0.04, 1.00), (0.10, 0.10, 1.32)]
    parts.append(stem('haw_bole', bole, [0.235, 0.180, 0.164, 0.152, 0.142], 6))

    top = mathutils.Vector(bole[-1])
    for i in range(6):
        az = i * TAU / 6.0 + rng.uniform(-0.34, 0.34)
        el = math.radians(rng.uniform(30, 62))
        p0 = top - mathutils.Vector((0, 0, rng.uniform(0.0, 0.34)))
        prim, path = limb('haw_p%d' % i, p0, az, el, rng.uniform(1.9, 2.6),
                          0.115, 0.052, 4, 5, rng,
                          lift_in=math.radians(26), lift_out=math.radians(-30),
                          bow=0.42, wob=0.16, power=1.1, drift=0.4)
        parts.append(prim)

        for j, f in enumerate((0.55, 1.0)):
            s0 = along(path, f)
            s_az = az + (-1.0 if j == 0 else 1.0) * rng.uniform(0.5, 1.0)
            s_el = el + math.radians(rng.uniform(-34, 16))
            sec, spath = limb('haw_s%d_%d' % (i, j), s0, s_az, s_el,
                              rng.uniform(0.95, 1.4), 0.050, 0.024, 3, 4, rng,
                              lift_in=math.radians(22), lift_out=math.radians(-26),
                              bow=0.40, wob=0.20, power=1.05, drift=0.5)
            parts.append(sec)
            for k in range(2 if i < 5 else 1):
                t0 = along(spath, 0.55 + 0.45 * k)
                tw, _ = limb('haw_t%d_%d_%d' % (i, j, k), t0,
                             s_az + rng.uniform(-1.1, 1.1),
                             s_el + math.radians(rng.uniform(-30, 34)),
                             rng.uniform(0.5, 0.85), 0.024, 0.010, 3, 3, rng,
                             lift_in=math.radians(18), lift_out=math.radians(-20),
                             bow=0.36, wob=0.24, power=1.0, drift=0.55)
                parts.append(tw)

    obj = lib.merge_into('tree_hawthorn', parts, mat=timber)
    bend_mesh(obj, WIND_BEARING, LEAN, Z0, Z1)
    return obj, 4.5


def tree_yew(timber, evergreen):
    """7 m tall, 6 m spread. A short fat fluted bole under 2 m, three stems
    reaching up into five overlapping evergreen lobes.

    The stems are the whole defence against a lollipop: without them this is a
    shape on a stick, and with them the mass is visibly carried."""
    rng = random.Random(4759)
    bare, mass = [], []

    bole = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.30), (0.0, 0.0, 0.85), (0.0, 0.0, 1.55)]
    bare.append(stem('yew_bole', bole, [0.62, 0.50, 0.455, 0.42], 10,
                     section=lambda r, s: lobed(r, s, lobes=5, depth=0.17)))

    stems = []
    for i in range(4):
        az = i * TAU / 4.0 + rng.uniform(-0.4, 0.4)
        el = math.radians(rng.uniform(66, 80))
        s, path = limb('yew_m%d' % i, (0.0, 0.0, 1.42), az, el,
                       rng.uniform(2.5, 3.6), 0.185, 0.075, 5, 4, rng,
                       lift_in=math.radians(8), lift_out=math.radians(-10),
                       bow=0.34, wob=0.09, power=1.15, drift=0.25)
        bare.append(s)
        stems.append(path)

    # Lobes hung off the tops of the stems and drooping outward, not centred on
    # the axis -- a yew is lopsided and its skirt hangs.
    lobes = ((0.0, 0.0, 5.15, 2.05, 2.00, 1.65),
             (1.55, 0.75, 3.75, 1.80, 1.75, 1.30),
             (-1.35, 1.30, 4.15, 1.65, 1.60, 1.25),
             (0.35, -1.70, 3.45, 1.75, 1.70, 1.20),
             (-1.05, -0.95, 5.55, 1.40, 1.35, 1.10))
    for i, (x, y, z, rx, ry, rz) in enumerate(lobes):
        mass.append(lump('yew_lobe%d' % i, (x, y, z), (rx, ry, rz),
                         relief=0.30, freq=2.3, seed=7.1 * i + 0.6))

    for o in bare:
        lib.attach(o, None, timber)
    for o in mass:
        lib.attach(o, None, evergreen)
    obj = lib.merge_into('tree_yew', bare + mass)
    return obj, 7.0


def tree_pine(timber, evergreen):
    """16 m tall, 6 m spread. A Scots pine on a ridge at 240-300 m: a long bare
    trunk with dead stubs on it, then flat plate-like crown masses tiered up the
    top third. At 7 px/m the only thing that reads is that profile, so the bare
    length below 10 m is the asset."""
    rng = random.Random(5171)
    bare, mass = [], []

    trunk_pts = [(0.0, 0.0, 0.0), (0.06, 0.05, 0.42), (0.12, 0.02, 2.10),
                 (0.14, -0.09, 4.60), (0.06, -0.14, 7.20),
                 (-0.06, -0.10, 9.80), (-0.16, 0.02, 12.40),
                 (-0.24, 0.12, 14.60), (-0.28, 0.18, 15.70)]
    trunk_r = [0.395, 0.300, 0.272, 0.244, 0.216, 0.188, 0.150, 0.110, 0.075]
    bare.append(stem('pine_bole', trunk_pts, trunk_r, 8))

    def trunk_at(z):
        for i in range(len(trunk_pts) - 1):
            a, b = trunk_pts[i], trunk_pts[i + 1]
            if a[2] <= z <= b[2]:
                t = (z - a[2]) / max(1e-6, b[2] - a[2])
                return mathutils.Vector((a[0] + (b[0] - a[0]) * t,
                                         a[1] + (b[1] - a[1]) * t, z))
        return mathutils.Vector(trunk_pts[-1])

    # Dead lower stubs. Short, drooping, and the reason the bare length reads as
    # a trunk that once had branches rather than as a pole.
    for i in range(7):
        z = 3.2 + i * 0.92 + rng.uniform(-0.2, 0.2)
        s, _ = limb('pine_d%d' % i, trunk_at(z), rng.uniform(0, TAU),
                    math.radians(rng.uniform(-24, -6)), rng.uniform(0.6, 1.15),
                    0.055, 0.020, 3, 3, rng, lift_in=math.radians(16),
                    lift_out=math.radians(-16), bow=0.35, wob=0.12, power=1.0)
        bare.append(s)

    plates = ((10.55, 2.55, 0.52, 0.42, -0.30),
              (11.85, 2.35, 0.48, -0.55, 0.30),
              (13.05, 1.95, 0.44, 0.30, 0.50),
              (14.15, 1.45, 0.40, -0.25, -0.35),
              (15.20, 0.95, 0.36, 0.15, 0.10))
    for i, (z, r, flat, ox, oy) in enumerate(plates):
        base = trunk_at(z)
        cx, cy = base.x + ox, base.y + oy
        mass.append(lump('pine_plate%d' % i, (cx, cy, z), (r, r * 0.94, r * flat),
                         relief=0.30, freq=2.0, seed=3.3 * i + 1.9))
        # Two branches carrying each plate, so it is held out from the trunk
        # rather than skewered by it.
        for j in range(2):
            az = math.atan2(cy - base.y, cx - base.x) + (-0.7 if j else 0.7)
            s, _ = limb('pine_b%d_%d' % (i, j), base, az,
                        math.radians(rng.uniform(-14, 6)),
                        r * 0.85 + rng.uniform(0.0, 0.3), 0.062, 0.026, 4, 3, rng,
                        lift_in=math.radians(14), lift_out=math.radians(-14),
                        bow=0.36, wob=0.12, power=1.0)
            bare.append(s)

    for o in bare:
        lib.attach(o, None, timber)
    for o in mass:
        lib.attach(o, None, evergreen)
    obj = lib.merge_into('tree_pine', bare + mass)
    return obj, 16.0


def scrub_gorse(timber, evergreen):
    """1.2 m tall, 1.6 m across. Four angular hummocks meeting the ground with
    no visible stem."""
    rng = random.Random(6899)
    parts = []
    blobs = ((0.0, 0.0, 0.52, 0.62, 0.58, 0.54),
             (0.42, 0.26, 0.40, 0.46, 0.44, 0.40),
             (-0.34, 0.30, 0.36, 0.40, 0.42, 0.36),
             (0.06, -0.40, 0.44, 0.44, 0.40, 0.44))
    for i, (x, y, z, rx, ry, rz) in enumerate(blobs):
        parts.append(lump('gorse%d' % i, (x, y, z), (rx, ry, rz),
                          relief=0.34, freq=2.6, seed=5.7 * i + 2.3, subdiv=0))
    rng.random()
    obj = lib.merge_into('scrub_gorse', parts, mat=evergreen)
    return obj, 1.2


def deadfall(timber, _evergreen):
    """5 m of fallen oak. The root plate torn up at the butt is what says
    windthrown rather than sawn log, and it costs thirty triangles."""
    rng = random.Random(7717)
    parts = []

    log = [(-2.40, 0.00, 0.40), (-1.20, 0.16, 0.36), (0.05, 0.12, 0.31),
           (1.20, -0.08, 0.26), (2.05, -0.20, 0.22), (2.55, -0.26, 0.20)]
    parts.append(stem('dead_log', log, [0.40, 0.355, 0.310, 0.262, 0.226, 0.205], 6))

    # The root plate: an irregular torn disc standing on edge at the butt.
    outline = []
    for i in range(10):
        a = i / 10.0 * TAU
        r = 0.98 * (1.0 + 0.30 * math.sin(a * 3.0 + 0.7) + 0.16 * math.sin(a * 5.0))
        outline.append((math.sin(a) * r, 0.90 + math.cos(a) * r * 0.92))
    outline = [(y, max(0.03, z)) for (y, z) in outline]
    parts.append(lib.prism('dead_plate', outline, 0.26,
                           loc=(-2.62, 0.0, 0.0), plane='yz'))

    for i, (f, az, el, length) in enumerate(
            ((0.22, 1.5, 0.65, 1.35), (0.48, -1.9, 0.50, 1.15),
             (0.72, 2.6, 0.30, 0.95), (0.90, -0.9, 0.75, 0.80))):
        p0 = along(log, f)
        s, _ = limb('dead_s%d' % i, p0, az, el, length, 0.105, 0.042, 4, 3, rng,
                    lift_in=math.radians(12), lift_out=math.radians(-24),
                    bow=0.36, wob=0.12, power=1.05)
        parts.append(s)

    # A broken snag where the top came off, rather than a tidy tapered end.
    snag, _ = limb('dead_snag', along(log, 1.0), -0.3, math.radians(22), 0.55,
                   0.195, 0.055, 5, 3, rng, lift_in=math.radians(10),
                   lift_out=math.radians(-30), bow=0.3, wob=0.05, power=1.6)
    parts.append(snag)

    obj = lib.merge_into('deadfall', parts, mat=timber)
    return obj, None


PIECES = {
    'tree_oak_bare': (tree_oak_bare, 1100),
    'tree_ash_bare': (tree_ash_bare, 1300),
    'tree_hawthorn': (tree_hawthorn, 700),
    'tree_yew': (tree_yew, 620),
    'tree_pine': (tree_pine, 1150),
    'scrub_gorse': (scrub_gorse, 110),
    'deadfall': (deadfall, 240),
}

INSTANCES = {'tree_oak_bare': 34, 'tree_ash_bare': 16, 'tree_hawthorn': 26,
             'tree_yew': 10, 'tree_pine': 20, 'scrub_gorse': 70, 'deadfall': 8}


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def main():
    wanted = argv() or list(PIECES)
    report = []
    table = []
    for name in wanted:
        if name not in PIECES:
            raise SystemExit('unknown piece %r; have %s'
                             % (name, ', '.join(sorted(PIECES))))
        fn, budget = PIECES[name]
        lib.reset()
        timber, evergreen = palette()
        obj, target_h = fn(timber, evergreen)
        k = fit_height(obj, target_h) if target_h else 1.0
        sit_on_ground(obj)
        lo, hi = world_bounds([obj])
        t = tris([obj])
        spread = max(hi[0] - lo[0], hi[1] - lo[1])
        height = hi[2] - lo[2]
        table.append((name, t, budget, height, spread, k))
        print('%-16s %5d tris (budget %d, %+d)   %.2f h x %.2f spread   '
              'crown/height %.2f   fit x%.3f'
              % (name, t, budget, t - budget, height, spread,
                 spread / max(height, 1e-6), k))
        if spread > 1.1 * height:
            print('   WARNING crown is wider than 1.1x the height')
        lib.export(name, report)
    lib.summarise(report)
    print('=== group 1 ===')
    total = 0
    for name, t, budget, h, s, k in table:
        total += t * INSTANCES[name]
        print('%-16s %5d tris x %2d instances = %6d'
              % (name, t, INSTANCES[name], t * INSTANCES[name]))
    print('scene total for the pieces built: %d triangles' % total)
    if LOOK:
        print('NOTE built with TREE_LOOK=1 -- debug grey, do not ship these')


if __name__ == '__main__':
    main()
