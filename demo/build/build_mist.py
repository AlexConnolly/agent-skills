# Asset group 7 of "Nightfall at the March Castle": the ground mist sheets.
#
#   blender --background --python build_mist.py -- [piece ...]
#
# Brief: briefs/mist.md, written before this file and committed verbatim.
# Spec:  ART-DIRECTION.md sections 2 (palette), 3.3 (fog, and why mist is not
#        it), 5 group 7, and 6.1 (the levels these pool in).
#
# THE ONE RULE THIS FILE EXISTS TO OBEY
#
# These four pieces are nothing but alpha, and ART-DIRECTION 0.3(a) records
# exactly how that goes wrong: build_castle.py asks its hearth puffs for
# alpha=0.34, the texture pass rebuilds a Principled with no alpha channel, and
# the shipped .glb has three clusters of solid pale-grey cubes floating over
# the roofs. So:
#
#   * the material sets blend_method AND the Alpha socket, because the glTF
#     exporter reads alphaMode off blend_method and baseColorFactor[3] off the
#     socket, and either one alone ships a lie;
#   * nothing in this group ever goes through skin_*.py -- there is no bake,
#     no unwrap and no image, and there is nothing here a texture could add;
#   * the proof is `python art_mist/inspect_glb.py <file>` reading the material
#     JSON back out of the container. The Blender viewport is not evidence.
#
# WHERE THE LOOK ACTUALLY LIVES. The camera is at eye height on a knoll and
# every one of these is read between two and seven degrees above the
# horizontal (the arithmetic is in art_mist/artconfig.py). A horizontal sheet
# at five degrees is almost entirely its own edge, so the plan shape -- the
# thing a top view shows and the thing that is easiest to model -- is the part
# nobody ever sees. What is left is two things, and they are what this file
# spends its triangles and its vertex data on:
#
#   1. THE SKYLINE OF THE TOP SURFACE. Undulated in two low frequencies so the
#      upper edge is a soft lumpy band rather than the straight line a flat
#      slab draws.
#   2. THE VERTICAL ALPHA GRADIENT, per vertex, in COLOR_0. glTF multiplies
#      COLOR_0 into baseColorFactor including its alpha, and Three.js honours
#      the fourth component, so a sheet can be dense in its first quarter metre
#      and gone at the crown without a texture, a UV or a bake. A slab at one
#      constant alpha is a grey plane, which is failure mode two in the brief.
#
# THE RIM FADE IS 85 PER CENT, and it was 45 until the orbit camera was
# rendered. The two cameras this asset is read from want opposite things. From
# the hero lens at eye height a sheet is seen edge-on, its plan outline
# collapses to nothing, and a hard rim costs you nothing -- and a strong fade
# actively hurts, because a low ray crosses the sheet near its rim and fading
# the rim thins the FOOT of the mist, which is the one part that should be
# solid. From the intro move and the orbit, which stand above the ward datum
# and look DOWN, the plan outline IS the silhouette, and at 45 per cent it came
# back in x2_orbit_mist.png as pale plates with straight edges lying on the
# grass. The down-looking camera wins because it is the one that can actually
# see this asset at all: measured against the built terrain, the hero still
# shows group 7 only as a 2-level wash in the bottom tenth of the frame.
#
# MIST IS NOT THE FOG. Section 3.3 puts FogExp2(0x16243A, 0.0045) on the whole
# scene, which is a distance wash and cannot make one hollow thicker than the
# field around it. These sheets are the local pooling only. They are built to
# sit UNDER that fog, not to stand in for it.
#
# AXES AND ORIGINS. Blender, Z-up, metres. Every piece is authored with its
# lowest point on z = 0 and its anchor at the world origin, so the export
# report's ground-contact line is a real check on all four.
#
# The bottom 0.40 of that height is HEM and is meant to be buried, so an
# instance is seated `0.40 x depth_scale x height` INTO the terrain rather
# than laid on top of it: 0.48 m for mist_sheet_a at full depth, 0.16 m for a
# wisp. That does two jobs -- it lets a flat slab bed into undulating ground
# instead of hanging off it at one end, and it keeps the underside from
# being coplanar with the terrain, which z-fights once depthWrite is off.
# The visible depth of a sheet is therefore 0.60 of its box: 0.72 m for
# mist_sheet_a at depth scale 1.0, and 1.04 m at the 1.45 the deepest
# instance uses -- knee to mid-thigh on a 1.75 m figure.
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'art_mist'))
sys.path.insert(1, os.path.join(HERE, 'art'))

import bpy                                          # noqa: E402
import artconfig as cfg                             # noqa: E402
import lib                                          # noqa: E402


# ---------------------------------------------------------------- palette

MIST_PALE = 0x5E7488        # ART-DIRECTION 2, the cool mass
SHEET_ALPHA = 0.11          # ART-DIRECTION 5 group 7, the loader's opacity


# ---------------------------------------------------------------- material

def mist_material():
    """One material for all four pieces, rebuilt after every lib.reset().

    Three things have to be true at once and each is checked in the glb:

      baseColorFactor  = mist-pale, alpha 0.11
      alphaMode        = BLEND        (from blend_method)
      COLOR_0          = VEC4, alpha carrying the per-vertex gradient

    The multiply nodes are there so the exporter folds the constants into
    baseColorFactor and leaves COLOR_0 as a clean 0..1 mask. Wiring the vertex
    colour straight into Base Color would work too, but then the exporter
    writes baseColorFactor [1,1,1,a] and the mist's colour lives only in the
    vertex data -- so any viewer that drops COLOR_0 draws it white, and white
    is the one thing section 2 forbids."""
    m = lib.hexmat('mist', MIST_PALE, rough=1.0, alpha=SHEET_ALPHA)
    if m.node_tree.nodes.get('mist_vcol'):
        return m
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']

    vcol = nt.nodes.new('ShaderNodeVertexColor')
    vcol.name = 'mist_vcol'
    vcol.layer_name = 'Col'
    vcol.location = (-620, -120)

    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    tint.inputs[6].default_value = lib.srgb(MIST_PALE)
    tint.location = (-380, 0)
    nt.links.new(vcol.outputs['Color'], tint.inputs[7])
    nt.links.new(tint.outputs[2], bsdf.inputs['Base Color'])

    fade = nt.nodes.new('ShaderNodeMath')
    fade.operation = 'MULTIPLY'
    fade.inputs[1].default_value = SHEET_ALPHA
    fade.location = (-380, -220)
    nt.links.new(vcol.outputs['Alpha'], fade.inputs[0])
    nt.links.new(fade.outputs['Value'], bsdf.inputs['Alpha'])

    # lib.material() already set blend_method for alpha < 1. Say it again
    # anyway -- this is the single property the glTF exporter turns into
    # alphaMode, and this file exists because it was once wrong.
    m.blend_method = 'BLEND'
    # EEVEE Next only: true alpha blending rather than a stochastic dither.
    # Carries no glTF meaning; it is here so the contact sheet is not noise.
    if hasattr(m, 'surface_render_method'):
        m.surface_render_method = 'BLENDED'
    m.show_transparent_back = True
    m.use_backface_culling = False
    return m


# ---------------------------------------------------------------- noise

def waves(width, cycles=2.4):
    """Frequencies for `wobble`, in radians per metre, for a piece `width`
    metres across.

    Stated as cycles across the piece rather than as a wavelength because that
    is the thing being decided: two and a half rises and falls across a sheet
    is a lumpy skyline, one is a dome and six is corduroy. It also means the
    9 m wisp and the 44 m pool get the same look instead of the same numbers."""
    k = 2.0 * math.pi / max(1e-6, width)
    return k * cycles, k * cycles * 0.63


def wobble(x, y, seed, k1, k2):
    """Smooth two-frequency noise from the coordinates, roughly -1.5 to 1.5.

    Deterministic, so a rebuild is the same mist, and continuous, so unlike a
    hash of the position it cannot tear the top surface into spikes."""
    return (math.sin(x * k1 + seed * 1.7) * math.cos(y * k2 + seed * 2.3)
            + 0.55 * math.sin(x * k2 * 2.1 - y * k1 * 1.6 + seed * 0.9))


def lobed(theta, lobes, seed):
    """Plan radius as a fraction of the nominal, for a convex-ish outline with
    `lobes` bulges and no two the same size."""
    return (1.0
            + 0.150 * math.sin(lobes * theta + seed)
            + 0.085 * math.sin(2.0 * theta + seed * 2.3)
            + 0.055 * math.sin(3.0 * theta - seed * 0.7))


# ---------------------------------------------------------------- alpha

def _smoothstep(a, b, t):
    t = max(0.0, min(1.0, (t - a) / max(1e-6, b - a)))
    return t * t * (3.0 - 2.0 * t)


def paint_alpha(obj, radial, seed, k1, k2, floor=0.10, rim=0.45):
    """Write COLOR_0: white RGB, and an alpha that is the mist's density.

    `radial(co) -> 0..1` is distance from the piece's own spine, 1 at the
    outline, and is the only per-piece part -- a pool measures it from a
    centre and a ribbon from its path.

      vertical   full density through the lower half, then falling away
                 fast to `floor` at the crown. This is the gradient that
                 makes an edge-on sheet read as a bank of air rather than
                 a plane, and the SHAPE of it decides the density of the
                 whole asset: (1 - t)**1.35 was tried first and it is down
                 to 0.62 by a third of the way up, which took the mean
                 vertex alpha to 0.35 and the effective opacity of a sheet
                 to 0.11 x 0.35 = 0.039 -- a third of what ART-DIRECTION 5
                 group 7 asks for, and a measured +0.0006 on the frame.
                 1 - t**2.2 holds 0.93 at a third of the way up and still
                 reaches the floor at the crown.
      rim        a mild fade over the outer fifth so the plan outline is never
                 a drawn line. Mild on purpose: see the header.
      patch      low-frequency variation so the wash is not uniform, which is
                 what turns two overlapping instances into a bank."""
    me = obj.data
    zs = [v.co.z for v in me.vertices]
    lo, hi = min(zs), max(zs)
    span = max(1e-6, hi - lo)
    layer = me.color_attributes.get('Col')
    if layer is None:
        layer = me.color_attributes.new(name='Col', type='FLOAT_COLOR',
                                        domain='POINT')
    for i, v in enumerate(me.vertices):
        t_z = (v.co.z - lo) / span
        t_r = radial(v.co)
        vert = floor + (1.0 - floor) * (1.0 - t_z ** 2.2)
        edge = 1.0 - rim * _smoothstep(0.74, 1.02, t_r)
        patch = 0.72 + 0.28 * (0.5 + 0.5 * wobble(v.co.x, v.co.y, seed + 4.0,
                                                  k1 * 0.7, k2 * 1.3))
        a = max(0.0, min(1.0, vert * edge * patch))
        layer.data[i].color = (1.0, 1.0, 1.0, a)
    return layer


def soften(obj, angle=30.0):
    """Smooth the domed top and keep the rim corner hard.

    ART-DIRECTION 5 group 7 says flat shaded and for every other asset in this
    scene that is right, but a translucent surface breaks the rule: the alpha
    is per-vertex and interpolates, so on a flat-shaded dome the only thing
    that steps at a polygon boundary is the normal, and it steps alone. In
    hero_stretch_ditch.png that showed as hard triangular wedges across the top
    of the ditch sheets -- 30 segments over 44 m is a 4.6 m facet, which at
    100 m is 1.2 degrees of hard edge in something that should have none.

    shade_auto's threshold is what keeps this from becoming a balloon: the top
    rings meet at about 4 degrees and smooth, the rim-to-skirt corner is 86 and
    stays sharp, so the sheet still has a defined foot where it meets the
    ground."""
    return lib.shade_auto(obj, angle_deg=angle)


# ---------------------------------------------------------------- fitting

def fit(obj, w, d, h):
    """Scale the mesh so its bounding box is exactly `w x d x h` with its
    underside on z = 0, and hand back the same map for other points.

    The lobe and undulation functions do not have a knowable extent, so the
    sizes in ART-DIRECTION 5 are held here rather than hoped for. The returned
    map is what lets a ribbon measure distance from its own path after the
    mesh has been squashed to the spec box."""
    vs = obj.data.vertices
    lo = [min(v.co[i] for v in vs) for i in range(3)]
    hi = [max(v.co[i] for v in vs) for i in range(3)]
    k = [w / max(1e-6, hi[0] - lo[0]),
         d / max(1e-6, hi[1] - lo[1]),
         h / max(1e-6, hi[2] - lo[2])]
    cx = (lo[0] + hi[0]) / 2.0
    cy = (lo[1] + hi[1]) / 2.0
    for v in vs:
        v.co.x = (v.co.x - cx) * k[0]
        v.co.y = (v.co.y - cy) * k[1]
        v.co.z = (v.co.z - lo[2]) * k[2]

    def plan(x, y):
        return ((x - cx) * k[0], (y - cy) * k[1])
    plan.k = k
    return plan


# ---------------------------------------------------------------- the pools

# Radius and height up the profile, as fractions of the nominal radius and
# of the height ABOVE the ground line -- so z runs -0.3333 to 1.0 and the
# negative part is hem (see HEM_FRACTION below). Closed loop: the last point
# and the first are both on the axis, so the quad between them collapses and
# revolve() drops it -- what comes out is a solid slab with a domed top, a
# short outer skirt and a flat underside.
#
# The skirt is the reason for the (1.0, 0) -> (1.0, 0.20) step. Without it the
# sheet meets the ground at a knife edge and, at five degrees, the first thing
# you see of it is a smear; with it there is a low dense band at the foot,
# which is what beds the mist into the hollow.
#
# Four points off the axis, so the vertical alpha gradient has four levels to
# interpolate between. Over 1.2 m at 22 px/m that is a stop every nine
# pixels, which is enough; a fifth ring was tried and cost 60 triangles for a
# gradient nobody could see.
POOL_OUTLINE = [(0.00, -0.6667),
                (1.06, -0.6667),
                (1.00, 0.20),
                (0.62, 0.74),
                (0.00, 1.00)]

WISP_OUTLINE = [(0.00, -0.5000),
                (1.06, -0.5000),
                (1.00, 0.28),
                (0.68, 0.74),
                (0.00, 1.00)]

# HEM_FRACTION of every piece's height is below its nominal ground line and is
# meant to be buried. It is not padding: a mist sheet is a FLAT slab, so on a
# slope that falls further than its own depth across its own span it stops
# touching the ground at one end and starts floating -- which is failure mode
# two, word for word, and it is what hero_diff.png showed on the first pass
# against the real terrain, a 26 m sheet_c hanging over the platform batter
# with sky visible under its far edge. Four fifths of a metre of hem lets an
# instance bed into ordinary ground undulation instead.
#
# 0.40 of the box, measured against the real terrain rather than guessed. A
# quarter was tried first and left sixteen of the twenty instances with air
# under them: the outfield's own undulation is plus or minus 1.2 m per
# ART-DIRECTION 6.3, and a 44 m slab 1.2 m deep spans several metres of that.
# At 0.40 the visible depth of mist_sheet_a is 0.72 m -- knee deep on a
# 1.75 m figure, which is the shallow end of what the brief asks for, and the
# instance depth scales in the placement table take the deeper ones back up.
#
# It still does NOT rescue a sheet put on a real slope. The fix for a batter
# is not to lay a pool on it, and mist_scene.py's `seating` is what catches
# that: it reports the largest air gap under each instance, on a grid that
# respects the instance's yaw.
HEM_FRACTION = 0.6667 / 1.6667


def pool(name, w, d, h, segments, lobes, seed, outline=None, sag=0.34,
         tear=0.10, cycles=2.4, rim=0.85, floor=0.14):
    """A lobed slab that pools: revolve a profile, pull the plan into lobes,
    then undulate the top.

    `sag` is how much of the depth the top surface rises and falls by, as a
    fraction -- the whole of the skyline, and the only thing that stops this
    reading as a dome. `tear` breaks the plan outline so the skirt is not a
    turned edge.

    The undulation is scaled by height above the underside, so the flat bottom
    stays flat and on z = 0; the plan distortion is not, so the skirt stays
    vertical instead of leaning.

    The plan is fitted to metres BEFORE the top is undulated, so the noise
    frequencies are cycles across the real sheet. Undulating first would make
    the 9 m wisp and the 44 m pool wobble at the same wavelength in unit space
    and therefore at wildly different wavelengths on the ground."""
    # A lobe needs three angular samples to read as a bulge. At two it is a
    # zigzag: the first build of mist_sheet_a asked twelve lobes of twenty-four
    # segments -- exactly Nyquist -- and top.png came back a cog with twelve
    # sharp points and needle spits at both ends of the silhouette. The tear
    # term aliased worse still, at 20.4 cycles against 24 samples.
    if lobes * 3 > segments:
        raise SystemExit('%s: %d lobes needs at least %d segments, has %d'
                         % (name, lobes, lobes * 3, segments))
    obj = lib.revolve(name, outline or POOL_OUTLINE, segments=segments,
                      close_outline=True, smooth=False)
    tear_k = max(2.0, round(lobes * 0.55))
    for v in obj.data.vertices:
        if math.hypot(v.co.x, v.co.y) > 1e-6:
            th = math.atan2(v.co.y, v.co.x)
            k = lobed(th, lobes, seed) + tear * math.sin(tear_k * th
                                                         + seed * 3.1)
            v.co.x *= k
            v.co.y *= k
    fit(obj, w, d, 1.0)

    k1, k2 = waves(w, cycles)
    for v in obj.data.vertices:
        v.co.z += sag * v.co.z * wobble(v.co.x, v.co.y, seed, k1, k2)
    fit(obj, w, d, h)

    half = (w / 2.0, d / 2.0)
    paint_alpha(obj, lambda co: math.hypot(co.x / half[0], co.y / half[1]),
                seed, k1, k2, floor=floor, rim=rim)
    obj.data.materials.append(mist_material())
    soften(obj)
    return obj


# ---------------------------------------------------------------- the ribbons

# The ribbon section, lateral and up, as fractions of half-width and depth.
# Eight points: a flat underside of three, then up one flank, over the crown
# and down the other. Four distinct heights, which is what the alpha gradient
# has to interpolate between over 0.9 m -- 47 pixels at the ditch's distance.
RIBBON_SECTION = [(-1.00, 0.00), (0.00, 0.00), (1.00, 0.00),
                  (0.82, 0.34), (0.46, 0.80),
                  (0.00, 1.00),
                  (-0.46, 0.80), (-0.82, 0.34)]


def ribbon(name, w, d, h, path, widths, seed, sag=0.30, steps=3, cycles=2.0,
           flatten=0.70, rim=0.85, floor=0.14):
    """A drawn-out sheet that follows something: the ditch, a hedge bank.

    `path` is control points in plan, run through catmull so the line is
    smooth; `widths` is one half-width per control point, interpolated along
    it, and it is what makes the thing swell and thin instead of being a hose.
    Both ends taper to nearly nothing so the sheet is torn rather than cut.

    `flatten` uncouples depth from width. lib.profile()'s `scales` multiplies
    the whole section, so a ribbon six metres wide in the middle and one metre
    wide at the ends would also be six times DEEPER in the middle -- a fat
    lens, not a sheet. This pulls the height back toward constant: depth ends
    up proportional to width ** (1 - flatten), so at 0.70 a stretch a quarter
    the width is still two thirds the depth, and only the torn ends really
    thin out. lib.profile() lays its vertices out ring by ring in path order
    and does not weld them, which is what makes the station recoverable from
    the vertex index."""
    line = lib.catmull(path, n=steps)
    n = len(line)
    scales = []
    for i in range(n):
        t = i / float(n - 1)
        u = t * (len(widths) - 1)
        j = min(len(widths) - 2, int(u))
        f = u - j
        k = widths[j] * (1 - f) + widths[j + 1] * f
        # Torn ends: the taper is on top of the profile, not instead of it.
        k *= _smoothstep(0.0, 0.18, t) * _smoothstep(0.0, 0.18, 1.0 - t)
        scales.append(max(0.06, k))
    obj = lib.profile(name, list(RIBBON_SECTION),
                      [(p[0], p[1], 0.0) for p in line],
                      close=True, smooth=False, scales=scales)

    nsec = len(RIBBON_SECTION)
    ref = max(scales)
    for i, v in enumerate(obj.data.vertices):
        k = scales[min(len(scales) - 1, i // nsec)]
        v.co.z *= (ref / k) ** flatten
    plan_a = fit(obj, w, d, 1.0)

    k1, k2 = waves(w, cycles)
    for v in obj.data.vertices:
        v.co.z += sag * v.co.z * wobble(v.co.x, v.co.y, seed, k1, k2)
    plan_b = fit(obj, w, d, h)

    # Distance from the path, normalised by the local half-width, so the rim
    # fade follows the ribbon instead of a bounding ellipse. The path is put
    # through BOTH maps the mesh went through, which is why fit() returns one
    # -- the second is very nearly the identity in plan, but "very nearly" is
    # how a spine ends up half a metre off its own sheet.
    spine = [plan_b(*plan_a(p[0], p[1])) for p in line]
    grow = 0.25 * (abs(plan_a.k[0]) + abs(plan_a.k[1])) * \
        (abs(plan_b.k[0]) + abs(plan_b.k[1]))
    reach = [max(0.4, s * grow) for s in scales]

    def radial(co):
        best = 9e9
        for (qx, qy), rr in zip(spine, reach):
            t = math.hypot(co.x - qx, co.y - qy) / rr
            if t < best:
                best = t
        return best

    paint_alpha(obj, radial, seed, k1, k2, floor=floor, rim=rim)
    obj.data.materials.append(mist_material())
    soften(obj)
    return obj


# ---------------------------------------------------------------- the pieces

def mist_sheet_a():
    """44 x 30 x 1.2, the hollow NE of the castle (ART-DIRECTION 6.1 puts its
    floor at y = -6.5). The big one: twelve lobes, and a top that rises and
    falls by 0.4 m so its edge-on skyline is a band 9 px deep at 22 px/m
    rather than a ruled line. Ten lobes on thirty segments -- three angular
    samples each, which is the minimum that reads as a bulge rather than a
    tooth."""
    return pool('mist_sheet_a', 44.0, 30.0, 1.20, segments=30, lobes=10,
                seed=1.0, sag=0.36)


def mist_sheet_b():
    """32 x 22 x 0.9, in the ditch, following the ring.

    ART-DIRECTION gives the box as 32 x 22 and also says it follows the ditch,
    and those pull apart: the ditch ring is about 55 m in radius, so 32 m of it
    bends by only 2.4 m and a piece curved enough to fill 22 m of Y would cut
    the corner off every arc it was laid on. Resolved in favour of following
    the ditch -- an arc of about 30 m radius, sagitta 4.4 m, and the rest of
    the width comes from the sheet itself swelling to 6 m half-width in the
    middle. 32.0 x 21.6 as built."""
    r = 30.0
    pts = []
    for i in range(5):
        a = math.radians(-32.0 + 16.0 * i)
        pts.append((r * math.sin(a), r * math.cos(a) - r * 0.86, 0.0))
    return ribbon('mist_sheet_b', 32.0, 22.0, 0.90, pts,
                  widths=(2.6, 5.2, 6.0, 4.6, 2.8), seed=2.0, sag=0.30)


def mist_sheet_c():
    """26 x 18 x 0.6, along the treeline and the field boundaries.

    Lower and thinner than the other two because it is lying against a hedge
    bank rather than filling a hollow, and kinked rather than curved -- a field
    boundary turns a corner, a ditch does not. The kink is what puts 18 m in Y
    on a sheet only 5 m wide."""
    pts = [(-13.0, -4.2, 0.0), (-4.5, 2.6, 0.0),
           (3.0, 4.9, 0.0), (12.0, -1.0, 0.0)]
    return ribbon('mist_sheet_c', 26.0, 18.0, 0.60, pts,
                  widths=(1.8, 3.4, 3.0, 2.0), seed=3.0, sag=0.26)


def mist_wisp():
    """9 x 5 x 0.4, the near foreground under 30 m.

    Ankle deep and ragged: at 67 px/m its whole depth is 27 pixels, so it is
    read almost entirely as a torn top edge over the ruts. Fewer segments and a
    harder tear than the pools -- this is the one piece close enough for a
    turned outline to show. Five lobes rather than the pools' ten, because at
    sixteen segments anything more aliases into a star.

    Its alpha is tuned differently from the pools, and this is the one place
    the two really diverge. A pool 120 m away is read at two degrees and is
    almost purely its own edge; a wisp 20 m away is read at eight to eleven
    degrees, and 9 m of plan foreshortened by sin(9 deg) still projects taller
    than 0.4 m of depth -- so a wisp is seen mostly from ABOVE, as its top
    surface, and its plan outline IS its silhouette. The first build gave it
    the pools' 45 per cent rim fade and it came back in the difference image
    as a hard-edged pale plate lying on the grass, which is failure mode two
    almost exactly. Ninety per cent takes the outline to nothing and the lower
    floor takes the crown down with it."""
    return pool('mist_wisp', 9.0, 5.0, 0.40, segments=16, lobes=5, seed=5.0,
                outline=WISP_OUTLINE, sag=0.44, tear=0.16, cycles=1.8,
                rim=0.90, floor=0.06)


PIECES = {
    'mist_sheet_a': mist_sheet_a,
    'mist_sheet_b': mist_sheet_b,
    'mist_sheet_c': mist_sheet_c,
    'mist_wisp': mist_wisp,
}


# ---------------------------------------------------------------- placement
#
# Twenty instances, in Three.js metres, as the piece's ANCHOR -- the centre of
# its underside, which this script authors at the local origin. `sink` is how
# far the anchor goes BELOW the terrain height at that point (see the header:
# a face coplanar with the ground z-fights once depthWrite is off), `yaw` is
# about Three.js +Y, and `scale` is (plan, depth) so a sheet can be stretched
# in plan without getting deeper than the brief allows.
#
# Every top stays under 2.4 m above its own local ground, per ART-DIRECTION 5
# group 7 -- with the deepest instance at 1.2 x 1.55 = 1.86 m of depth and a
# 0.3 m sink, the worst case is 1.56 m, which is chest on a 1.75 m figure and
# well clear of a lens at 1.7 m. The camera can never be inside one.
#
# Ground heights come from terrain.json (ART-DIRECTION 6.3), sampled by the
# loader. Nothing here assumes a flat world.
#
#  piece          Three.js (x, z)   yaw   plan  depth  sink   where
#  -------------- ----------------- ----- ----- ------ -----  -----------------
#  mist_sheet_a   ( 26, -66)          18   1.00  1.00   0.30  the hollow, core
#  mist_sheet_a   ( 30, -74)         104   0.85  1.45   0.25  stacked on it,
#                                                             deeper and turned
#  mist_sheet_a   ( 18, -60)         -37   0.70  0.62   0.20  stacked, shallow
#  mist_sheet_a   ( 34, -88)         143   0.95  1.10   0.35  the hollow, far
#  mist_sheet_a   ( 16, -84)          62   1.10  0.80   0.25  the hollow, west
#  mist_sheet_b   ( 50,  24)         -90   0.90  1.00   0.30  ditch bank, 31 m,
#                                                             by the bridge
#  mist_sheet_b   ( 50,  12)         -96   1.00  1.45   0.25  stacked on it
#  mist_sheet_b   ( 49,   0)         -84   0.85  0.72   0.30  stacked, shallow
#  mist_sheet_b   ( 52, -38)         -30   0.75  1.15   0.20  ditch, NE
#  mist_sheet_b   ( 30, -54)          -6   0.65  0.80   0.30  ditch, N
#  mist_sheet_c   ( 46,  32)          34   1.20  0.90   0.20  field edge above
#                                                             the ditch
#  mist_sheet_c   ( 44,  20)         -64   1.00  1.20   0.20  the same boundary
#  mist_sheet_c   (-30,-150)          -6   0.90  0.80   0.15  treeline on the
#                                                             ridge, far N
#  mist_sheet_c   (-62,-172)          51   1.30  1.10   0.25  treeline, far NW
#  mist_wisp      ( 70,  38)          12   1.00  1.00   0.15  the knoll crest,
#                                                             9 m, under the
#                                                             wayside cross
#  mist_wisp      ( 68,  36)        -140   0.80  1.35   0.10  stacked on it
#  mist_wisp      ( 74,  34)          88   1.15  0.70   0.15  crest, S
#  mist_wisp      ( 66,  41)         -22   0.90  1.15   0.20  crest, N
#  mist_wisp      ( 72,  30)         160   1.05  0.90   0.15  the ruts, 15 m
#  mist_wisp      ( 63,  42)          40   0.70  0.60   0.10  a rag, 17 m
#
# EVERY NUMBER ABOVE WAS SET BY THE TERRAIN, NOT CHOSEN. Seating comes from
# bilinear sampling of docs/data/terrain.json -- ART-DIRECTION 6.3's single
# source of truth -- and visibility from ray-marching that same grid against
# the hero sight line (art_mist/mist_scene.py, `sees`). Both are printed by
# `blender --background --python art_mist/mist_scene.py`, per instance, so
# this table can be re-derived rather than trusted.
#
# WHAT THE HERO STILL CAN ACTUALLY SEE, and it is much less than it looks.
# The lens is at y = -1.0, the ward floor at 0.0, so the sight line grazing
# the platform RISES and never comes back down: no ground behind the castle is
# in the picture, however deep it is cut. Sweep the real grid for cells that
# are at once in frame, unoccluded, and below -4 m, and what comes back is one
# strip -- x 45..55, z -15..+35, the ditch's near bank at 30 to 47 m -- plus
# the knoll crest itself at 9 to 20 m. That is all of it.
#
# So: mist_sheet_b carries the still, three of its five stacked along that
# strip at 31, 39 and 47 m; mist_wisp carries the bottom band off the crest;
# mist_sheet_c takes the field edge just above the ditch. mist_sheet_a is read
# from the intro move's start position (92, 1.5, 52) -- 1.5 m ABOVE the ward
# floor, which is the 2.5 m that makes the hollow exist -- and from the top of
# the orbit, and all five of its instances stay in the hollow where the mist
# belongs rather than being dragged forward into a frame that has no room for
# a 44 m pool.
#
# STACKING IS NOT OPTIONAL, and this is the other thing the renders changed.
# Alpha blending does not accumulate with path length: a ray grazing a closed
# slab crosses exactly two surfaces whether it travels 2 m through it or 40,
# so an edge-on sheet is no denser than a face-on one and a bank made of ONE
# slab cannot be thicker in its middle. The density has to come from instances
# overlapping -- five sheets scattered across 100 m of hollow measured a
# +0.0001 lift on the frame, which is nothing; three stacked on the same
# ground at different depths give a low band crossed six times and a crown
# crossed twice, which is exactly the gradient wanted. That is what
# ART-DIRECTION 5 group 7 means by "they overlap and accumulate" and by "never
# let two sit at the same height": same ground, different tops.
#
# TWO PLACEMENT RULES THAT MATTER MORE THAN THE COORDINATES, both from
# ART-DIRECTION 5 group 7:
#
#   * never two at the same height. Three sheets at 0.11 accumulate to 0.30 and
#     that is the point, but three sheets whose tops coincide accumulate into
#     one thicker plane with one edge, which is the failure the accumulation
#     was meant to avoid.
#   * out of the point lights. The ward bonfire reaches 32 m from (24, -2) and
#     the bridge lantern 12 m from (48, 24); a mist slab lit from inside by a
#     point light is a glowing plastic sheet. The ditch instance nearest the
#     bridge is 6 m clear of the lantern's range and the hollow's nearest
#     instance is outside the bonfire's, which is why the hollow goes black
#     behind the breach instead of catching its light.


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
        PIECES[name]()
        lib.export(name, report)
    lib.summarise(report)
    print('OUT     %s' % os.path.abspath(cfg.OUT))


if __name__ == '__main__':
    main()
