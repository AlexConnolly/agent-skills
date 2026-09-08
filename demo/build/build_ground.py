# The ground for "Nightfall at the March Castle" — ART-DIRECTION.md section 6.
#
#   blender --background --python build_ground.py -- [platform|outfield|ridge|all]
#
# Three meshes, no baked map on any of them, all vertex-coloured:
#
#   ground_platform   the shoulder of limestone the castle stands on, with the
#                     ditch cut into it as a negative feature of the same mesh
#   ground_outfield   400 x 400 m of worked land: the drover's knoll the camera
#                     stands on, the hollow the mist pools in, and undulation
#   ground_ridge      everything from 145 m out to 620 m, carrying the crest at
#                     +6.0 that keeps the castle off a dead-flat horizon
#
# Blender, Z up, metres. The ward floor of the castle is Z = 0. Three.js is
# Y-up so the exporter maps (x, y, z) -> (x, z, -y): every "y" in the art
# direction's tables is a Z here, and every Three.js "z" is -Y.
#
# ------------------------------------------------------------------ the levels
#
# Section 6.1 fixes these and the whole scene is placed against them, so they
# are held EXACTLY rather than approximately, and main() measures them back off
# the built mesh rather than trusting the arithmetic:
#
#     ward floor / platform top      0.0
#     platform toe                  -4.5      batter falls at 1:1.6
#     outfield, general             -4.5
#     ditch bottom                  -6.8
#     ditch water surface           -6.0      (built by the crossing, not here)
#     drover's knoll crest          -2.7      the camera stands on it, eye -1.0
#     the hollow                    -6.5
#     distant ridge                 +6.0
#
# The plateaux — the top, the toe, the ditch floor — are dead flat and exact.
# The irregularity is put into the *plan* instead: the profile is evaluated at
# a distance that has been displaced by coordinate-derived noise, so the toe
# line and the ditch lip meander in and out by a couple of metres and the
# batter slumps and bulges, while every level stays on its number. Displacing
# the section sideways is also a better model of what erosion actually does to
# a bank than pushing vertices up and down.
#
# ------------------------------------------------------- why the shapes are these
#
# Almost every decision below is a sight line from the hero camera in section
# 4.1, not a taste call. The camera's eye is at Z = -1.0, which is one metre
# BELOW the platform top, so the platform's near shoulder cuts the horizon at
# about 1.3 degrees and hides every square metre of ground beyond it. That one
# fact decides three things:
#
#   1. The ridge has to clear that shoulder or it is not in the picture at all.
#      +6.0 at 240-320 m FROM THE CAMERA clears it; +6.0 at 240-320 m from the
#      castle (which is 330-410 m from the camera) does not. The camera reading
#      is the one that makes section 6.1's own claim true, so that is the one
#      used, and horizon_profile() below prints the margin in degrees.
#   2. The knoll cannot fall back toward the castle at 1:14. At that slope the
#      ground stays above the line of sight to the ditch and the water at -6.0
#      is hidden, which costs the bridge lantern's reflection — the whole
#      reason the lantern exists. It falls at about 1:9 instead, into a wet
#      margin a metre below the general field level at the ditch lip.
#   3. Detail in the middle distance is wasted. Nothing below about +4 m at
#      200 m out is visible from this camera, so the outfield's triangles go
#      into the near ground and the ridge, and the far ground is coarse.
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, 'art_ground'))

import bpy                                                   # noqa: E402
import bmesh                                                 # noqa: E402
import artconfig as cfg                                      # noqa: E402
import lib                                                   # noqa: E402
import texlib                                                # noqa: E402


# ---------------------------------------------------------------- levels (6.1)

WARD = 0.0
TOE = -4.5
FIELD = -4.5
DITCH_FLOOR = -6.8
WATER = -6.0
KNOLL_CREST = -2.7
HOLLOW_FLOOR = -6.5
RIDGE_CREST = 6.0

EYE = cfg.CAM[2]                       # -1.0
CAM_XY = (cfg.CAM[0], cfg.CAM[1])      # 78.9, -43.3


# ------------------------------------------------------------------ the plan
#
# The platform's level top, as an irregular faceted polygon: a rock shoulder
# has corners and re-entrants, and a rounded box or an ellipse reads as a cake
# stand. Wound counter-clockwise, and star-shaped about PLAN_C so the mesh can
# be swept radially (asserted in main()).
#
# Two deliberate re-entrants — a gully biting into the north shoulder where the
# castle's north curtain steps back, and a second above the ditch on the SE.
PLAN = [
    (46.0, -4.0),
    (45.0, 12.0),
    (40.0, 24.0),
    (32.0, 32.0),
    (20.0, 36.0),
    (9.0, 29.0),          # re-entrant
    (-2.0, 36.0),
    (-16.0, 37.0),
    (-28.0, 32.0),
    (-37.0, 23.0),
    (-42.0, 10.0),
    (-44.0, -6.0),
    (-41.0, -20.0),
    (-33.0, -30.0),
    (-20.0, -37.0),
    (-5.0, -42.0),
    (12.0, -42.0),
    (25.0, -37.0),
    (30.0, -32.0),        # re-entrant
    (39.0, -30.0),
    (44.0, -16.0),
]
PLAN_C = (1.0, -2.0)

# The castle's wall foot, as the convex hull of every vertex of castle.glb
# below Z = 2, measured — not guessed — with:
#
#   blender --background --python art_ground/shots.py -- castle   (bounds), and
#   the hull dump in the agent transcript.
#
# It is here only so berm_clearance() can prove section 6.1's "6 m of level
# ground outside every wall foot; 10 m outside the gate" instead of asserting
# it. Nothing structural depends on the castle.
CASTLE_HULL = [
    (-35.0, -22.2), (-34.0, -25.4), (-31.3, -27.1), (2.2, -31.5),
    (9.8, -31.5), (31.4, -25.8), (34.0, -21.3), (36.1, 1.5),
    (36.1, 22.2), (35.3, 26.6), (30.0, 29.1), (-29.7, 26.3),
    (-32.2, 25.5), (-33.2, 22.2),
]
GATE_Y = -24.0          # anything south of this is the gate approach: 10 m


# --------------------------------------------------- the section, outward from PLAN
#
# d is the distance outward from the plan polygon. Every band is a run in
# metres; the levels they run between are the constants above.
BATTER = 7.2            # 0.0 -> -4.5, which is 1:1.6
TOE_W = 3.2             # -4.5, level, so the bridge has something to land on
SCARP = 3.4             # -4.5 -> -6.8
DFLOOR = 6.0            # -6.8, level
CSCARP = 4.4            # -6.8 -> whatever the field is doing
APRON = 4.0             # follow the field, so the mesh does not end on a slope

D_BATTER = BATTER
D_TOE = D_BATTER + TOE_W
D_SCARP = D_TOE + SCARP
D_FLOOR = D_SCARP + DFLOOR
D_LIP = D_FLOOR + CSCARP
D_END = D_LIP + APRON

# How far the outfield is pushed down underneath the platform mesh, so the two
# never fight for the depth buffer. 12 cm at the platform's rim, where they are
# both drawing the same turf at the same height and the seam has no colour
# difference to be seen by; 3.2 m under the ditch, where the outfield would
# otherwise punch straight through the ditch floor.
SINK_DEEP = 3.2
SINK_RIM = 0.12


# ---------------------------------------------------------------- palette (6.2/6.3)

TURF = 0x1A2419         # turf-night
ROCK = 0x2A2B28         # limestone where the slope breaks through
DARK = 0x101812         # the ditch and the re-entrants
WETB = 0x1B1D18         # the wet band above the waterline
DRY = 0x232616          # browner and drier, the worn crest of the knoll
SOUR = 0x161C18         # the sour wet ground east of the ditch


# ---------------------------------------------------------------- noise
#
# Value noise from a hash of the integer lattice, smootherstep-interpolated.
# Deterministic from the coordinates, so the same seed is the same landform on
# any machine and terrain.json always agrees with the mesh.

def _hash2(i, j, s):
    n = (i * 374761393 + j * 668265263 + s * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF) / 8388607.5 - 1.0


def vnoise(x, y, s=0):
    i, j = math.floor(x), math.floor(y)
    fx, fy = x - i, y - j
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    a = _hash2(i, j, s)
    b = _hash2(i + 1, j, s)
    c = _hash2(i, j + 1, s)
    d = _hash2(i + 1, j + 1, s)
    return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy


def fbm(x, y, s=0, octaves=2):
    v = 0.0
    total = 0.0
    amp = 1.0
    for k in range(octaves):
        v += amp * vnoise(x, y, s + k * 37)
        total += amp
        x *= 2.13
        y *= 2.13
        amp *= 0.48
    return v / total


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def smooth01(t):
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def ramp(v, a, b):
    """1 at v == a, 0 at v == b, smooth between. Works either direction."""
    return smooth01((v - b) / (a - b)) if a != b else (1.0 if v == a else 0.0)


def mix(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- the plan as a field

def poly_sd(px, py, poly=None):
    """Signed distance to the plan polygon, negative inside."""
    poly = poly or PLAN
    best = 1e18
    inside = False
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        wx, wy = px - ax, py - ay
        ll = ex * ex + ey * ey
        t = 0.0 if ll < 1e-12 else max(0.0, min(1.0, (wx * ex + wy * ey) / ll))
        cx, cy = wx - ex * t, wy - ey * t
        best = min(best, cx * cx + cy * cy)
        if (ay > py) != (by > py):
            if px < ax + (py - ay) * ex / ey:
                inside = not inside
    return (-1.0 if inside else 1.0) * math.sqrt(best)


def dist_eff(px, py):
    """The plan distance the section is actually evaluated at.

    Displacing d rather than z is what keeps every level in 6.1 exact while the
    toe line and the ditch lip still wander a couple of metres in and out. The
    gradient of the displacement stays well under 1, so d_eff is monotonic
    along any outward ray and no band can be skipped."""
    d = poly_sd(px, py)
    d += 1.55 * fbm(px / 23.0, py / 23.0, 401, 2)
    d += 0.55 * fbm(px / 8.5, py / 8.5, 419, 2)
    return d


# ---------------------------------------------------------------- the outfield field

KNOLL_AT = (78.9, -43.3)                 # the camera's own ground point
_KA = (-0.8836, 0.4684)                  # unit vector from the knoll to the castle
_KP = (0.4684, 0.8836)

HOLLOW_AT = (5.0, 92.0)
HOLLOW_R = (70.0, 45.0)

RIDGE_R = 258.0                          # crest, in metres FROM THE CAMERA
RIDGE_FWD = math.degrees(math.atan2(cfg.CAM_TARGET[1] - cfg.CAM[1],
                                    cfg.CAM_TARGET[0] - cfg.CAM[0]))


def knoll_w(px, py):
    u = (px - KNOLL_AT[0]) * _KA[0] + (py - KNOLL_AT[1]) * _KA[1]
    v = (px - KNOLL_AT[0]) * _KP[0] + (py - KNOLL_AT[1]) * _KP[1]
    # Steeper on the castle side than the outer side: a spur, not a dome, and
    # the steep side is what lets the eye see over the brow into the ditch.
    ru = u / 17.5 if u > 0 else u / 33.0
    rv = v / 27.0
    t = math.sqrt(ru * ru + rv * rv)
    return 1.0 - smooth01(t)


def hollow_w(px, py):
    dx = (px - HOLLOW_AT[0]) / HOLLOW_R[0]
    dy = (py - HOLLOW_AT[1]) / HOLLOW_R[1]
    t = math.sqrt(dx * dx + dy * dy)
    w = 1.0 - smooth01(t)
    # Bite the rim about a little so the basin is not a saucer.
    return clamp01(w * (1.0 + 0.22 * fbm(px / 44.0, py / 44.0, 733, 2)))


def ridge_w_target(px, py):
    """Weight and target height for the distant ridge.

    Defined by distance FROM THE CAMERA, not from the castle, because the job
    the ridge has to do is to sit at a constant angle above the platform's near
    shoulder right across the frame — and a crest at a constant camera range is
    exactly a crest at a constant elevation angle."""
    dx, dy = px - CAM_XY[0], py - CAM_XY[1]
    rc = math.hypot(dx, dy)
    phi = (math.degrees(math.atan2(dy, dx)) - RIDGE_FWD + 540.0) % 360.0 - 180.0
    # Along the arc: full height across the frame and a little beyond, easing
    # away at the ends so the ridge does not stop dead.
    arc = ramp(abs(phi), 42.0, 78.0)
    # Across: up the front, a crest, then a long back slope that never returns
    # to field level — otherwise there is a valley behind the ridge.
    if rc < RIDGE_R:
        prof = smooth01((rc - 168.0) / (RIDGE_R - 168.0))
    else:
        prof = 1.0 - 0.62 * smooth01((rc - RIDGE_R - 18.0) / 190.0)
    w = arc * prof
    # The crest is exactly +6.0 where it matters — behind the castle, a little
    # right of the frame centre — and falls away along its length so it reads
    # as a ridge and not as a wall.
    fall = 1.9 * (1.0 - math.exp(-((phi + 6.0) / 34.0) ** 2))
    target = RIDGE_CREST - fall
    return w, target


def h_field(px, py):
    """The outfield surface: knows nothing about the castle or the ditch."""
    z = FIELD
    z += 0.80 * fbm(px / 86.0, py / 86.0, 101, 2)
    z += 0.44 * fbm(px / 31.0, py / 31.0, 211, 2)
    z += 0.15 * fbm(px / 11.5, py / 11.5, 307, 2)
    z = mix(z, KNOLL_CREST, knoll_w(px, py))
    z = mix(z, HOLLOW_FLOOR, hollow_w(px, py))
    w, target = ridge_w_target(px, py)
    z = mix(z, target, w)
    return z


def margin_dip(d):
    """The wet trough that always forms outside a ditch.

    Worth a metre of the picture: it is what drops the ground at the ditch lip
    below the camera's line of sight to the water, and it is the sour ground
    section 6.3 wants coloured differently and section 6 of the asset list
    wants hurdled off."""
    return -1.05 * (1.0 - smooth01(abs(d - 28.0) / 15.0))


def field_h(px, py):
    """h_field with the ditch margin — the surface outside the platform mesh."""
    d = dist_eff(px, py)
    z = h_field(px, py)
    if d > 12.0:
        z += margin_dip(d)
    return z


# ---------------------------------------------------------------- the section

def _ease(t):
    """A shoulder and a toe on every slope, but not so much that the batter
    doubles its mid-slope: 65 % of the way to a smoothstep."""
    return mix(t, t * t * (3.0 - 2.0 * t), 0.65)


def section_z(d, base):
    """Height at plan-distance d, cutting down into ground at `base`."""
    if d <= 0.0:
        return WARD
    if d < D_BATTER:
        return mix(WARD, TOE, _ease(d / BATTER))
    if d < D_TOE:
        return TOE
    if d < D_SCARP:
        return mix(TOE, DITCH_FLOOR, _ease((d - D_TOE) / SCARP))
    if d < D_FLOOR:
        return DITCH_FLOOR
    if d < D_LIP:
        return mix(DITCH_FLOOR, base, _ease((d - D_FLOOR) / CSCARP))
    return base


def slump(px, py, d):
    """Vertical relief on the slopes only.

    Each term is a half sine across its band, so it is exactly zero where the
    band meets a plateau and no level in 6.1 can be disturbed by it."""
    z = 0.0
    if 0.0 < d < D_BATTER:
        z += 0.42 * fbm(px / 13.0, py / 13.0, 511, 2) * \
            math.sin(math.pi * d / BATTER)
    elif D_TOE < d < D_SCARP:
        z += 0.16 * fbm(px / 9.0, py / 9.0, 523, 2) * \
            math.sin(math.pi * (d - D_TOE) / SCARP)
    elif D_FLOOR < d < D_LIP:
        z += 0.26 * fbm(px / 12.0, py / 12.0, 541, 2) * \
            math.sin(math.pi * (d - D_FLOOR) / CSCARP)
    return z


def platform_h(px, py):
    d = dist_eff(px, py)
    base = h_field(px, py) + (margin_dip(d) if d > 12.0 else 0.0)
    return section_z(d, base) + slump(px, py, d)


def ground_h(px, py):
    """The composite visible surface: what terrain.json carries and what every
    instanced asset in the scene is seated on."""
    d = dist_eff(px, py)
    if d < D_END:
        return platform_h(px, py)
    return field_h(px, py)


def outfield_h(px, py):
    """The outfield mesh's own surface, pushed down where the platform or the
    ridge mesh is drawn over it."""
    d = dist_eff(px, py)
    z = field_h(px, py)
    z -= SINK_DEEP * ramp(d, 18.0, D_END)
    z -= SINK_RIM * ramp(d, D_END - 2.0, D_END + 10.0)
    r = math.hypot(px - PLAN_C[0], py - PLAN_C[1])
    z -= SINK_RIM * ramp(r, 148.0, 132.0)
    return z


# ---------------------------------------------------------------- colour (6.2/6.3)

def _lin(hex_value):
    c = texlib.srgb(hex_value)
    return (c[0], c[1], c[2])


_TURF = _lin(TURF)
_ROCK = _lin(ROCK)
_DARK = _lin(DARK)
_WETB = _lin(WETB)
_DRY = _lin(DRY)
_SOUR = _lin(SOUR)


def _blend(a, b, t):
    return (mix(a[0], b[0], t), mix(a[1], b[1], t), mix(a[2], b[2], t))


def ground_colour(co, normal):
    """Four colours driven by height and slope, plus the wet band. No UVs, no
    bake, no image files — glTF carries it as COLOR_0 and it interpolates, so a
    grass-to-rock transition fades instead of stepping at a polygon edge."""
    x, y, z = co[0], co[1], co[2]
    nz = clamp01(normal[2])

    c = _TURF
    # worn and drier where the drove road crosses the high ground
    c = _blend(c, _DRY, 0.85 * ramp(z, -2.2, -3.9) * smooth01((nz - 0.72) / 0.2))
    # sour and wet in the low ground, which is most of the ditch margin
    c = _blend(c, _SOUR, 0.75 * ramp(z, -5.6, -4.75))
    # limestone breaking through wherever the slope goes past about 35 degrees
    rock_t = ramp(nz, 0.66, 0.88)
    c = _blend(c, _ROCK, rock_t)
    # the ditch and the re-entrants, where nothing but shadow lives
    c = _blend(c, _DARK, 0.88 * ramp(z, -6.6, -5.2))
    # the wet band, the bottom 1.2 m of the ditch above the waterline
    band = smooth01((z - (WATER - 0.3)) / 0.35) * ramp(z, WATER + 1.0, WATER + 1.5)
    c = _blend(c, _WETB, 0.8 * band)

    n = 1.0 + 0.13 * fbm(x / 17.0, y / 17.0, 811, 2) \
        + 0.07 * fbm(x / 4.5, y / 4.5, 829, 2)
    return (c[0] * n, c[1] * n, c[2] * n)


def vcol_material(name, rough=0.94):
    """Principled with COLOR_0 wired to Base Color.

    lib.material() cannot do this: the glTF exporter only writes COLOR_0 when
    the material actually reads the colour attribute, so a mesh painted by
    texlib.vertex_colour() and given a plain material exports as a flat slab
    and every render lies about it."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    ca = nt.nodes.new('ShaderNodeVertexColor')
    ca.layer_name = 'Col'
    ca.location = (-320, 220)
    nt.links.new(ca.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    return m


# ---------------------------------------------------------------- mesh helpers

def _obj(name):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob, me


def _finish(ob, me, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
    return ob


def grid_mesh(name, xs, ys, hfn, mat):
    """A single-sided heightfield. Not lib.loft(): loft closes its section into
    a ring, which for a heightfield means an underside nobody can see from a
    camera that is always above it, at exactly twice the triangles."""
    ob, me = _obj(name)
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, hfn(x, y))) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((rows[j][i], rows[j][i + 1],
                          rows[j + 1][i + 1], rows[j + 1][i]))
    return _finish(ob, me, bm, mat)


def polar_mesh(name, centre, angles, radii_for, hfn, mat,
               skirt=0.0, cap_centre=False, floor=None):
    """Rings swept round `centre`. `radii_for(k)` returns the radii for spoke k
    (the same count on every spoke), innermost first."""
    ob, me = _obj(name)
    bm = bmesh.new()
    rings = []
    for k, a in enumerate(angles):
        ca, sa = math.cos(a), math.sin(a)
        spoke = []
        for r in radii_for(k):
            x, y = centre[0] + ca * r, centre[1] + sa * r
            spoke.append(bm.verts.new((x, y, hfn(x, y))))
        rings.append(spoke)
    n = len(angles)
    m = len(rings[0])
    for k in range(n):
        k2 = (k + 1) % n
        for i in range(m - 1):
            bm.faces.new((rings[k][i], rings[k][i + 1],
                          rings[k2][i + 1], rings[k2][i]))
    if cap_centre:
        cz = hfn(centre[0], centre[1])
        hub = bm.verts.new((centre[0], centre[1], cz))
        for k in range(n):
            bm.faces.new((hub, rings[k][0], rings[(k + 1) % n][0]))
    if skirt:
        low = [bm.verts.new((v.co.x, v.co.y, v.co.z - skirt))
               for v in (rings[k][m - 1] for k in range(n))]
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((rings[k][m - 1], low[k], low[k2], rings[k2][m - 1]))
        if floor is not None:
            base = [bm.verts.new((v.co.x, v.co.y, floor)) for v in low]
            hub = bm.verts.new((centre[0], centre[1], floor))
            for k in range(n):
                k2 = (k + 1) % n
                bm.faces.new((low[k], base[k], base[k2], low[k2]))
                bm.faces.new((hub, base[k2], base[k]))
    return _finish(ob, me, bm, mat)


def inner_skirt(ob, centre, angles, r_inner, hfn, drop):
    """A hidden wall hanging off a polar mesh's inner rim, so nothing can be
    seen under it at a grazing angle."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    top = []
    for a in angles:
        x = centre[0] + math.cos(a) * r_inner
        y = centre[1] + math.sin(a) * r_inner
        top.append(bm.verts.new((x, y, hfn(x, y))))
    low = [bm.verts.new((v.co.x, v.co.y, v.co.z - drop)) for v in top]
    n = len(angles)
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((top[k2], low[k2], low[k], top[k]))
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-4)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    return ob


# ---------------------------------------------------------------- the three meshes

SPOKES = 128

# Where the rings go: tight through the shoulder, the toe, the lip and the
# ditch, loose where the section is flat.
D_RINGS = [0.0, 0.7, 1.6, 2.7, 3.9, 5.1, 6.2, 7.2,
           8.2, 9.3, 10.4,
           11.4, 12.5, 13.8,
           15.4, 17.4, 19.8,
           20.9, 22.1, 23.2, 24.2,
           25.6, 28.2]
TOP_FRACTIONS = [0.18, 0.36, 0.53, 0.69, 0.83, 0.94, 1.0]


_R0_CACHE = {}


def boundary_radius(a):
    """Where the ray at angle `a` from PLAN_C crosses the plan polygon."""
    key = round(a, 7)
    if key in _R0_CACHE:
        return _R0_CACHE[key]
    lo, hi = 0.0, 200.0
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        p = (PLAN_C[0] + math.cos(a) * mid, PLAN_C[1] + math.sin(a) * mid)
        if poly_sd(p[0], p[1]) < 0.0:
            lo = mid
        else:
            hi = mid
    _R0_CACHE[key] = 0.5 * (lo + hi)
    return _R0_CACHE[key]


def radius_for_d(a, r0, d):
    """Where the ray at angle `a` reaches plan-distance d.

    Solved rather than offset: offsetting a polygon self-intersects at every
    re-entrant, and the level sets of the distance field never do."""
    if d <= 0.0:
        return r0
    lo, hi = r0, r0 + d * 3.0 + 4.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        p = (PLAN_C[0] + math.cos(a) * mid, PLAN_C[1] + math.sin(a) * mid)
        if poly_sd(p[0], p[1]) < d:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def build_platform():
    mat = vcol_material('ground_rock')
    angles = [2.0 * math.pi * k / SPOKES for k in range(SPOKES)]
    r0 = [boundary_radius(a) for a in angles]
    spokes = []
    for k, a in enumerate(angles):
        rs = [r0[k] * f for f in TOP_FRACTIONS[:-1]]
        rs += [radius_for_d(a, r0[k], d) for d in D_RINGS]
        spokes.append(rs)
    ob = polar_mesh('ground_platform', PLAN_C, angles, lambda k: spokes[k],
                    platform_h, mat, skirt=0.9, cap_centre=True, floor=-9.5)
    texlib.vertex_colour(ob, ground_colour)
    return ob


OUT_HALF = 200.0
OUT_N = 97                      # 96 x 96 quads at 4.167 m, section 6.3


def build_outfield():
    mat = vcol_material('ground_turf')
    step = 2.0 * OUT_HALF / (OUT_N - 1)
    xs = [-OUT_HALF + i * step for i in range(OUT_N)]
    ys = list(xs)
    ob = grid_mesh('ground_outfield', xs, ys, outfield_h, mat)
    texlib.vertex_colour(ob, ground_colour)
    return ob


RIDGE_RINGS = [145.0, 152.0, 160.0, 168.0, 176.0, 184.0, 192.0, 200.0,
               209.0, 218.0, 228.0, 238.0, 250.0, 264.0, 280.0, 300.0,
               325.0, 355.0, 392.0, 435.0, 490.0, 555.0, 620.0]
RIDGE_SPOKES = 144


def build_ridge():
    mat = vcol_material('ground_ridge_turf')
    angles = [2.0 * math.pi * k / RIDGE_SPOKES for k in range(RIDGE_SPOKES)]
    ob = polar_mesh('ground_ridge', PLAN_C, angles,
                    lambda k: RIDGE_RINGS, field_h, mat, skirt=1.6)
    inner_skirt(ob, PLAN_C, angles, RIDGE_RINGS[0], field_h, 1.2)
    texlib.vertex_colour(ob, ground_colour)
    return ob


# ---------------------------------------------------------------- terrain.json

TERRAIN_STEP = 2.5


def write_terrain():
    """One source of truth for the height of the ground (6.3).

    Written in THREE.JS axes, because the only consumer is the placement code:
    x is Three x, the outer index is Three z, and the value is Three y.
    Blender y = -Three z."""
    n = int(2 * OUT_HALF / TERRAIN_STEP) + 1
    rows = []
    for j in range(n):
        z3 = -OUT_HALF + j * TERRAIN_STEP
        by = -z3
        rows.append([round(ground_h(-OUT_HALF + i * TERRAIN_STEP, by), 3)
                     for i in range(n)])
    data = {
        'note': 'Ground height for Nightfall at the March Castle. Three.js '
                'axes: x east, y up, z south. heights[iz][ix] is y at '
                'x = min + ix*step, z = min + iz*step. Sample bilinearly; do '
                'not reimplement the height function in JS.',
        'source': 'demo/build/build_ground.py',
        'min': [-OUT_HALF, -OUT_HALF],
        'max': [OUT_HALF, OUT_HALF],
        'step': TERRAIN_STEP,
        'n': [n, n],
        'levels': {
            'ward': WARD, 'platform_toe': TOE, 'outfield': FIELD,
            'ditch_floor': DITCH_FLOOR, 'ditch_water': WATER,
            'knoll_crest': KNOLL_CREST, 'hollow': HOLLOW_FLOOR,
            'ridge_crest': RIDGE_CREST,
        },
        'heights': rows,
    }
    out = os.path.abspath(cfg.DATA)
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'terrain.json')
    with open(path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print('TERRAIN %s  %d x %d at %.2f m  %.1f KB'
          % (path, n, n, TERRAIN_STEP, os.path.getsize(path) / 1024.0))
    return path


# ---------------------------------------------------------------- diagnostics

def mesh_zs(obj):
    return [round((obj.matrix_world @ v.co).z, 4) for v in obj.data.vertices]


def mesh_levels(zs):
    """Measure section 6.1 back off the built meshes. Assuming a level is right
    because the arithmetic says so is how a scene ends up with every asset
    5 cm out."""
    print('=== 6.1 levels, measured on the built mesh ===')
    want = [('ward floor / platform top', WARD),
            ('platform toe', TOE),
            ('ditch bottom', DITCH_FLOOR),
            ('knoll crest (under the camera)', KNOLL_CREST),
            ('the hollow', HOLLOW_FLOOR),
            ('distant ridge crest', RIDGE_CREST)]
    hi, lo = max(zs), min(zs)
    counts = {}
    for z in zs:
        counts[z] = counts.get(z, 0) + 1
    for label, level in want:
        n = counts.get(round(level, 4), 0)
        near = min(abs(z - level) for z in zs)
        flag = 'EXACT (%d verts)' % n if n else 'nearest %+.4f off' % near
        print('  %-32s want %+7.3f   %s' % (label, level, flag))
    print('  mesh z range %+.3f .. %+.3f  (the low end is the hidden skirt)'
          % (lo, hi))


def probe_levels():
    """The same levels, taken off the height functions at the points that
    matter, to the millimetre."""
    print('=== 6.1 levels, probed on the height function ===')
    rows = [
        ('ward centre', ground_h(0.0, -2.0), WARD),
        ('berm, 8 m E of the east curtain', ground_h(44.0, 2.0), WARD),
        ('berm, 8 m S of the gate', ground_h(6.0, -38.0), WARD),
        ('knoll crest = camera ground point', ground_h(*KNOLL_AT), KNOLL_CREST),
        ('hollow floor', ground_h(*HOLLOW_AT), HOLLOW_FLOOR),
    ]
    for label, got, want in rows:
        print('  %-38s %+8.4f   want %+7.3f   %s'
              % (label, got, want, 'OK' if abs(got - want) < 0.002 else '****'))
    # The toe, the ditch floor and the ridge are lines, not points: march.
    toe = []
    floor = []
    for k in range(36):
        a = 2 * math.pi * k / 36.0
        r0 = boundary_radius(a)
        zs = []
        for i in range(int(D_END * 10)):
            d = i / 10.0
            r = r0 + d
            p = (PLAN_C[0] + math.cos(a) * r, PLAN_C[1] + math.sin(a) * r)
            zs.append((platform_h(*p), d))
        floor.append(min(zs)[0])
        toe.append(len([1 for z, d in zs if abs(z - TOE) < 1e-9]) / 10.0)
    print('  platform toe   %+7.3f exactly, over %.1f..%.1f m of run on every '
          'one of 36 bearings' % (TOE, min(toe), max(toe)))
    print('  ditch floor    min over 36 bearings %+8.4f .. %+8.4f  want %+.3f  '
          '%s' % (min(floor), max(floor), DITCH_FLOOR,
                  'OK' if abs(min(floor) - DITCH_FLOOR) < 0.002
                  and abs(max(floor) - DITCH_FLOOR) < 0.002 else '****'))
    rid = max(h_field(CAM_XY[0] + math.cos(math.radians(RIDGE_FWD + p)) * r,
                      CAM_XY[1] + math.sin(math.radians(RIDGE_FWD + p)) * r)
              for p in range(-24, 13) for r in range(230, 300))
    print('  ridge crest    max %+8.4f   want %+7.3f   %s'
          % (rid, RIDGE_CREST, 'OK' if abs(rid - RIDGE_CREST) < 0.005 else '****'))


def berm_clearance():
    print('=== berm: 6 m of level ground outside every wall foot, 10 m at the '
          'gate ===')
    worst = (1e9, None)
    worst_gate = (1e9, None)
    for i in range(len(CASTLE_HULL)):
        ax, ay = CASTLE_HULL[i]
        bx, by = CASTLE_HULL[(i + 1) % len(CASTLE_HULL)]
        for t in range(41):
            f = t / 40.0
            px, py = ax + (bx - ax) * f, ay + (by - ay) * f
            d = -poly_sd(px, py)          # positive = inside the plan
            if py < GATE_Y:
                if d < worst_gate[0]:
                    worst_gate = (d, (px, py))
            elif d < worst[0]:
                worst = (d, (px, py))
    print('  tightest berm     %.2f m at (%.1f, %.1f)   want >= 6.0   %s'
          % (worst[0], worst[1][0], worst[1][1],
             'OK' if worst[0] >= 6.0 else '**** TOO TIGHT'))
    print('  tightest at gate  %.2f m at (%.1f, %.1f)   want >= 10.0  %s'
          % (worst_gate[0], worst_gate[1][0], worst_gate[1][1],
             'OK' if worst_gate[0] >= 10.0 else '**** TOO TIGHT'))


def ditch_section(bearing_deg, label):
    a = math.radians(bearing_deg)
    r0 = boundary_radius(a)
    prev = None
    marks = {}
    for i in range(int((D_END + 6) * 50)):
        r = r0 + i / 50.0
        p = (PLAN_C[0] + math.cos(a) * r, PLAN_C[1] + math.sin(a) * r)
        z = ground_h(*p)
        if prev is not None and prev[1] > WATER >= z and 'water_in' not in marks:
            marks['water_in'] = (r, p)
        if prev is not None and prev[1] <= WATER < z and 'water_in' in marks:
            marks.setdefault('water_out', (r, p))
        prev = (r, z)
    ri = marks.get('water_in', (0, (0, 0)))
    ro = marks.get('water_out', (0, (0, 0)))
    print('  %-22s water from r=%.1f to r=%.1f  (%.1f m wide) at Blender '
          '(%.1f, %.1f)..(%.1f, %.1f)'
          % (label, ri[0], ro[0], ro[0] - ri[0],
             ri[1][0], ri[1][1], ro[1][0], ro[1][1]))
    lip_in = r0 + D_TOE
    lip_out = r0 + D_LIP
    pin = (PLAN_C[0] + math.cos(a) * lip_in, PLAN_C[1] + math.sin(a) * lip_in)
    pout = (PLAN_C[0] + math.cos(a) * lip_out, PLAN_C[1] + math.sin(a) * lip_out)
    print('  %-22s clear span %.1f m, inner lip %+.2f at (%.1f, %.1f), outer '
          'lip %+.2f at (%.1f, %.1f)'
          % ('', lip_out - lip_in, ground_h(*pin), pin[0], pin[1],
             ground_h(*pout), pout[0], pout[1]))


def horizon_profile():
    """What the hero camera can actually see over the platform's near shoulder.

    This is the diagnostic the whole asset turns on: the ridge is only in the
    picture if it clears this line, and nothing else in the middle distance is
    in the picture at all."""
    print('=== hero horizon: the highest thing on each ray, in degrees above '
          'the lens ===')
    print('  frame   skyline   at r     from   ridge    band     frame-y%')
    tilt = -cfg.HERO_ELEVATION_DEG
    for s in range(11):
        frac = s / 10.0
        phi = (0.5 - frac) * 54.0
        b = math.radians(RIDGE_FWD + phi)
        cb, sb = math.cos(b), math.sin(b)
        near = (-90.0, 0.0)
        far = (-90.0, 0.0)
        for i in range(2, 620):
            t = float(i)
            z = ground_h(CAM_XY[0] + cb * t, CAM_XY[1] + sb * t)
            e = math.degrees(math.atan2(z - EYE, t))
            if t < 150.0:
                if e > near[0]:
                    near = (e, t)
            elif e > far[0]:
                far = (e, t)
        band = far[0] - near[0]
        top = (tilt + 16.0 - max(near[0], far[0])) / 32.0 * 100.0
        print('  %4.0f%%   %+6.2f    %5.0f m   %-6s %+6.2f  %+6.2f   %5.1f%%'
              % (frac * 100, near[0], near[1], 'near', far[0], band, top))
    print('  "band" is how far the far ground stands above the near skyline. '
          'Positive means the ridge is in the picture.')


def sight_line(label, target_xy, target_z):
    """Whether a point is visible from the lens, and by how much."""
    dx = target_xy[0] - CAM_XY[0]
    dy = target_xy[1] - CAM_XY[1]
    span = math.hypot(dx, dy)
    ux, uy = dx / span, dy / span
    worst = 1e9
    at = 0.0
    for i in range(1, int(span)):
        t = float(i)
        z = ground_h(CAM_XY[0] + ux * t, CAM_XY[1] + uy * t)
        los = EYE + (target_z - EYE) * (t / span)
        if los - z < worst:
            worst = los - z
            at = t
    print('  %-34s %s  clearance %+.2f m at %.0f m out'
          % (label, 'VISIBLE' if worst > 0 else 'HIDDEN ', worst, at))


# ---------------------------------------------------------------- main

def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def assert_star_shaped():
    for k in range(360):
        a = 2 * math.pi * k / 360.0
        r = boundary_radius(a)
        p = (PLAN_C[0] + math.cos(a) * r, PLAN_C[1] + math.sin(a) * r)
        if abs(poly_sd(*p)) > 0.02:
            raise SystemExit('PLAN is not star-shaped about PLAN_C at %.1f deg'
                             % math.degrees(a))
    print('PLAN  %d facets, star-shaped about (%.1f, %.1f), '
          'extent %.1f x %.1f m at the top'
          % (len(PLAN), PLAN_C[0], PLAN_C[1],
             max(p[0] for p in PLAN) - min(p[0] for p in PLAN),
             max(p[1] for p in PLAN) - min(p[1] for p in PLAN)))


def main():
    args = argv()
    which = args[0] if args else 'all'
    report = []

    assert_star_shaped()
    berm_clearance()
    probe_levels()

    a = math.atan2(CAM_XY[1] - PLAN_C[1], CAM_XY[0] - PLAN_C[0])
    print('=== the ditch where the drove road crosses ===')
    ditch_section(math.degrees(a), 'on the camera bearing')

    print('=== sight lines from the lens at %+.1f ===' % EYE)
    r0 = boundary_radius(a)
    wr = r0 + D_FLOOR - 1.0
    sight_line('ditch water, near half',
               (PLAN_C[0] + math.cos(a) * (r0 + D_LIP - 1.5),
                PLAN_C[1] + math.sin(a) * (r0 + D_LIP - 1.5)), WATER)
    sight_line('ditch water, centre',
               (PLAN_C[0] + math.cos(a) * wr, PLAN_C[1] + math.sin(a) * wr),
               WATER)
    sight_line('platform toe, ESE',
               (PLAN_C[0] + math.cos(a) * (r0 + D_TOE - 1.0),
                PLAN_C[1] + math.sin(a) * (r0 + D_TOE - 1.0)), TOE)

    horizon_profile()

    zs = []
    for tag, fn in (('platform', build_platform),
                    ('outfield', build_outfield),
                    ('ridge', build_ridge)):
        if which not in ('all', tag):
            continue
        lib.reset()
        ob = fn()
        zs += mesh_zs(ob)
        lib.export('ground_' + tag, report)
    if which == 'all':
        write_terrain()

    if zs:
        mesh_levels(zs)
    lib.summarise(report)


main()
