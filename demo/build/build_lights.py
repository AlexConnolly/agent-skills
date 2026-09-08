# Asset groups 3 and 4 of "Nightfall at the March Castle": everything that glows.
#
#   blender --background --python build_lights.py -- [piece ...]
#
# Brief: briefs/lights.md, written before this file and committed verbatim.
# Spec:  ART-DIRECTION.md sections 2 (palette), 3.4 and 3.6 (the light budget
#        and every emissive source), 5 group 3 and 5 group 4.
#
# TWO RULES THIS FILE EXISTS TO OBEY
#
# 1. Nothing here ever goes through skin_*.py. texlib.apply_baked() rebuilds a
#    fresh Principled wired to base colour, roughness, normal and metallic, and
#    there is no emission channel in it -- so a baked brazier is a dark bucket.
#    These are all flat lib.material() objects and the texture pass must skip
#    them entirely.
# 2. lib.material() drives Emission Color from the same RGBA as Base Color, so
#    a fire mesh is painted the colour it is meant to glow. Everything is built
#    at emissive=1.0 and docs/js/materials.js sets the real intensity by
#    material name (ART-DIRECTION 3.6), which keeps the whole lighting balance
#    tunable without a Blender rebuild.
#
# AXES AND ORIGINS. Blender, Z-up, metres. Every piece is authored with its
# lowest point on z = 0 and its anchor on the Z axis, so the export report's
# ground-contact line is a real check on all thirteen and placing one is a
# position plus a yaw. Two conventions beyond that:
#
#   panes, shutters, cressets  emit toward local -Y. The wall face is y = 0 and
#                              the room is behind it at +Y.
#   lamp_post                  its hook arm reaches out along -Y.
#
# ART-DIRECTION 5 group 4 lists pane sizes in the castle's own per-opening axis
# order, which is inconsistent between pieces and wrong for pane_loop (its
# 0.44 is the depth of the slit into the drum, taken from on_ring's local
# frame where +X points radially out; the opening is 0.28 wide). Everything
# here is authored in the one convention above and the placement table at the
# bottom of this file gives the position and yaw for all eleven instances.
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, 'art'))

import artconfig as cfg      # noqa: E402
import lib                   # noqa: E402


TAU = math.tau


# ---------------------------------------------------------------- palette
#
# ART-DIRECTION section 2. Nothing outside these.

FIRE_CORE = 0xFFD08A       # the ONE bright thing
FIRE_FLAME = 0xFF9A3C
TALLOW = 0xFFBE6A
EMBER = 0xB23A16
MIST_PALE = 0x5E7488
TIMBER_NIGHT = 0x100D0A
STONE_DARK = 0x151D29


def materials():
    """Rebuilt after every lib.reset(), which clears the material cache."""
    return {
        # Emissive. Painted the colour they glow; strength 1.0 here, the real
        # emissiveIntensity comes from the by-name table in scene code.
        'core': lib.hexmat('emis_fire_core', FIRE_CORE, rough=1.0, emissive=1.0),
        'flame': lib.hexmat('emis_fire_flame', FIRE_FLAME, rough=1.0, emissive=1.0),
        'tallow': lib.hexmat('emis_tallow', TALLOW, rough=1.0, emissive=1.0),
        'ember': lib.hexmat('emis_ember', EMBER, rough=1.0, emissive=1.0),
        # Translucent. The name prefix matters: materials.js dispatches
        # plume_* to transparent + depthWrite false + DoubleSide.
        'vapour': lib.hexmat('plume_vapour', MIST_PALE, rough=1.0, alpha=0.13),
        # The dark mass. Lit by the point light beside it and by nothing else.
        'iron': lib.hexmat('iron_night', TIMBER_NIGHT, rough=0.62),
        'timber': lib.hexmat('timber_night', TIMBER_NIGHT, rough=0.90),
        'stone': lib.hexmat('stone_night', STONE_DARK, rough=0.95),
    }


def paint(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


# ---------------------------------------------------------------- fire

def shard(name, base, h, r, lean, bearing, mat, segments=4, tip=0.008):
    """One tapered flame shard: a faceted cone leaning off vertical.

    Deliberately not a flame *shape*. At the twenty-six pixels per metre this
    scene draws, a cluster of leaning shards through bloom is convincing and a
    modelled flame is a rubber glove. `base` is where it stands, so shards can
    be scattered across a bed without solving for the centre of a rotated cone."""
    dx = math.sin(lean) * math.cos(bearing)
    dy = math.sin(lean) * math.sin(bearing)
    dz = math.cos(lean)
    loc = (base[0] + dx * h / 2, base[1] + dy * h / 2, base[2] + dz * h / 2)
    return paint(lib.cyl(name, r, tip, h, loc=loc, rot=(0.0, lean, bearing),
                         segments=segments), mat)


def fire_bed(name, r1, r2, h, at, mats, segments=8):
    """The hot heart. `fire-core` is the only colour in the whole scene allowed
    to be bright, and it lives here and in the bonfire and nowhere else."""
    return paint(lib.cyl(name, r1, r2, h, loc=(at[0], at[1], at[2] + h / 2),
                         segments=segments), mats['core'])


def embers(name, at, spread, n, mats, seed=0):
    """Coals sitting in the bed: the deepest warm step, and what stops the bed
    reading as a flat disc of light."""
    import random
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a = rng.uniform(0, TAU)
        d = spread * math.sqrt(rng.uniform(0.05, 1.0))
        s = rng.uniform(0.55, 1.0)
        out.append(paint(lib.box('%s%d' % (name, i),
                                 (0.13 * s, 0.10 * s, 0.07 * s),
                                 loc=(at[0] + math.cos(a) * d,
                                      at[1] + math.sin(a) * d,
                                      at[2] + 0.02 * s),
                                 rot=(0, 0, rng.uniform(0, TAU))),
                         mats['ember']))
    return out


# ---------------------------------------------------------------- brazier

def brazier(mats):
    """0.62 across, 1.10 to the flame tips: waist high on a 1.75 m figure.

    A maintained object, not set dressing -- a stand somebody welded, a basket
    somebody refills. Three splayed legs, a stretcher hoop, a shallow pan, six
    bars and a heavy rim, and two brightnesses of fire inside it."""
    out = []
    foot_r, top_r = 0.26, 0.145
    leg_h = 0.60
    lean = math.atan2(foot_r - top_r, leg_h)
    span = math.hypot(foot_r - top_r, leg_h)
    for i in range(3):
        a = i / 3.0 * TAU + math.radians(30)
        r_mid = (foot_r + top_r) / 2
        # -lean tilts the head of the leg inward, so the feet splay outward.
        out.append(paint(lib.cyl('brz_leg%d' % i, 0.030, 0.022, span,
                                 loc=(math.cos(a) * r_mid, math.sin(a) * r_mid,
                                      leg_h / 2),
                                 rot=(0.0, -lean, a), segments=4), mats['iron']))
    out.append(paint(lib.ring('brz_stretcher', 0.185, 0.215, 0.028,
                              loc=(0, 0, 0.20), segments=6), mats['iron']))
    # A shallow pan. Its top cap is solid and sits under the bed, so nothing is
    # lost to it and the ring of iron showing round the fire reads as the pan.
    out.append(paint(lib.cyl('brz_pan', 0.170, 0.290, 0.20, loc=(0, 0, 0.70),
                             segments=8), mats['iron']))
    out.append(paint(lib.ring('brz_rim', 0.278, 0.310, 0.055, loc=(0, 0, 0.815),
                              segments=8), mats['iron']))
    for i in range(6):
        a = i / 6.0 * TAU
        out.append(paint(lib.box('brz_bar%d' % i, (0.030, 0.030, 0.19),
                                 loc=(math.cos(a) * 0.295, math.sin(a) * 0.295,
                                      0.885),
                                 rot=(0.0, -0.16, a)), mats['iron']))
    out.append(fire_bed('brz_bed', 0.235, 0.200, 0.075, (0, 0, 0.760), mats))
    out += embers('brz_ember', (0, 0, 0.822), 0.13, 3, mats, seed=11)
    for i, (h, r, ln, bg) in enumerate((
            (0.30, 0.075, 0.16, 0.4), (0.24, 0.060, 0.26, 2.6),
            (0.19, 0.055, 0.12, 4.5), (0.26, 0.065, 0.21, 5.6),
            (0.15, 0.048, 0.30, 1.6))):
        d = 0.075 if i % 2 else 0.045
        out.append(shard('brz_flame%d' % i,
                         (math.cos(bg + 1.0) * d, math.sin(bg + 1.0) * d, 0.800),
                         h, r, ln, bg, mats['flame']))
    return out


# ---------------------------------------------------------------- bonfire

def bonfire(mats):
    """2.6 across, 1.40 tall. The picture. It sits just inside the breach and
    its light is what escapes through the hole in the wall.

    A ring of set stones rather than a tripod, because this one is a hearth
    somebody built on the ground and has kept going, and crossed logs because
    a fire with no fuel in it is a special effect."""
    out = []
    import random
    rng = random.Random(7)
    for i in range(9):
        a = i / 9.0 * TAU
        w = rng.uniform(0.34, 0.48)
        d = rng.uniform(0.24, 0.34)
        h = rng.uniform(0.22, 0.34)
        r = 1.10 - d / 2
        out.append(paint(lib.box('bnf_stone%d' % i, (d, w, h),
                                 loc=(math.cos(a) * r, math.sin(a) * r, h / 2),
                                 rot=(0, 0, a + rng.uniform(-0.25, 0.25))),
                         mats['stone']))
    # Nine logs, crossed. Two lengths and two heights so the stack has a top
    # and a bottom rather than reading as a bundle.
    for i in range(9):
        a = i / 9.0 * TAU + 0.35
        length = rng.uniform(1.25, 1.70)
        tilt = rng.uniform(0.85, 1.20)      # from vertical: nearly lying down
        z0 = rng.uniform(0.10, 0.34)
        rad = rng.uniform(0.062, 0.095)
        out.append(shard('bnf_log%d' % i, (math.cos(a) * 0.78,
                                           math.sin(a) * 0.78, z0),
                         length, rad, tilt, a + math.pi, mats['timber'],
                         segments=5, tip=rad * 0.82))
    out.append(fire_bed('bnf_bed', 0.80, 0.62, 0.26, (0, 0, 0.12), mats,
                        segments=10))
    out += embers('bnf_ember', (0, 0, 0.38), 0.55, 5, mats, seed=23)
    for i, (h, r, ln, bg) in enumerate((
            (0.95, 0.20, 0.14, 0.9), (0.72, 0.17, 0.28, 2.4),
            (1.02, 0.19, 0.09, 4.0), (0.60, 0.15, 0.31, 5.3),
            (0.80, 0.16, 0.20, 3.1), (0.52, 0.13, 0.36, 1.7))):
        d = 0.36 if i % 2 else 0.20
        out.append(shard('bnf_flame%d' % i,
                         (math.cos(bg + 0.7) * d, math.sin(bg + 0.7) * d, 0.38),
                         h, r, ln, bg, mats['flame'], segments=5))
    return out


# ---------------------------------------------------------------- lantern

def lantern(mats):
    """0.22 square, 0.34 to the top of the bail.

    A horn lantern: an iron frame with four cloudy panes. Not a glass box, not
    a modern hurricane lamp. The frame has to be heavy relative to the panes,
    and the cap has to be a real vented pyramid, or it reads as Victorian."""
    out = []
    out.append(paint(lib.box('ltn_base', (0.20, 0.20, 0.026), loc=(0, 0, 0.013)),
                     mats['iron']))
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(paint(lib.box('ltn_post%d%d' % (sx > 0, sy > 0),
                                     (0.024, 0.024, 0.222),
                                     loc=(sx * 0.088, sy * 0.088, 0.137)),
                             mats['iron']))
    # Horn, not glass: set inside the frame, and the only emissive part.
    for k, (sx, sy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        size = (0.146, 0.010, 0.186) if sy else (0.010, 0.146, 0.186)
        out.append(paint(lib.box('ltn_pane%d' % k, size,
                                 loc=(sx * 0.086, sy * 0.086, 0.137)),
                         mats['tallow']))
    out.append(paint(lib.box('ltn_cap', (0.224, 0.224, 0.056), loc=(0, 0, 0.276),
                             taper=0.26), mats['iron']))
    out.append(paint(lib.box('ltn_vent', (0.038, 0.038, 0.030), loc=(0, 0, 0.311)),
                     mats['iron']))
    for sx in (-1, 1):
        out.append(paint(lib.box('ltn_bail%d' % (sx > 0), (0.013, 0.013, 0.032),
                                 loc=(sx * 0.044, 0, 0.318)), mats['iron']))
    out.append(paint(lib.box('ltn_bailtop', (0.101, 0.013, 0.013),
                             loc=(0, 0, 0.334)), mats['iron']))
    return out


# ---------------------------------------------------------------- cresset

def cresset(mats):
    """0.34 across the bowl, 0.50 tall, mounted on a wall face at y = 0 and
    reaching out along -Y. An open bowl of burning pitch on a bracket."""
    out = []
    out.append(paint(lib.box('crs_plate', (0.090, 0.030, 0.300),
                             loc=(0, -0.015, 0.150)), mats['iron']))
    out.append(paint(lib.box('crs_arm', (0.048, 0.215, 0.048),
                             loc=(0, -0.135, 0.265)), mats['iron']))
    # The diagonal stay is what says somebody hung this on a wall and meant it
    # to stay there.
    out.append(paint(lib.box('crs_stay', (0.034, 0.034, 0.235),
                             loc=(0, -0.112, 0.170), rot=(0.86, 0, 0)),
                     mats['iron']))
    bowl = paint(lib.revolve('crs_bowl',
                             [(0.055, 0.000), (0.165, 0.115),
                              (0.170, 0.140), (0.132, 0.032)],
                             segments=8), mats['iron'])
    bowl.location = (0.0, -0.235, 0.280)
    out.append(bowl)
    out.append(fire_bed('crs_bed', 0.130, 0.108, 0.050, (0, -0.235, 0.392),
                        mats, segments=6))
    for i, (h, r, ln, bg) in enumerate(((0.106, 0.045, 0.14, 0.5),
                                        (0.082, 0.038, 0.30, 2.9),
                                        (0.094, 0.040, 0.22, 4.7))):
        out.append(shard('crs_flame%d' % i,
                         (-math.cos(bg) * 0.045, -0.235 + math.sin(bg) * 0.045,
                          0.420),
                         h, r, ln, bg, mats['flame'], segments=3))
    return out


# ---------------------------------------------------------------- lamp post

def lamp_post(mats):
    """0.16 square, 2.40 to the cap: a hand taller than a man. Carries the
    lanterns on the causeway and the bridge. Nothing on it is emissive."""
    out = []
    out.append(paint(lib.box('lmp_stone', (0.34, 0.34, 0.14), loc=(0, 0, 0.07),
                             chamfer=0.02), mats['stone']))
    out.append(paint(lib.box('lmp_post', (0.16, 0.16, 2.20), loc=(0, 0, 1.24),
                             chamfer=0.014), mats['timber']))
    out.append(paint(lib.box('lmp_strap', (0.176, 0.176, 0.050),
                             loc=(0, 0, 1.92)), mats['iron']))
    out.append(paint(lib.box('lmp_arm', (0.046, 0.300, 0.046),
                             loc=(0, -0.130, 2.260)), mats['iron']))
    out.append(paint(lib.box('lmp_hook', (0.036, 0.036, 0.110),
                             loc=(0, -0.262, 2.205)), mats['iron']))
    out.append(paint(lib.box('lmp_cap', (0.208, 0.208, 0.060), loc=(0, 0, 2.370),
                             taper=0.55), mats['iron']))
    return out


# ---------------------------------------------------------------- plumes

def plume(mats, name, height, width, points, straight=0.62, bend_deg=30.0,
          throat=0.50, flatten=0.55):
    """A smoke column. `lib.sweep`, not `profile`, because the section has to
    change shape and not only size: a plume on a clear cold night rises, hits
    the inversion, and flattens into an ellipse rather than going on climbing.

    Rises near vertical for `straight` of its height, then bends `bend_deg` off
    vertical and drifts north-east -- the same south-west wind that leans the
    hawthorns and the keep banner. Widens from a chimney-sized `throat` to the
    full width. No emission at all: it is lit by the moon behind it and the
    fires under it."""
    drift = (math.cos(math.radians(45)), math.sin(math.radians(45)))   # NE
    theta_max = math.radians(bend_deg)

    def theta(t):
        u = (t - straight * 0.72) / (1.0 - straight * 0.72)
        u = min(1.0, max(0.0, u))
        return theta_max * (u * u * (3 - 2 * u))          # smoothstep

    path, sections = [], []
    s = 0.0
    prev_z = 0.0
    for i in range(points):
        t = i / (points - 1.0)
        z = height * t
        s += math.tan(theta(t)) * (z - prev_z)
        prev_z = z
        path.append((drift[0] * s, drift[1] * s, z))
        w = throat + (width - throat) * (t ** 0.72)
        a = w / 2.0
        b = a * (1.0 - (1.0 - flatten) * (t ** 1.4))
        sections.append([(math.cos(k / 8.0 * TAU) * a,
                          math.sin(k / 8.0 * TAU) * b) for k in range(8)])
    return [paint(lib.sweep(name, path, sections, close=True), mats['vapour'])]


# ---------------------------------------------------------------- lit openings

def pane(mats, name, w, t, h, mat='tallow'):
    """A lit opening plate. Thin in Y, emitting toward -Y, base on z = 0.

    Twelve triangles and one of the three most important assets in the scene:
    it is the difference between a black hole in a wall and a room with people
    in it."""
    return [paint(lib.box(name, (w, t, h), loc=(0, 0, h / 2)), mats[mat])]


def oven_mouth(mats):
    """The bake-house oven's round-headed mouth, 0.55 by 0.70, in `ember` --
    the deepest warm step, and the only source in the scene that is not tallow
    or fire. A rectangle would read as a letterbox; the arch is what says oven."""
    hw, spring, apex = 0.275, 0.425, 0.700
    outline = [(-hw, 0.0), (hw, 0.0), (hw, spring)]
    for k in range(1, 7):
        a = k / 6.0 * math.pi
        outline.append((hw * math.cos(a), spring + (apex - spring) * math.sin(a)))
    outline.append((-hw, spring))
    return [paint(lib.prism('oven_mouth', outline, 0.060, plane='xz'),
                  mats['ember'])]


def shutter(mats):
    """0.72 by 2.10, hinged on the Z axis and authored flat in the wall plane so
    the scene can swing the two of them to different angles.

    This is the whole trick of group 4. A bare lit rectangle reads as a decal;
    a lit rectangle with a timber shutter swung two thirds across it, throwing
    a hard edge over the light, reads as a window in a building somebody lives
    in. Four boards with real gaps between them, two ledges behind, two strap
    hinges in front."""
    out = []
    for i in range(4):
        out.append(paint(lib.box('sht_board%d' % i, (0.170, 0.026, 2.100),
                                 loc=(0.090 + i * 0.180, 0.007, 1.050)),
                         mats['timber']))
    for k, z in enumerate((0.360, 1.740)):
        out.append(paint(lib.box('sht_ledge%d' % k, (0.706, 0.018, 0.140),
                                 loc=(0.358, 0.029, z)), mats['timber']))
        out.append(paint(lib.box('sht_strap%d' % k, (0.400, 0.010, 0.055),
                                 loc=(0.200, -0.011, z)), mats['iron']))
    return out


# ---------------------------------------------------------------- the kit

PIECES = {
    'brazier': brazier,
    'bonfire': bonfire,
    'lantern': lantern,
    'cresset': cresset,
    'lamp_post': lamp_post,
    'plume_tall': lambda m: plume(m, 'plume_tall', 13.0, 2.50, 24),
    'plume_low': lambda m: plume(m, 'plume_low', 8.0, 1.80, 18),
    'pane_window': lambda m: pane(m, 'pane_window', 1.40, 0.06, 2.10),
    'pane_hall': lambda m: pane(m, 'pane_hall', 1.05, 0.10, 1.40),
    'pane_loop': lambda m: pane(m, 'pane_loop', 0.28, 0.06, 1.45),
    'pane_lancet': lambda m: pane(m, 'pane_lancet', 1.20, 0.10, 2.40),
    'pane_passage': lambda m: pane(m, 'pane_passage', 1.90, 0.06, 2.60),
    'oven_mouth': oven_mouth,
    'shutter': shutter,
}

# Every instance in the scene, as Three.js metres and a yaw about Three.js +Y.
# Positions are the piece's ANCHOR -- the point authored at the local origin,
# which is on the ground for anything that stands and on the bottom edge of the
# opening for anything that hangs on a wall. ART-DIRECTION quotes several of
# these as box centres; those have been converted here, once, so nobody has to
# do it twice.
#
#   piece         Three.js (x, y, z)          yaw    note
#   brazier       (6.0, 0.0, 26.2)              -    gate passage
#   brazier       (6.0, 10.4, 22.0)             -    wall-walk over the gate
#   brazier       (-19.0, 0.0, 6.0)             -    hall door
#   brazier       (12.0, 0.0, 8.0)              -    ward
#   bonfire       (24.0, 0.0, -2.0)             -    just inside the breach
#   lamp_post     (48.0, -1.0, 24.0)          180    bridge post
#   lamp_post     (9.5, 0.2, 30.4)             90    causeway
#   lamp_post     (2.5, 0.2, 30.4)             90    causeway
#   lantern       hung from each post at anchor + (arm) - (0, 0.34, 0)
#   cresset       (3.4, 8.6, 28.2)              0    gatehouse front, west
#   cresset       (8.6, 7.4, 28.2)              0    gatehouse front, east
#   cresset       (26.2, 9.8, 19.6)           -90    SE tower
#   cresset       (7.4, 3.2, 25.4)            180    gate passage, inner
#   plume_tall    (-14.9, 23.5, -9.1)           -    keep chimney head
#   plume_low     (-24.8, 8.9, 3.5)             -    hall ridge
#   plume_low     (23.6, 3.1, 16.6)             -    oven flue
#   pane_window   (-14.5, 13.45, 1.44)          0    keep, west of centre
#   pane_window   (-4.5, 13.45, 1.44)           0    keep, east of centre
#   shutter       (-15.2, 13.45, 1.42)         52    across the first pane
#   shutter       (-3.8, 13.45, 1.42)         -34    across the second
#   pane_hall     (-19.63, 4.90, 12.3)         90    hall, near end
#   pane_hall     (-19.63, 4.90, 9.1)          90    hall, next along
#   pane_loop     (13.2, 8.68, 26.4)         -58.4   east gate drum
#   pane_lancet   (11.33, 2.00, -11.0)        -90    chapel west
#   pane_passage  (6.0, 0.10, 24.0)             0    4 m back inside the passage
#   oven_mouth    (22.9, 0.55, 16.6)          -90    bake-house oven front


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def main():
    wanted = argv() or list(PIECES)
    unknown = [w for w in wanted if w not in PIECES]
    if unknown:
        raise SystemExit('no such piece: %s\nhave: %s'
                         % (', '.join(unknown), ', '.join(sorted(PIECES))))
    report = []
    for name in wanted:
        lib.reset()
        parts = PIECES[name](materials())
        lib.merge_into(name, parts)
        lib.export(name, report)
    lib.summarise(report)
    print('OUT     %s' % os.path.abspath(cfg.OUT))


if __name__ == '__main__':
    main()
