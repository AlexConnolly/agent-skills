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
sys.path.append(os.path.join(HERE, 'art_lights'))

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


def fire_bed(name, r, h, at, mats, seed=0, slabs=3):
    """The hot heart, as a cluster of overlapping slabs rather than a disc.

    An emissive surface does not shade -- every face of it renders the same
    value whichever way it points -- so the only things that read on a bed of
    `fire-core` are its OUTLINE and whatever dark geometry bites into it. Pass
    one made this a flat-topped cylinder and it came back from the render as a
    plate of cream sitting in a black bowl, in all three fires at once.

    Overlapping slabs at three bearings give a broken edge for nothing; sinking
    the bed below the rim of the thing that holds it gives the dark a bite; and
    the ember lumps take the rest of the bright area away."""
    import random
    rng = random.Random(seed)
    out = []
    for i in range(slabs):
        a = rng.uniform(0, TAU)
        d = r * rng.uniform(0.0, 0.36)
        s = rng.uniform(0.74, 1.0)
        out.append(paint(lib.box('%s%d' % (name, i),
                                 (r * 1.72 * s, r * 1.26 * s,
                                  h * rng.uniform(0.68, 1.0)),
                                 loc=(at[0] + math.cos(a) * d,
                                      at[1] + math.sin(a) * d,
                                      at[2] + h / 2),
                                 rot=(0, 0, rng.uniform(0, TAU))),
                         mats['core']))
    return out


def embers(name, at, spread, n, mats, seed=0, size=1.0):
    """Coals sitting proud on the bed: the deepest warm step, and -- more
    usefully -- the dark-ish lumps that break the bright shape up."""
    import random
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a = rng.uniform(0, TAU)
        d = spread * math.sqrt(rng.uniform(0.10, 1.0))
        s = rng.uniform(0.62, 1.0) * size
        out.append(paint(lib.box('%s%d' % (name, i),
                                 (0.19 * s, 0.14 * s, 0.10 * s),
                                 loc=(at[0] + math.cos(a) * d,
                                      at[1] + math.sin(a) * d,
                                      at[2] + 0.02 * s),
                                 rot=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3),
                                      rng.uniform(0, TAU))),
                         mats['ember']))
    return out


# ---------------------------------------------------------------- brazier

def brazier(mats):
    """0.62 across, 1.10 to the flame tips: waist high on a 1.75 m figure.

    A maintained object, not set dressing -- a stand somebody welded, a basket
    somebody refills. Three splayed legs, a stretcher hoop, a shallow pan, six
    bars and a heavy rim, and two brightnesses of fire inside it."""
    out = []
    foot_r, top_r = 0.255, 0.140
    leg_h = 0.585
    r_leg = 0.034
    lean = math.atan2(foot_r - top_r, leg_h)
    span = math.hypot(foot_r - top_r, leg_h)
    for i in range(3):
        a = i / 3.0 * TAU + math.radians(30)
        r_mid = (foot_r + top_r) / 2
        # -lean tilts the head of the leg inward, so the feet splay outward.
        # The z is solved, not guessed: the lowest cap vertex of a cone tilted
        # by `lean` sits half a span plus r*sin(lean) below its centre, and the
        # first pass put the feet a centimetre through the floor.
        out.append(paint(lib.cyl('brz_leg%d' % i, r_leg, 0.024, span,
                                 loc=(math.cos(a) * r_mid, math.sin(a) * r_mid,
                                      span / 2 * math.cos(lean)
                                      + r_leg * math.sin(lean)),
                                 rot=(0.0, -lean, a), segments=4), mats['iron']))
    out.append(paint(lib.ring('brz_stretcher', 0.170, 0.203, 0.030,
                              loc=(0, 0, 0.265), segments=6), mats['iron']))
    # A SHALLOW pan -- pass one made this 0.20 deep with a hard taper and it
    # photographed as a barbecue kettle. Its top cap is solid and sits under
    # the bed, so nothing is lost to it.
    out.append(paint(lib.cyl('brz_pan', 0.225, 0.292, 0.135, loc=(0, 0, 0.655),
                             segments=8), mats['iron']))
    # Basket: bars between the pan and a heavy rim hoop that CAPS them. Pass
    # one hung the hoop below the bar tops and the bars read as loose skewers
    # stuck round the edge of a barbecue.
    for i in range(6):
        a = i / 6.0 * TAU
        out.append(paint(lib.box('brz_bar%d' % i, (0.032, 0.032, 0.150),
                                 loc=(math.cos(a) * 0.294, math.sin(a) * 0.294,
                                      0.795),
                                 rot=(0.0, -0.05, a)), mats['iron']))
    out.append(paint(lib.ring('brz_rim', 0.278, 0.312, 0.048, loc=(0, 0, 0.862),
                              segments=8), mats['iron']))
    # The bed sits BELOW the rim, so the hoop and the bars cut across it.
    out += fire_bed('brz_bed', 0.148, 0.072, (0, 0, 0.706), mats, seed=5)
    out += embers('brz_ember', (0, 0, 0.769), 0.120, 4, mats, seed=11, size=0.68)
    for i, (h, r, ln, bg) in enumerate((
            (0.315, 0.072, 0.10, 0.35), (0.205, 0.055, 0.44, 2.55),
            (0.145, 0.046, 0.20, 4.60), (0.265, 0.063, 0.31, 5.65),
            (0.110, 0.040, 0.52, 1.70), (0.185, 0.050, 0.14, 3.55))):
        d = (0.085, 0.030, 0.100, 0.055, 0.110, 0.070)[i]
        out.append(shard('brz_flame%d' % i,
                         (math.cos(bg + 1.0) * d, math.sin(bg + 1.0) * d, 0.775),
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
    # Eleven stones, close enough together to be a RING. Pass one used nine at
    # radius 1.10 and they read as boxes dropped on the floor round a fire
    # rather than a kerb somebody laid.
    for i in range(11):
        a = i / 11.0 * TAU
        w = rng.uniform(0.44, 0.60)
        d = rng.uniform(0.26, 0.36)
        h = rng.uniform(0.24, 0.38)
        r = 1.22 - d / 2
        out.append(paint(lib.box('bnf_stone%d' % i, (d, w, h),
                                 loc=(math.cos(a) * r, math.sin(a) * r, h / 2),
                                 rot=(0, 0, a + rng.uniform(-0.22, 0.22))),
                         mats['stone']))
    # Eight logs standing off the kerb and crossing OVER the fire, their tips
    # gathering around a metre up. Pass one laid them nearly flat and they flew
    # out past the ring like a cheval de frise; pass two stood them on a tight
    # circle and they converged to a point like a black starburst. The fix is
    # to move the FEET out to the kerb, so the sticks cross the bright bed
    # instead of radiating from it, and to scatter where the tips arrive.
    for i in range(8):
        a = i / 8.0 * TAU + 0.35
        foot = rng.uniform(0.88, 1.02)
        rise = rng.uniform(0.80, 1.05)
        z0 = rng.uniform(0.06, 0.20)
        rad = rng.uniform(0.058, 0.090)
        out.append(shard('bnf_log%d' % i, (math.cos(a) * foot,
                                           math.sin(a) * foot, z0),
                         math.hypot(foot, rise), rad, math.atan2(foot, rise),
                         a + math.pi, mats['timber'],
                         segments=5, tip=rad * 0.80))
    # Two big logs lying across it, which is what a fire somebody feeds looks
    # like and which puts a dark bar over the middle of the bright bed.
    for i, (a, ln) in enumerate(((0.55, 1.95), (3.05, 1.75))):
        out.append(shard('bnf_baulk%d' % i,
                         (math.cos(a) * ln / 2, math.sin(a) * ln / 2, 0.30),
                         ln, 0.105, 1.44, a + math.pi, mats['timber'],
                         segments=5, tip=0.085))
    # High enough to clear the kerb -- the hero camera looks slightly UP at
    # this fire from ninety metres, so a bed down among the stones is a bed
    # nobody ever sees.
    out += fire_bed('bnf_bed', 0.44, 0.26, (0, 0, 0.24), mats, seed=13)
    out += embers('bnf_ember', (0, 0, 0.470), 0.40, 6, mats, seed=23, size=1.7)
    for i, (h, r, ln, bg) in enumerate((
            (0.86, 0.19, 0.10, 0.90), (0.58, 0.15, 0.42, 2.40),
            (0.92, 0.18, 0.06, 4.05), (0.48, 0.13, 0.48, 5.30),
            (0.72, 0.16, 0.24, 3.10), (0.38, 0.11, 0.56, 1.70))):
        d = (0.14, 0.30, 0.08, 0.34, 0.21, 0.38)[i]
        out.append(shard('bnf_flame%d' % i,
                         (math.cos(bg + 0.7) * d, math.sin(bg + 0.7) * d, 0.470),
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
                                     (0.032, 0.032, 0.222),
                                     loc=(sx * 0.084, sy * 0.084, 0.137)),
                             mats['iron']))
    # Horn, not glass: set inside the frame, and the only emissive part.
    #
    # Pass one gave the panes 0.146 of a 0.20 frame and it photographed as a
    # glazed box -- exactly the modern lantern the brief forbids. Narrower
    # panes, heavier corner posts, and a mid-rail across each pane: the rail is
    # what says a sheet of scraped horn pegged into ironwork.
    for k, (sx, sy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        size = (0.118, 0.010, 0.186) if sy else (0.010, 0.118, 0.186)
        out.append(paint(lib.box('ltn_pane%d' % k, size,
                                 loc=(sx * 0.086, sy * 0.086, 0.137)),
                         mats['tallow']))
        rail = (0.132, 0.011, 0.017) if sy else (0.011, 0.132, 0.017)
        out.append(paint(lib.box('ltn_rail%d' % k, rail,
                                 loc=(sx * 0.092, sy * 0.092, 0.148)),
                         mats['iron']))
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
    # Sunk into the bowl, not filling it: pass one made this a flat disc the
    # full width of the rim and the cresset photographed as a bowl of custard.
    out += fire_bed('crs_bed', 0.076, 0.044, (0, -0.235, 0.348), mats, seed=3)
    out += embers('crs_ember', (0, -0.235, 0.382), 0.052, 3, mats, seed=31,
                  size=0.32)
    for i, (h, r, ln, bg) in enumerate(((0.118, 0.044, 0.12, 0.5),
                                        (0.076, 0.034, 0.50, 2.9),
                                        (0.096, 0.038, 0.28, 4.7),
                                        (0.058, 0.028, 0.62, 1.6))):
        out.append(shard('crs_flame%d' % i,
                         (-math.cos(bg) * 0.042, -0.235 + math.sin(bg) * 0.042,
                          0.402),
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
    # Arm, brace and an UPTURNED hook. Pass one had a bare horizontal bar with
    # a stub hanging off it and the head of the post read as a tap.
    out.append(paint(lib.box('lmp_arm', (0.046, 0.420, 0.046),
                             loc=(0, -0.190, 2.270)), mats['iron']))
    out.append(paint(lib.box('lmp_brace', (0.032, 0.032, 0.280),
                             loc=(0, -0.150, 2.100), rot=(0.87, 0, 0)),
                     mats['iron']))
    out.append(paint(lib.box('lmp_hook', (0.032, 0.032, 0.135),
                             loc=(0, -0.375, 2.210)), mats['iron']))
    out.append(paint(lib.box('lmp_hooktip', (0.030, 0.070, 0.030),
                             loc=(0, -0.348, 2.158)), mats['iron']))
    out.append(paint(lib.box('lmp_cap', (0.208, 0.208, 0.060), loc=(0, 0, 2.370),
                             taper=0.55), mats['iron']))
    return out


# ---------------------------------------------------------------- plumes

def plume(mats, name, height, width, points, straight=0.45, bend_deg=30.0,
          throat=0.50, flatten=0.58, lean_deg=4.0, fade=0.14):
    """A smoke column. `lib.sweep`, not `profile`, because the section has to
    change SHAPE and not only size: a plume on a clear cold night rises, meets
    the inversion, and flattens into an ellipse rather than going on climbing.

    Rises near vertical for `straight` of its height, then bends `bend_deg` off
    vertical and drifts north-east -- the same south-west wind that leans the
    hawthorns and the keep banner. Widens from a chimney-sized `throat` to the
    full width. No emission at all: it is lit by the moon behind it and by the
    fires underneath it.

    Three things here are fixes, and each one has a render behind it:

    `lean_deg` is not decoration. `lib.sweep` frames each section against world
    up, so a path that is EXACTLY vertical makes the cross product degenerate
    and the framing falls back to an arbitrary axis; the moment the path tilts,
    the frame swings 45 degrees between two consecutive rings and puts a hard
    pinch in the column. Pass one had a visible bright kink at a third height
    in both plumes for exactly that reason. A four-degree lean from the flue --
    which is true of any real plume anyway -- keeps the frame continuous.

    smooth=False because `lib.sweep` defaults to smooth shading whatever
    SMOOTH_DEFAULT says, and a smooth-shaded 8-sided tube photographed as a
    bent rubber sleeve. The art direction asks for faceted, and faceted is also
    what makes it read as vapour rather than a solid.

    close=False because a capped tube has an end, and smoke does not. The
    bottom sits inside the chimney, and over the last `fade` of the path the
    section shrinks away so the top pinches out instead of being chopped off
    flat -- pass two ended on a full-width open ring and the render showed a
    column that had been cut through with a knife."""
    drift = (math.cos(math.radians(45)), math.sin(math.radians(45)))   # NE
    theta_0 = math.radians(lean_deg)
    theta_max = math.radians(bend_deg)

    def theta(t):
        u = (t - straight) / (0.92 - straight)
        u = min(1.0, max(0.0, u))
        return theta_0 + (theta_max - theta_0) * (u * u * (3 - 2 * u))

    # The section is a flattened ellipse, so at the mouth its own half-depth
    # hangs below the first path point once the path leans. Lift the whole
    # thing by exactly that, or the export report calls a 2 cm rim a sunk model.
    z0 = (throat / 2.0) * math.sin(theta_0)
    path, sections = [], []
    s = 0.0
    prev_z = 0.0
    for i in range(points):
        t = i / (points - 1.0)
        z = height * t + z0
        s += math.tan(theta(t)) * (z - prev_z)
        prev_z = z
        path.append((drift[0] * s, drift[1] * s, z))
        # t**0.55, not t**0.72: the first pass expanded late and the column
        # came out as a narrow stalk under a fat bulb -- a thumb, not smoke.
        w = throat + (width - throat) * (t ** 0.55)
        if t > 1.0 - fade:
            u = (t - (1.0 - fade)) / fade
            w *= 1.0 - 0.62 * u * u
        a = w / 2.0
        b = a * (1.0 - (1.0 - flatten) * (t ** 1.1))
        sections.append([(math.cos(k / 8.0 * TAU) * a,
                          math.sin(k / 8.0 * TAU) * b) for k in range(8)])
    return [paint(lib.sweep(name, path, sections, close=False, smooth=False),
                  mats['vapour'])]


# ---------------------------------------------------------------- lit openings

def pane(mats, name, w, t, h, mat='tallow', mullions=0, transom=None,
         bar='stone', bw=0.085):
    """A lit opening plate. Thin in Y, emitting toward -Y, base on z = 0.

    Twelve triangles and one of the three most important assets in the scene:
    it is the difference between a black hole in a wall and a room with people
    in it.

    The mullion is not decoration and it is not optional on the wide ones. Put
    the whole kit in one frame at the intensities of ART-DIRECTION 3.6 and the
    lit windows out-glow the bonfire, because a 1.40 x 2.10 plate at 1.6 is
    2.9 square metres of light against maybe 0.3 for the heart of the fire --
    area beats intensity. A dark stone mullion and transom across it takes back
    a fifth of the bright area, breaks a flat rectangle into four lights, and
    is what a two-light window in a thirteenth-century keep actually is. The
    same trick as the lantern's mid-rail, and it works for the same reason."""
    out = [paint(lib.box(name, (w, t, h), loc=(0, 0, h / 2)), mats[mat])]
    for i in range(mullions):
        x = w * ((i + 1) / float(mullions + 1) - 0.5)
        out.append(paint(lib.box('%s_mull%d' % (name, i), (bw, t + 0.05, h),
                                 loc=(x, -0.020, h / 2)), mats[bar]))
    if transom:
        out.append(paint(lib.box('%s_tran' % name, (w, t + 0.05, bw * 0.85),
                                 loc=(0, -0.020, h * transom)), mats[bar]))
    return out


def arch_plate(name, w, h, t, mat, spring=0.62, steps=6):
    """A round-headed opening: straight jambs to the springing, then a
    semicircle. `spring` is the fraction of the height the arch starts at.

    A rectangle where an arch belongs reads as a letterbox cut in a wall, and
    both the places this is used -- an oven mouth and the far end of a barrel-
    vaulted gate passage -- are arches in the castle it has to sit against."""
    hw = w / 2.0
    z_spring = h * spring
    outline = [(-hw, 0.0), (hw, 0.0), (hw, z_spring)]
    for k in range(1, steps):
        a = k / float(steps) * math.pi
        outline.append((hw * math.cos(a), z_spring + (h - z_spring) * math.sin(a)))
    outline.append((-hw, z_spring))
    return [paint(lib.prism(name, outline, t, plane='xz'), mat)]


def oven_mouth(mats):
    """The bake-house oven's round-headed mouth, 0.55 by 0.70, in `ember` --
    the deepest warm step, and the only source in the scene that is neither
    tallow nor fire."""
    return arch_plate('oven_mouth', 0.550, 0.700, 0.060, mats['ember'])


def shutter(mats):
    """0.72 by 2.10, hinged on the Z axis and authored flat in the wall plane so
    the scene can swing the two of them to different angles.

    This is the whole trick of group 4. A bare lit rectangle reads as a decal;
    a lit rectangle with a timber shutter swung two thirds across it, throwing
    a hard edge over the light, reads as a window in a building somebody lives
    in. Four boards with real gaps between them, two ledges behind, two strap
    hinges in front."""
    out = []
    # 22 mm gaps and alternating thickness, because pass one used 10 mm and the
    # four boards photographed as one slab with scored lines on it. A shutter
    # that reads has light coming between the boards.
    for i in range(4):
        t = 0.030 if i % 2 else 0.024
        out.append(paint(lib.box('sht_board%d' % i, (0.158, t, 2.100),
                                 loc=(0.090 + i * 0.180, 0.006 + t / 2 - 0.012,
                                      1.050)),
                         mats['timber']))
    for k, z in enumerate((0.330, 1.760)):
        out.append(paint(lib.box('sht_ledge%d' % k, (0.706, 0.026, 0.155),
                                 loc=(0.358, 0.034, z)), mats['timber']))
        out.append(paint(lib.box('sht_strap%d' % k, (0.480, 0.014, 0.070),
                                 loc=(0.240, -0.014, z)), mats['iron']))
        out.append(paint(lib.box('sht_pintle%d' % k, (0.052, 0.052, 0.105),
                                 loc=(0.006, -0.014, z)), mats['iron']))
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
    # Two lights and a transom on the keep windows, two lights on the hall and
    # the chapel, a bare slit on the arrow loop, and a round head on the
    # passage -- which is not a window at all but the far end of a barrel
    # vault seen down a dark tunnel.
    'pane_window': lambda m: pane(m, 'pane_window', 1.40, 0.06, 2.10,
                                  mullions=1, transom=0.66),
    'pane_hall': lambda m: pane(m, 'pane_hall', 1.05, 0.10, 1.40,
                                mullions=1, bar='timber', bw=0.070),
    'pane_loop': lambda m: pane(m, 'pane_loop', 0.28, 0.06, 1.45),
    'pane_lancet': lambda m: pane(m, 'pane_lancet', 1.20, 0.10, 2.40,
                                  mullions=1, bw=0.095),
    'pane_passage': lambda m: arch_plate('pane_passage', 1.90, 2.60, 0.06,
                                         m['tallow'], spring=0.66),
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
