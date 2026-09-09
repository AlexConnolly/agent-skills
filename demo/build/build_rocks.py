# Nightfall at the March Castle — asset group 2, the rock and outcrop kit.
#
#   blender --background --python build_rocks.py
#   blender --background --python build_rocks.py -- boulder_a     (one piece)
#
# Brief: demo/build/briefs/rocks.md, written first and committed verbatim.
# Spec:  demo/ART-DIRECTION.md section 5 group 2.
#
# WHY THESE ARE PRISMS AND NOT WARPED SPHERES
#
# The brief bans potatoes, and the reason is petrological rather than
# aesthetic: limestone is a BEDDED rock. It was laid down in flat sheets and it
# breaks along them, and along near-vertical joints at right angles to them. So
# an outcrop is a stack of slabs with flat tops, flat sides and sharp arrises —
# and a stack of slabs is exactly lib.prism(): an arbitrary 2D plan extruded
# into a slab, one call per bed. Each bed gets its own irregular plan, its own
# small offset and its own dip, and the steps between them are real steps in
# the silhouette rather than shading that vanishes at night.
#
# Nothing is smoothed and nothing is bevelled. A bevel you can see on a rock is
# a bevel that is too big, and at 22-90 px/m a 4 cm one is invisible while
# costing a third of the triangle budget. What the surface gets instead is
# lib.displace() with coordinate-derived noise, which moves the vertices that
# are already there and adds nothing.
#
# NOTHING HERE MAY BE DISTINCTIVE. Between them these five pieces are drawn 62
# times. A memorable crack or a bright face is worse than no detail at all,
# because it reads as a repeat. All the variety is in the placement jitter.
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, 'art_props'))

import artconfig as cfg          # noqa: E402
import lib                       # noqa: E402
import texlib                    # noqa: E402
import props_common as pc        # noqa: E402


# ---------------------------------------------------------------- the colour ramp

def rock_colour(co, normal, base_z=0.0, wet=0.0):
    """Grey-brown limestone, dark in the crevices, green-grey at the foot.

    Three terms, and each of them is doing a specific job at night:

      * facing        an upward face catches the cold hemisphere fill and a
                      downward one goes to near-black. This is most of what
                      makes an unlit shape read at all (section 3.2).
      * crevice       a cheap ambient-occlusion stand-in: low and inward-facing
                      geometry is darker. Real AO needs a bake and there is no
                      bake here.
      * moss          green-grey creeping up the bottom 20-30 cm where the turf
                      meets the stone.
    """
    up = max(0.0, normal.z)
    facing = 0.30 + 0.70 * (up ** 0.7)
    h = co.z - base_z
    crevice = 1.0 - 0.35 * math.exp(-max(0.0, h) * 2.2)
    n = pc.fbm3(co.x * 0.55, co.y * 0.55, co.z * 0.9, 71, 2)
    k = max(0.0, min(1.0, facing * crevice + n * 0.10 - wet * 0.18))
    c = pc.lerp3(pc.lin(pc.ROCK_DARK), pc.lin(pc.ROCK_LIT), k)
    moss = max(0.0, 1.0 - h / 0.30) * (0.55 + 0.45 * n)
    return pc.lerp3(c, pc.lin(pc.ROCK_MOSS), max(0.0, min(0.75, moss)))


def paint(obj, base_z=0.0, wet=0.0):
    texlib.vertex_colour(obj, lambda co, nrm: rock_colour(co, nrm, base_z, wet))
    return obj


# ---------------------------------------------------------------- one bedded block

def seat_and_size(obj, size):
    """Put the floor on z=0, the plan centred, and the extents exactly on spec.

    Two jobs in one pass, and both matter. The floor, because a rock that
    floats 8 cm is the fault section 9.4 rejects the scene for and no render of
    an isolated model shows it. The extents, because shear, relief and a
    boolean all move the bounding box, so a block authored at 6.0 x 4.0 x 2.4
    comes out at 6.85 x 4.58 x 3.03 and the size in the table stops being true.
    Scaling the finished mesh to the spec is the only way the number in the
    brief stays the number in the model."""
    lo, hi = pc.bbox([obj])
    ex = [max(1e-6, hi[i] - lo[i]) for i in range(3)]
    k = [size[i] / ex[i] for i in range(3)]
    cx, cy = (lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5
    for v in obj.data.vertices:
        v.co = ((v.co.x - cx) * k[0], (v.co.y - cy) * k[1],
                (v.co.z - lo[2]) * k[2])
    return obj


def bedded_block(name, length, width, height, beds, seed,
                 plan_points=9, taper=0.60, dip=7.0, reentrant=1,
                 relief=0.05, step=0.42):
    """A stack of limestone beds: the whole kit is built out of this.

    `beds` slabs, each with its own irregular plan, each smaller and shoved off
    the one below, the whole sequence sheared over a few degrees because
    bedding is never level once the ground has moved. The offsets are what put
    steps in the SILHOUETTE; without them this is a tapered lump that only
    reads as bedded under a light, and there is no light here.

    Sheared rather than rotated: a shear leaves the joint faces plumb and only
    tilts the beds, which is what a dipping sequence with vertical jointing
    actually looks like."""
    rng = pc.Rng(seed)
    # Bed thicknesses vary: a sequence of equal beds reads as a machined stack.
    thick = [rng.uni(0.62, 1.45) for _ in range(beds)]
    tsum = sum(thick)
    thick = [t / tsum * height for t in thick]

    # ONE loft, not a pile of prisms. A stack of separately-built slabs is a
    # bag of interpenetrating closed shells, and the EXACT boolean solver
    # answers a self-intersecting target with an empty mesh — which is how the
    # first version of this function deleted every rock in the kit. Two
    # stations at the same height with different plans give a real vertical
    # step between beds, so the loft loses nothing.
    stations = []
    z = 0.0
    ox = oy = 0.0
    for i in range(beds):
        t = thick[i]
        # Taper up the stack, plus a per-bed wobble, so consecutive beds differ
        # in plan by enough to read as a step at 40 m and not merely as a line.
        k = (1.0 - (1.0 - taper) * (z / height if height else 0.0)) \
            * rng.uni(0.88, 1.10)
        outline = pc.blob_outline(plan_points, length * 0.5 * k,
                                  width * 0.5 * k, seed * 31 + i * 7,
                                  rough=0.20, reentrant=reentrant if i else 0)
        ox += rng.uni(-step, step) * t
        oy += rng.uni(-step * 0.8, step * 0.8) * t
        a = rng.uni(-0.26, 0.26)
        ca, sa = math.cos(a), math.sin(a)
        sect = [(px * ca - py * sa + ox, px * sa + py * ca + oy)
                for (px, py) in outline]
        stations.append((z, sect))
        stations.append((z + t, sect))
        z += t
    obj = lib.loft(name, stations, cap_ends=True)
    # loft sweeps along X; this is a stack, so turn it up the Z axis. Done as a
    # coordinate swap rather than a rotation so the mesh coordinates and the
    # world coordinates stay the same thing for everything that follows.
    for v in obj.data.vertices:
        v.co = (v.co.y, v.co.z, v.co.x)
    tan = math.tan(math.radians(dip))
    for v in obj.data.vertices:
        v.co.z += v.co.x * tan
    # Surface relief. Low frequency, small amplitude: the faces stay flat
    # enough to read as cleavage and gain enough irregularity not to read as
    # cardboard. lib.displace moves the vertices that are already there, so
    # this costs nothing.
    lib.displace(obj, lambda co, nrm: (
        pc.fbm3(co.x * 0.42, co.y * 0.42, co.z * 0.55, seed, 2) * relief,
        pc.fbm3(co.x * 0.42 + 9, co.y * 0.42, co.z * 0.55, seed + 3, 2) * relief,
        pc.fbm3(co.x * 0.42, co.y * 0.42 + 9, co.z * 0.55, seed + 6, 2)
        * relief * 0.6))
    return obj


def joint_face(obj, seed, count=2, depth=0.22):
    """Take a near-vertical joint off the block: a flat plane, full height.

    A bed sequence with no joints is a wedding cake. One or two flat planes
    running the whole height of the piece, at an angle to the bedding, is what
    makes it limestone rather than sedimentary shortbread.

    This clips the vertices onto the plane rather than cutting with a boolean,
    and that is a deliberate choice rather than a shortcut. lib.cut on this
    target reduced a 130-vertex block to 7 — the EXACT solver wants closed
    non-self-intersecting input, and a bed sequence whose plans cross each
    other in places is not that. Clipping is exact, costs no triangles, and
    lands every clipped vertex ON the plane, which is a flatter face than a
    boolean would leave. What it cannot do is cut a re-entrant notch; the beds
    already provide those."""
    rng = pc.Rng(seed)
    for i in range(count):
        a = rng.uni(0, math.tau)
        # A few degrees off plumb. Joints in a bedded rock are near-vertical
        # and never exactly vertical, and the difference is the one thing that
        # stops a clipped face reading as a saw cut.
        tilt = rng.uni(-0.13, 0.13)
        n = (math.cos(a) * math.cos(tilt), math.sin(a) * math.cos(tilt),
             math.sin(tilt))
        lo, hi = pc.bbox([obj])
        c = ((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5,
             (lo[2] + hi[2]) * 0.5)
        proj = [sum((v.co[j] - c[j]) * n[j] for j in range(3))
                for v in obj.data.vertices]
        limit = max(proj) - depth * rng.uni(0.65, 1.5)
        for v, p in zip(obj.data.vertices, proj):
            if p > limit:
                over = p - limit
                v.co = tuple(v.co[j] - n[j] * over for j in range(3))
    return obj


# ---------------------------------------------------------------- the five pieces

def rock_outcrop_a():
    """6.0 x 4.0 x 2.4, ~380 tris, 9 instances on the platform batter.

    The biggest piece and the one that has to say the castle was cut from the
    rock it stands on: four beds, chest high on a man, three and a half of him
    long, breaking out of the turf."""
    o = bedded_block('rock_outcrop_a', 6.0, 4.0, 2.4, beds=5, seed=11,
                     plan_points=15, taper=0.30, dip=13.0, reentrant=2,
                     step=0.55)
    joint_face(o, 21, count=3, depth=0.42)
    seat_and_size(o, (6.0, 4.0, 2.4))
    return paint(o)


def rock_outcrop_b():
    """3.6 x 3.0 x 1.6, ~260 tris, 14 on the ditch sides and the knoll crest."""
    o = bedded_block('rock_outcrop_b', 3.6, 3.0, 1.6, beds=3, seed=29,
                     plan_points=13, taper=0.42, dip=15.0, reentrant=1,
                     step=0.55)
    joint_face(o, 47, count=2, depth=0.30)
    seat_and_size(o, (3.6, 3.0, 1.6))
    return paint(o)


def boulder_a():
    """1.8 x 1.4 x 1.2, ~150 tris, 18 scattered, 3 of them inside 25 m.

    Knee high. Two beds only — at this size you are looking at a single block
    that has come off the outcrop, not a sequence."""
    o = bedded_block('boulder_a', 1.8, 1.4, 1.2, beds=3, seed=53,
                     plan_points=9, taper=0.64, dip=14.0, reentrant=1,
                     relief=0.030)
    joint_face(o, 61, count=2, depth=0.20)
    seat_and_size(o, (1.8, 1.4, 1.2))
    return paint(o)


def boulder_b():
    """1.1 x 0.9 x 0.7, ~110 tris, 16. A thing you would step over."""
    o = bedded_block('boulder_b', 1.1, 0.9, 0.7, beds=2, seed=83,
                     plan_points=8, taper=0.68, dip=18.0, reentrant=1,
                     relief=0.018)
    joint_face(o, 97, count=2, depth=0.13)
    seat_and_size(o, (1.1, 0.9, 0.7))
    return paint(o)


def scree_run():
    """8.0 x 3.0 x 0.6, ~340 tris, 5 below the outcrops.

    Loose broken rock at its angle of repose, thinning to nothing at both ends
    so it can butt the castle's own rubble spill without a seam. Chips, not a
    slab: lib.array places them along the run and the seeded jitter does all
    the variety, which is the same discipline the placement code uses on the
    kit as a whole."""
    rng = pc.Rng(7)

    # A bed of small stuff first. The first version of this was chips alone and
    # `iso_a.png` showed bare turf between them all the way along, so it read as
    # debris somebody had dropped in a line rather than as a run of loose rock.
    # A scree is CONTINUOUS: fines under, blocks on top.
    bed = pc.blob_outline(11, 4.0, 1.5, 909, rough=0.16)
    parts = [lib.prism('scree_bed', bed, 0.19, loc=(0, 0, 0.06), plane='xy')]

    def chip(i, pos, angle):
        # A lens, not a bar: the run thins to nothing at both ends so it can
        # butt the castle's own rubble spill without a seam.
        env = math.sin(math.pi * min(1.0, max(0.0, i / 17.0))) ** 0.45
        if env < 0.12:
            return None
        s = rng.uni(0.30, 0.62) * (0.55 + 0.75 * env)
        outline = pc.blob_outline(5, s, s * rng.uni(0.60, 0.95),
                                  700 + i, rough=0.30)
        return lib.prism('scree_chip%d' % i, outline,
                         s * rng.uni(0.45, 0.85),
                         loc=(pos[0], pos[1] * env, pos[2] + s * 0.22 * env),
                         rot=(rng.uni(-0.45, 0.45), rng.uni(-0.45, 0.45), angle),
                         plane='xy')

    parts += lib.array(chip, 18, step=(0.47, 0.0, 0.0), start=(-4.0, 0.0, 0.10),
                       jitter=(0.20, 0.95, 0.10), turn=math.pi, scale=0.0,
                       seed=5)
    obj = lib.merge_into('scree_run', parts)
    seat_and_size(obj, (8.0, 3.0, 0.6))
    return paint(obj, wet=0.25)


PIECES = {
    'rock_outcrop_a': (rock_outcrop_a, 380, 9),
    'rock_outcrop_b': (rock_outcrop_b, 260, 14),
    'boulder_a': (boulder_a, 150, 18),
    'boulder_b': (boulder_b, 110, 16),
    'scree_run': (scree_run, 340, 5),
}

ORDER = ['rock_outcrop_a', 'rock_outcrop_b', 'boulder_a', 'boulder_b',
         'scree_run']


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def main():
    args = argv()
    want = args if args else ORDER
    report = []
    rows = []
    total_instanced = 0
    for name in want:
        build, budget, instances = PIECES[name]
        lib.reset()
        obj = build()
        obj.data.materials.clear()
        obj.data.materials.append(pc.vertex_material('rock_' + name, rough=0.94))
        lib.export(name, report)
        tris = report[-1][1]
        lo, hi = pc.bbox([obj])
        rows.append((name, tris, budget,
                     '%.2f x %.2f x %.2f m' % (hi[0] - lo[0], hi[1] - lo[1],
                                               hi[2] - lo[2]),
                     'x%d' % instances))
        total_instanced += tris * instances
    lib.summarise(report)
    pc.budget_table(rows)
    print('kit in the scene: %d triangles over %d instances  (section 5 says '
          '~9 500)' % (total_instanced, sum(PIECES[n][2] for n in want)))


if __name__ == '__main__':
    main()
