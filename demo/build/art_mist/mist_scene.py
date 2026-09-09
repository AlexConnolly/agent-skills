# The twenty mist instances in the world they pool in, from the hero camera.
#
#   blender --background --python mist_scene.py -- [tag]
#
# shots.py renders one model at a time on a flat plane at a fixed heading, and
# for these four pieces that is the wrong sheet for three reasons, all of which
# this script exists to fix:
#
#   1. A SINGLE SHEET AT ELEVEN PER CENT IS NOT THE ASSET. ART-DIRECTION 5
#      group 7 is explicit that they overlap and accumulate -- three layers at
#      0.11 reading as 0.30 -- so a lone instance is a third of the thing and
#      judging the density off one is judging the wrong number.
#   2. MIST NEEDS SOMEWHERE TO POOL. The whole claim is that these do what
#      FogExp2 cannot: make one hollow thicker than the field around it. On a
#      flat plane that claim is untestable, so this builds the levels out of
#      ART-DIRECTION 6.1 -- platform, ditch, knoll, hollow, ridge -- and puts
#      the sheets in them.
#   3. THE FOG IS PART OF THE PICTURE. Section 3.3's FogExp2(0x16243A, 0.0045)
#      is applied here in the compositor off the Z pass, with the same curve
#      Three.js uses, so what comes out is the mist SEEN THROUGH the fog rather
#      than the mist on its own. A sheet that reads beautifully without it and
#      dissolves with it has not been proven at all.
#
# It renders a matched pair every time -- `_mist.png` and `_bare.png`, the same
# frame with the sheets hidden. That pair is the only honest answer to "is this
# doing anything the global fog is not already doing".
#
# WHAT IS FAITHFUL AND WHAT IS NOT. Faithful: the real ground_platform,
# ground_outfield and ground_ridge as exported by build_ground.py, seated by
# bilinear sampling of the terrain.json those three were written from -- which
# is what ART-DIRECTION 6.3 means by one source of truth, and the reason this
# script does not have a height function of its own any more; the real
# castle.glb; the camera (4.1) to the metre and the degree; the moon (3.1);
# the hemisphere fill (3.2); the fog curve and colour (3.3); the two point
# lights whose range the sheets have to stay out of (3.4); and the sheets'
# own material straight out of their glb.
#
# Not faithful, and do not read anything into them: there is no bloom, so read
# these as the hardest and least flattering version of the frame; Blender's
# gradient world is not Three.js's HemisphereLight, which is close but not the
# same integral; and there is no ditch water, because the only ditch the hero
# camera can see is its outer BANK at about -4.4, three metres above the
# waterline, so a water plane would have been an invisible complication.
#
# If the models are not on disk it falls back to an analytic stand-in of 6.1's
# levels and says so loudly. Everything below was measured against the real
# ones.
import bpy
import bmesh
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

import artconfig as cfg      # noqa: E402
import lib                   # noqa: E402


# ---------------------------------------------------------------- palette

SKY_ZENITH = 0x080D18
SKY_HORIZON = 0x1C2C42
FOG = 0x16243A
MOON_COLD = 0xAFC8EC
STONE_DARK = 0x151D29
TURF_NIGHT = 0x1A2419
EARTH_WET = 0x20211C
WATER_BLACK = 0x0A121A

FOG_DENSITY = 0.0045         # ART-DIRECTION 3.3

# Must match build_mist.py's HEM_FRACTION: the fraction of each piece's
# height that lives below its ground line and is meant to be buried.
HEM = 0.40


# ---------------------------------------------------------------- coordinates
#
# ART-DIRECTION 0.2: X_three = X_blender, Y_three = Z_blender,
# Z_three = -Y_blender. Everything below is quoted in Three.js metres, the way
# the document and build_mist.py's placement table are, and converted here
# once.

def blend(x, y, z):
    """Three.js (x, y, z) -> Blender (x, y, z)."""
    return (x, -z, y)


# ---------------------------------------------------------------- the ground
#
# ART-DIRECTION 6.3: build_ground.py writes docs/data/terrain.json -- the
# station grid, the extents and the heights -- and everything else samples it
# bilinearly. "Do not reimplement the height function in JS", and the same goes
# for a Blender check rig: an instance seated on a private copy of the terrain
# is not seated on the terrain.

SCENE = os.environ.get('SCENE_MODELS') or os.path.join(
    os.path.dirname(cfg.OUT), 'models')
TERRAIN = os.environ.get('SCENE_TERRAIN') or os.path.join(
    os.path.dirname(cfg.OUT), 'data', 'terrain.json')

_GRID = None


def terrain():
    """The real height grid, or None if build_ground.py has not run."""
    global _GRID
    if _GRID is None:
        if os.path.exists(TERRAIN):
            import json
            with open(TERRAIN) as fh:
                _GRID = json.load(fh)
            print('TERRAIN %s  %s..%s step %s'
                  % (TERRAIN, _GRID['min'], _GRID['max'], _GRID['step']))
        else:
            _GRID = False
            print('TERRAIN MISSING at %s -- falling back to the analytic '
                  'stand-in of ART-DIRECTION 6.1. Every seating number below '
                  'is then approximate.' % TERRAIN)
    return _GRID or None


# The stand-in, used only when terrain.json is absent.
PLATFORM = (40.0, 34.0)
DITCH_OUT, DITCH_HALF = 8.0, 6.0
HOLLOW = (26.0, -66.0)
KNOLL = (78.9, 43.3)


def _pulse(t, half):
    u = min(1.0, abs(t) / max(1e-6, half))
    return (1.0 - u * u) ** 2


def _standin(x, z):
    dx = max(0.0, abs(x) - PLATFORM[0])
    dz = max(0.0, abs(z) - PLATFORM[1])
    out = math.hypot(dx, dz)
    y = 0.0 if out <= 0.0 else max(-4.5, -out / 1.6)
    y -= 2.3 * _pulse(out - DITCH_OUT, DITCH_HALF)
    y -= 2.0 * _pulse(math.hypot(x - HOLLOW[0], z - HOLLOW[1]), 44.0)
    y += 1.8 * _pulse(math.hypot(x - KNOLL[0], z - KNOLL[1]), 32.0)
    ring = math.hypot(x * 0.75, z)
    if z < 0 or x < 0:
        y += 10.5 * _pulse(ring - 275.0, 130.0)
    return y + 1.2 * (math.sin(x * 0.031 + 1.3) * math.cos(z * 0.024 - 0.7))


def height(x, z):
    """Ground height in Three.js metres at plan (x, z), bilinear off the real
    grid. heights[iz][ix] at x = min[0] + ix*step, z = min[1] + iz*step."""
    g = terrain()
    if not g:
        return _standin(x, z)
    mn, st, n, H = g['min'], g['step'], g['n'], g['heights']
    fx = (x - mn[0]) / st
    fz = (z - mn[1]) / st
    ix = max(0, min(n[0] - 2, int(math.floor(fx))))
    iz = max(0, min(n[1] - 2, int(math.floor(fz))))
    tx, tz = fx - ix, fz - iz
    a = H[iz][ix] * (1 - tx) + H[iz][ix + 1] * tx
    b = H[iz + 1][ix] * (1 - tx) + H[iz + 1][ix + 1] * tx
    return a * (1 - tz) + b * tz


def sees(x, z, rise=0.9, steps=200):
    """Whether the hero lens can see a point `rise` metres above the ground.

    The one test that decided the placement table. ART-DIRECTION 4.1 puts the
    lens at y = -1.0 and 6.1 puts the ward floor at 0.0, so the sight line
    grazing the platform rises and never comes back: most of the world behind
    the castle is simply not in the picture, whatever is built there."""
    ty = height(x, z) + rise
    for i in range(1, steps):
        f = i / float(steps)
        px = 78.9 + (x - 78.9) * f
        pz = 43.3 + (z - 43.3) * f
        py = -1.0 + (ty + 1.0) * f
        if py < height(px, pz) + 0.06:
            return False
    return True


def load_glb(name, where=None):
    path = os.path.join(where or SCENE, name + '.glb')
    if not os.path.exists(path):
        return None
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o not in before]


def ground():
    """The real ground if build_ground.py has run, else a heightfield of the
    stand-in so the script still says something."""
    got = []
    for name in ('ground_platform', 'ground_outfield', 'ground_ridge'):
        objs = load_glb(name)
        if objs:
            got.extend(objs)
            print('GROUND  %s' % name)
    if got:
        return got
    print('GROUND  stand-in heightfield -- no ground_*.glb in %s' % SCENE)
    half, step = 210.0, 4.5
    n = int(2 * half / step) + 1
    me = bpy.data.meshes.new('ground')
    ob = bpy.data.objects.new('ground', me)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    grid = []
    for i in range(n):
        row = []
        x = -half + i * step
        for j in range(n):
            z = -half + j * step
            row.append(bm.verts.new(blend(x, height(x, z), z)))
        grid.append(row)
    for i in range(n - 1):
        for j in range(n - 1):
            bm.faces.new((grid[i][j], grid[i][j + 1],
                          grid[i + 1][j + 1], grid[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(lib.hexmat('turf', TURF_NIGHT, rough=0.95))
    for p in me.polygons:
        p.use_smooth = False
    return [ob]


# ---------------------------------------------------------------- the castle
#
# The real castle.glb if it is on disk. It matters more than it looks: the
# whole placement question for this asset is which ground the castle hides,
# and four boxes standing in for a 71 m ruin answer it wrongly in both
# directions -- a solid block occludes ground the breach lets through, and a
# block 6 m too wide occludes ground that is in the picture.

def castle():
    objs = load_glb('castle')
    if objs:
        print('CASTLE  castle.glb, %d objects' % len(objs))
        return objs
    print('CASTLE  four-block stand-in -- no castle.glb in %s' % SCENE)
    m = lib.hexmat('stone', STONE_DARK, rough=0.9)
    out = []
    for name, (cx, cy, cz), size in (
            ('curtain', (0, 5.5, 0), (58, 11, 52)),
            ('se_tower', (28.8, 9.7, 21.3), (10.4, 19.4, 10.4)),
            ('ne_tower', (28.8, 6.0, -21.3), (9.6, 12.0, 9.6)),
            ('keep', (-9.5, 11.7, -6.5), (12.0, 23.4, 10.0))):
        b = lib.box(name, (size[0], size[2], size[1]), loc=blend(cx, cy, cz))
        b.data.materials.append(m)
        out.append(b)
    return out


# ---------------------------------------------------------------- the sheets
#
# build_mist.py's placement table, verbatim: piece, Three.js (x, z), yaw about
# Three.js +Y, plan scale, depth scale, and how far the underside is seated
# BELOW the terrain at that point.

PLACEMENT = [
    ('mist_sheet_a', 8, -68, 0, 1.00, 1.00, 1.00, 0.05),
    ('mist_sheet_a', -12, -76, 0, 0.85, 1.00, 1.45, 0.05),
    ('mist_sheet_a', -14, -74, 104, 0.70, 1.00, 0.62, 0.05),
    ('mist_sheet_a', -20, -78, 90, 0.80, 1.00, 1.10, 0.05),
    ('mist_sheet_a', -18, -74, 45, 0.75, 1.00, 0.80, 0.05),
    ('mist_sheet_b', -8, -54, 0, 0.90, 0.45, 1.00, 0.05),
    ('mist_sheet_b', 4, -54, 0, 1.00, 0.45, 1.45, 0.05),
    ('mist_sheet_b', -2, -54, -8, 0.85, 0.50, 0.72, 0.05),
    ('mist_sheet_b', -24, -52, 6, 0.75, 0.45, 1.15, 0.05),
    ('mist_sheet_b', 20, -56, -12, 0.65, 0.50, 0.80, 0.05),
    ('mist_sheet_c', -64, 60, 0, 1.20, 1.00, 0.90, 0.05),
    ('mist_sheet_c', -76, 60, 0, 1.00, 1.00, 1.20, 0.05),
    ('mist_sheet_c', -72, 56, 45, 0.90, 1.00, 0.80, 0.05),
    ('mist_sheet_c', -80, 60, 45, 1.30, 1.00, 1.10, 0.05),
    ('mist_wisp', 70, 38, 12, 1.00, 1.00, 1.00, 0.05),
    ('mist_wisp', 68, 36, -140, 0.80, 1.00, 1.35, 0.05),
    ('mist_wisp', 66, 41, -22, 0.90, 1.00, 1.15, 0.05),
    ('mist_wisp', 72, 34, 160, 1.05, 1.00, 0.90, 0.05),
    ('mist_wisp', 0, -56, 40, 0.70, 0.55, 0.60, 0.05),
    ('mist_wisp', 8, -56, 88, 0.90, 0.55, 0.70, 0.05),
]


def seating(src, x, z, yaw, plan, narrow, deep, hem):
    """How badly an instance fails to touch the ground it is lying on.

    Returns (gap, core, rim) in metres: the largest air space under the slab,
    the ground standing through the middle 60 per cent of it, and the ground
    standing through the outer 40. Measured on a rotated grid over the real
    footprint -- a first version sampled an unrotated ellipse of the plan
    extents and reported a 32 m ribbon lying ALONG the ditch as falling 6.8 m
    across itself, which is the depth of the ditch measured at ninety degrees
    to the sheet. A check that is wrong in the alarming direction is worse
    than no check.

    Core and rim are separated because they mean opposite things. ART-DIRECTION
    5 group 7 sizes mist_sheet_b at 32 x 22 m and puts it in a ditch that is
    nearer 14 m between banks, so its edges MUST end up inside the banks -- and
    that is right, it is what makes a strip of mist look like it is lying in a
    trench rather than draped over one. A sheet whose MIDDLE is buried has
    simply disappeared.

    This is the measurement that matters most for this asset and it is not
    obvious: these are FLAT slabs, and a flat slab laid on a hollow touches it
    at the rim and bridges the middle, while one laid on a rise touches in the
    middle and lifts at the rim. At eleven per cent alpha the second case is a
    pale lens hanging in the air with sky under it, which is the failure mode
    the brief names."""
    ex = max(abs(v.co.x) for v in src.data.vertices) * plan
    ey = max(abs(v.co.y) for v in src.data.vertices) * plan * narrow
    box = max(v.co.z for v in src.data.vertices) * deep
    c, s = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    base = height(x, z) - hem * box
    gap = core = rim = 0.0
    for i in range(-3, 4):
        for j in range(-3, 4):
            r2 = (i / 3.0) ** 2 + (j / 3.0) ** 2
            if r2 > 1.0:
                continue
            u, v = ex * i / 3.0, ey * j / 3.0
            g = height(x + u * c - v * s, z + u * s + v * c)
            gap = max(gap, base - g)
            through = g - (base + box)
            if r2 <= 0.36:
                core = max(core, through)
            else:
                rim = max(rim, through)
    return gap, core, rim


def load(name):
    new = load_glb(name, where=cfg.OUT)
    if not new:
        raise SystemExit('no such model: %s in %s' % (name, cfg.OUT))
    for o in new:
        o.hide_render = True
    return [o for o in new if o.type == 'MESH'][0]


def sheets():
    masters = {}
    out = []
    tris = 0
    for name, x, z, yaw, plan, narrow, deep, sink in PLACEMENT:
        if name not in masters:
            masters[name] = load(name)
        src = masters[name]
        box = max(v.co.z for v in src.data.vertices) * deep
        ob = src.copy()
        ob.data = src.data
        bpy.context.collection.objects.link(ob)
        ob.hide_render = False
        # The bottom quarter of every piece is hem and is meant to be buried
        # (build_mist.py, HEM_FRACTION), so the seat is the hem plus whatever
        # extra this instance asks for. Computing it here rather than writing
        # it into the table means a change to the hem cannot leave twenty
        # instances quietly floating a hand's breadth off the grass.
        y = height(x, z) - (HEM * box + sink)
        ob.location = blend(x, y, z)
        ob.rotation_euler = (0.0, 0.0, math.radians(-yaw))
        ob.scale = (plan, plan * narrow, deep)
        out.append(ob)
        tris += sum(len(p.vertices) - 2 for p in src.data.polygons)
        top = y + box
        g = height(x, z)
        print('  %-13s three(%6.1f,%6.1f)  ground %+5.2f  top %+5.2f '
              ' = %.2f above local ground' % (name, x, z, g, top, top - g))
        if top - g > 2.4:
            print('     WARNING over the 2.4 m ceiling in ART-DIRECTION 5.7')
        if not sees(x, z, rise=max(0.2, top - g)):
            print('     hidden from the hero lens (occluded, not off frame)')
        gap, core, rim = seating(src, x, z, yaw, plan, narrow, deep, HEM)
        if gap > 0.25:
            print('     WARNING floats: %.2f m of air under it at the worst '
                  'point (sheet is %.2f m deep)' % (gap, box))
        elif core > box * 0.5:
            print('     WARNING buried: ground stands %.2f m through the '
                  'MIDDLE of a %.2f m sheet, so there is nothing left to see'
                  % (core, box))
        elif rim > 0.1:
            print('     rim buried %.2f m in the banks -- which is what a '
                  'sheet lying in a ditch is supposed to do' % rim)
        elif gap > 0.08:
            print('     %.2f m gap under it: seated, but only just' % gap)
    print('SHEETS  %d instances, %d triangles' % (len(out), tris))
    return out


# ---------------------------------------------------------------- lighting

def sky():
    """A two-band gradient world: zenith #080D18 over horizon #1C2C42.

    ART-DIRECTION 3.2 asks for a HemisphereLight rather than an AmbientLight
    precisely so upward-facing surfaces pick up cold sky and downward-facing
    ones go near black. A flat world colour here would flatten the mist's
    domed top into one value, which is the one thing it must not be."""
    w = bpy.data.worlds.new('night')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs['Strength'].default_value = 0.55
    tex = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = lib.srgb(SKY_HORIZON)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = lib.srgb(SKY_ZENITH)
    nt.links.new(tex.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    return w


def moon():
    """ART-DIRECTION 3.1: south-west, 34 degrees, behind the castle."""
    d = bpy.data.lights.new('moon', type='SUN')
    d.energy = 1.9
    d.color = lib.srgb(MOON_COLD)[:3]
    d.angle = math.radians(1.5)
    o = bpy.data.objects.new('moon', d)
    bpy.context.collection.objects.link(o)
    import mathutils
    v = -mathutils.Vector((-58.6, -58.6, 55.9))
    o.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    return o


def point_lights():
    """Only the two that matter to this asset.

    ART-DIRECTION 5 group 7: keep the sheets out of the point-light ranges,
    because a mist slab lit from inside by one is a glowing plastic sheet. The
    ward bonfire and the bridge lantern are the two whose ranges come anywhere
    near, so they are here to be checked against rather than for the look.
    Blender is in watts and Three.js in candela at decay 2, so the conversion
    is power = 4 * pi * intensity (the same one kit_shots.py uses)."""
    out = []
    for name, three, hexv, intensity in (
            ('bonfire', (24.0, 1.6, -2.0), 0xFF7A2E, 26.0),
            ('lantern', (48.0, -0.4, 24.0), 0xFFD08A, 3.5)):
        d = bpy.data.lights.new(name, type='POINT')
        d.energy = 4.0 * math.pi * intensity
        d.color = lib.srgb(hexv)[:3]
        d.shadow_soft_size = 0.25
        # ART-DIRECTION 3.4: no shadows on any of the seven point lights. That
        # is the affordable envelope and it is also a hazard for this asset --
        # an unshadowed bonfire inside the ward reaches straight through the
        # curtain wall and into the ditch, so whether a sheet lights up from
        # inside is a question this render has to be able to answer. Leaving
        # Blender's shadow on would answer a different one.
        d.use_shadow = False
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = blend(*three)
        out.append(o)
    return out


# ---------------------------------------------------------------- the fog
#
# THREE.FogExp2: factor = 1 - exp(-(density * depth)^2), mixed toward the fog
# colour. Applied in the compositor off the Z pass so the curve is the engine's
# and not an approximation of it -- a homogeneous volume in EEVEE integrates to
# 1 - exp(-sigma*z), which is a visibly different shape at the distances that
# matter here (9 per cent at the castle, 87 per cent at the ridge).

def fog_compositor():
    """Blender 5.2 note: the scene compositor is a NODE GROUP now --
    `scene.compositing_node_group`, wired to a Group Output, with generic
    ShaderNodeMath / ShaderNodeMix inside it. `scene.node_tree`,
    CompositorNodeComposite and CompositorNodeMath are all gone, and the first
    two fail loudly while the old MixRGB just quietly is not there."""
    sc = bpy.context.scene
    sc.view_layers[0].use_pass_z = True
    ng = bpy.data.node_groups.new('fog', 'CompositorNodeTree')
    ng.interface.new_socket(name='Image', in_out='OUTPUT',
                            socket_type='NodeSocketColor')
    sc.compositing_node_group = ng
    rl = ng.nodes.new('CompositorNodeRLayers')
    out = ng.nodes.new('NodeGroupOutput')

    def math_node(op, a=None, b=None):
        n = ng.nodes.new('ShaderNodeMath')
        n.operation = op
        if a is not None:
            n.inputs[0].default_value = a
        if b is not None:
            n.inputs[1].default_value = b
        return n

    scale = math_node('MULTIPLY', b=FOG_DENSITY)
    sq = math_node('POWER', b=2.0)
    neg = math_node('MULTIPLY', b=-1.0)
    ex = math_node('EXPONENT')
    inv = math_node('SUBTRACT', a=1.0)
    mix = ng.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['B'].default_value = lib.srgb(FOG)

    ng.links.new(rl.outputs['Depth'], scale.inputs[0])
    ng.links.new(scale.outputs[0], sq.inputs[0])
    ng.links.new(sq.outputs[0], neg.inputs[0])
    ng.links.new(neg.outputs[0], ex.inputs[0])
    ng.links.new(ex.outputs[0], inv.inputs[1])
    ng.links.new(inv.outputs[0], mix.inputs['Factor'])
    ng.links.new(rl.outputs['Image'], mix.inputs['A'])
    ng.links.new(mix.outputs['Result'], out.inputs[0])
    return mix


# ---------------------------------------------------------------- the camera

def hero(kind='hero'):
    """ART-DIRECTION 4.1 to the metre. `kind` picks one of three readings:

      hero    the published still
      ditch   the same lens dropped onto the bridge, 36 m out, where the ditch
              instances are read at nearly seven degrees
      hollow  turned onto the hollow alone, which is the case the global fog
              cannot do and therefore the one that has to be shown"""
    look = {
        'hero': ((78.9, -1.0, 43.3), (3.9, 9.3, -6.4), 32.0),
        'ditch': ((78.9, -1.0, 43.3), (44.0, -5.0, 14.0), 20.0),
        'hollow': ((78.9, -1.0, 43.3), (34.0, -4.6, -40.0), 22.0),
        # ART-DIRECTION 4.2, the intro move's start: 1.5 m ABOVE the ward
        # floor rather than 1.0 m below it. Those 2.5 m are the whole
        # difference between a frame in which the ground behind the
        # castle exists and one in which it does not, so the hollow is
        # judged from here.
        'start': ((92.0, 1.5, 52.0), (6.0, 11.0, -5.0), 32.0),
        # ART-DIRECTION 4.3's envelope, at the corner of it that opens the
        # hollow: azimuth at the -38 degree limit, polar 80 (the highest the
        # fence allows), distance 130 (the far limit). A sweep of the whole
        # envelope -- 975 sampled positions -- puts at least one hollow
        # instance in frame and unoccluded from 395 of them, and this is the
        # first. So mist_sheet_a is not dead geometry; it is simply not in the
        # held still, and this is the shot that proves it either way.
        'orbit': ((131.5, 31.9, -16.4), (3.9, 9.3, -6.4), 32.0),
    }[kind]
    cam = bpy.data.cameras.new('cam')
    cam.sensor_fit = 'VERTICAL'
    cam.angle_y = math.radians(look[2])
    cam.clip_start = 0.5
    cam.clip_end = 900.0
    ob = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(ob)
    ob.location = blend(*look[0])
    import mathutils
    d = mathutils.Vector(blend(*look[1])) - mathutils.Vector(blend(*look[0]))
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    return ob


# ---------------------------------------------------------------- main

def frame(cam, mist):
    """Where each instance actually lands in the frame, and how far away.

    ART-DIRECTION 4.1 gives a table of what sits where across the frame, and
    an instance that is off the edge of it is not a placement decision, it is
    a bug -- the first run of this script had the whole hollow at 129 per cent
    across and rendered a picture with no pooled mist in it at all, which
    looked exactly like a picture of mist that failed to read."""
    from bpy_extras.object_utils import world_to_camera_view
    import mathutils
    bpy.context.view_layer.update()
    sc = bpy.context.scene
    print('  %-13s %8s %8s %8s %8s' % ('piece', 'across%', 'down%', 'dist m',
                                       'deg up'))
    for o in mist:
        p = world_to_camera_view(sc, cam, o.matrix_world.translation)
        eye = cam.matrix_world.translation
        v = o.matrix_world.translation - mathutils.Vector(eye)
        rise = math.degrees(math.atan2(v.z, math.hypot(v.x, v.y)))
        rng = v.length
        edge = '' if 0.0 < p.x < 1.0 else '   OFF FRAME'
        print('  %-13s %7.1f  %7.1f  %7.1f  %7.2f%s'
              % (o.data.name, p.x * 100, (1 - p.y) * 100, rng, rise, edge))


def render(path):
    sc = bpy.context.scene
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('SHOT', path)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    # `solid` forces every sheet to alpha 1. It answers the one question the
    # translucent render cannot: whether a sheet that is contributing nothing
    # is too faint, or simply not on screen -- behind the platform, below the
    # frame, or the wrong side of the castle. Those look identical at 11 per
    # cent and want completely different fixes.
    solid = 'solid' in args
    # `x2` doubles the loader opacity. ART-DIRECTION 5 group 7 fixes it at
    # 0.11 and this does not argue with that -- it measures what the number
    # buys, so the scene author is choosing between two numbers they have both
    # seen rather than between a number and an adjective.
    boost = 2.0 if 'x2' in args else 1.0
    kinds = ([a for a in args if a not in ('solid', 'x2')]
             or ['hero', 'start', 'orbit'])

    lib.reset()
    sc = bpy.context.scene
    avail = [i.identifier for i in
             sc.render.bl_rna.properties['engine'].enum_items]
    for cand in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        if cand in avail:
            sc.render.engine = cand
            break
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 900
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    try:
        sc.eevee.taa_render_samples = 48
    except AttributeError:
        pass

    sky()
    moon()
    point_lights()
    ground()
    castle()
    mist = sheets()
    for o in mist:
        for slot in o.material_slots:
            m = slot.material
            if m and hasattr(m, 'surface_render_method'):
                m.surface_render_method = 'BLENDED'
                m.show_transparent_back = True
                m.use_backface_culling = False
                print('MIST MATERIAL %s blend_method=%s'
                      % (m.name, m.blend_method))
            if m and boost != 1.0:
                # Insert our own multiply rather than hunting for one in the
                # importer's graph: the glTF importer builds its own node
                # chain for baseColorFactor.a x COLOR_0.a and its shape is not
                # ours to rely on. A first attempt looked for a ShaderNodeMath
                # feeding Alpha, found none, and silently changed nothing --
                # which is the worst possible outcome for a measurement.
                b = m.node_tree.nodes['Principled BSDF']
                sock = b.inputs['Alpha']
                if sock.is_linked:
                    link = sock.links[0]
                    # Name the source BEFORE removing the link: removing it
                    # invalidates the wrapper and reading link.from_node then
                    # raises, which is how this printed a traceback instead of
                    # a measurement the first time.
                    src, from_sock = link.from_node.bl_idname, link.from_socket
                    mul = m.node_tree.nodes.new('ShaderNodeMath')
                    mul.operation = 'MULTIPLY'
                    mul.inputs[1].default_value = boost
                    m.node_tree.links.remove(link)
                    m.node_tree.links.new(from_sock, mul.inputs[0])
                    m.node_tree.links.new(mul.outputs[0], sock)
                    print('   alpha x%.2f (inserted after %s)' % (boost, src))
                else:
                    sock.default_value *= boost
                    print('   alpha x%.2f -> %.3f'
                          % (boost, sock.default_value))
            if m and solid:
                b = m.node_tree.nodes.get('Principled BSDF')
                if b:
                    for link in list(m.node_tree.links):
                        if link.to_socket == b.inputs['Alpha']:
                            m.node_tree.links.remove(link)
                    b.inputs['Alpha'].default_value = 1.0
                m.blend_method = 'OPAQUE'
    fog_compositor()

    out = os.path.join(cfg.SHOTS, '_scene')
    tag = 'solid_' if solid else ('x2_' if boost != 1.0 else '')
    for kind in kinds:
        cam = hero(kind)
        frame(cam, mist)
        for o in mist:
            o.hide_render = False
        render(os.path.join(out, '%s%s_mist.png' % (tag, kind)))
        for o in mist:
            o.hide_render = True
        render(os.path.join(out, '%s%s_bare.png' % (tag, kind)))
    print('SCENE   %s' % out)


if __name__ == '__main__':
    main()
