# The one camera that matters, in 16:9, with whatever is finished so far.
#
#   blender --background --python heroshot.py -- <outdir> <name> [<name> ...]
#
# shots.py frames a model in its own bounding box, which for 400 m of terrain
# is a survey photograph and tells you nothing about whether the ground works.
# ART-DIRECTION.md section 4.1 gives one fixed camera; this renders exactly it,
# several ways, because no single one of them can be trusted alone:
#
#   hero_day.png     bright key from the moon bearing. Reads the LANDFORM.
#   hero_clay.png    every material replaced by one grey. Reads FORM only, with
#                    no vertex colour to flatter or hide it.
#   hero_night.png   the real palette and the real light level. Reads VALUE.
#   hero_sky.png     objects flat black on a white sky. Reads the SKYLINE —
#                    whether the ridge stands above the platform's shoulder, and
#                    whether the far ground exists at all.
#   hero_rake.png    a second key from the CAMERA side. The moon is behind the
#                    castle, so every camera-facing slope is unlit and the real
#                    lighting is useless for reading whether a landform exists.
#   hero_ridge.png   the distant ridge white and everything else black, which
#                    is the only honest answer to "is the ridge in the picture".
#   hero_bands.png   the ground false-coloured in 1 m height bands, so the
#                    batter, the toe, the ditch and the knoll can be told apart
#                    and counted instead of guessed at.
#   intro_start.png  the section 4.2 intro camera, which stands 2.5 m ABOVE the
#                    ward datum and therefore sees the ditch, the toe and the
#                    outfield that the hero still cannot.
#   hero_grid.png    the day shot with a horizon rule and thirds drawn over it.
#   survey_*.png     the same world from up and back, for context only.
import bpy
import bmesh
import math
import mathutils
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
import artconfig as cfg     # noqa: E402
import lib                  # noqa: E402
import shots                # noqa: E402


RES_X = 1600
RES_Y = 900


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def world(hex_value, strength, name):
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = lib.srgb(hex_value)
    bg.inputs['Strength'].default_value = strength
    return w


class Isolate:
    """Paint one named object white and everything else black.

    The scene's aerial perspective is what separates the distant ridge from the
    near ground in value, and neither a night render nor a silhouette can show
    it: in the first everything is the same near-black, and in the second the
    ridge and the platform's shoulder are both flat black and merge into one
    outline eight pixels thick. A world volume was tried as a stand-in for
    FogExp2 and rendered the frame solid black. Painting the ridge white and
    everything else black answers the only question that matters - how much of
    it stands above the near skyline, and where across the frame - and answers
    it in pixels."""

    def __init__(self, objs, name):
        self.objs = [o for o in objs if o.type == 'MESH']
        self.name = name
        self.stash = []

    def __enter__(self):
        hot = lib.material('_iso_hot', (1, 1, 1, 1), rough=1.0, emissive=1.0)
        cold = lib.material('_iso_cold', (0, 0, 0, 1), rough=1.0, emissive=1.0)
        for o in self.objs:
            self.stash.append((o, list(o.data.materials),
                               [p.material_index for p in o.data.polygons]))
            o.data.materials.clear()
            o.data.materials.append(hot if o.name.startswith(self.name) else cold)
        self.world = bpy.context.scene.world
        world(0x000000, 1.0, 'iso_world')
        return self

    def __exit__(self, *exc):
        for o, mats, idx in self.stash:
            o.data.materials.clear()
            for m in mats:
                o.data.materials.append(m)
            for p, i in zip(o.data.polygons, idx):
                p.material_index = i
        bpy.context.scene.world = self.world
        return False


def key_light(hex_value, energy, name='key'):
    d = bpy.data.lights.new(name, type='SUN')
    d.energy = energy
    d.color = lib.srgb(hex_value)[:3]
    d.angle = math.radians(1.5)
    o = bpy.data.objects.new(name, d)
    v = -mathutils.Vector(cfg.SUN_FROM)
    o.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(o)
    return o


def hero_camera(loc=None, target=None):
    cam = bpy.data.cameras.new('hero')
    cam.sensor_fit = 'VERTICAL'
    cam.sensor_height = 24.0
    cam.lens = 12.0 / math.tan(math.radians(cfg.CAM_FOV_V_DEG / 2.0))
    cam.clip_start = 0.3
    cam.clip_end = 2000.0
    ob = bpy.data.objects.new('hero', cam)
    bpy.context.collection.objects.link(ob)
    ob.location = loc or cfg.CAM
    d = mathutils.Vector(target or cfg.CAM_TARGET) - mathutils.Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    return ob


def figure(at):
    """A 1.75 m person, so size is judged against a body and not a number."""
    made = shots.scale_figure(at=at)
    return made


def render(path):
    sc = bpy.context.scene
    sc.render.resolution_x = RES_X
    sc.render.resolution_y = RES_Y
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('SHOT', path)


def overlay(src, dst):
    """Thirds, the frame-y percentages the art direction quotes, and a rule on
    the horizon, drawn straight into the pixels."""
    import numpy as np
    img = bpy.data.images.load(src)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    a = buf.reshape(h, w, 4)
    # Blender's buffer is bottom-up.
    tilt = -cfg.HERO_ELEVATION_DEG
    for pct, col in ((13.0, (0.9, 0.3, 0.2)), (70.0, (0.2, 0.9, 0.9))):
        row = int(round((1.0 - pct / 100.0) * (h - 1)))
        a[row, :, :3] = col
    for elev, col in ((0.0, (1.0, 0.9, 0.2)),):
        frac = (tilt + cfg.CAM_FOV_V_DEG / 2 - elev) / cfg.CAM_FOV_V_DEG
        row = int(round((1.0 - frac) * (h - 1)))
        if 0 <= row < h:
            a[row, :, :3] = col
    for f in (1 / 3.0, 2 / 3.0):
        a[:, int(f * (w - 1)), :3] = (0.55, 0.55, 0.55)
    for f in (0.16, 0.32, 0.42, 0.47, 0.66, 0.85):
        a[::9, int(f * (w - 1)), :3] = (1.0, 0.4, 0.8)
    out = bpy.data.images.new('ov', w, h, alpha=True)
    out.colorspace_settings.name = 'Non-Color'
    out.pixels.foreach_set(a.ravel())
    out.filepath_raw = dst
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(img)
    bpy.data.images.remove(out)
    print('SHOT', dst, '(thirds; cyan 70%, red 13%, yellow = the true horizon)')


def height_bands(objs):
    """Replace the ground's material with a per-face ramp keyed to height, in
    one-metre bands. A landform that cannot be read in a night render can still
    be counted here, and a band that is missing is a feature that is missing."""
    import colorsys
    stash = []
    mats = []
    for k in range(-11, 9):
        r, g, b = colorsys.hsv_to_rgb((k * 0.085) % 1.0, 0.55,
                                      0.35 + 0.55 * ((k + 11) % 3) / 2.0)
        m = bpy.data.materials.new('_band%d' % k)
        m.use_nodes = True
        bsdf = m.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        bsdf.inputs['Roughness'].default_value = 1.0
        mats.append(m)
    for o in objs:
        if o.type != 'MESH' or not o.name.startswith('ground'):
            continue
        stash.append((o, list(o.data.materials),
                      [p.material_index for p in o.data.polygons]))
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)
        for p in o.data.polygons:
            z = (o.matrix_world @ p.center).z
            p.material_index = max(0, min(len(mats) - 1, int(math.floor(z)) + 11))
    return stash


def restore(stash):
    for o, ms, idx in stash:
        o.data.materials.clear()
        for m in ms:
            o.data.materials.append(m)
        for p, i in zip(o.data.polygons, idx):
            p.material_index = i


class Clay:
    """One flat grey on everything. Vertex colour is a good liar about form."""

    def __init__(self, objs, hex_value=0x8A8A88):
        self.objs = [o for o in objs if o.type == 'MESH']
        self.hex = hex_value
        self.stash = []

    def __enter__(self):
        m = lib.hexmat('_clay', self.hex, rough=0.88)
        for o in self.objs:
            self.stash.append((o, list(o.data.materials),
                               [p.material_index for p in o.data.polygons]))
            o.data.materials.clear()
            o.data.materials.append(m)
        return self

    def __exit__(self, *exc):
        for o, mats, idx in self.stash:
            o.data.materials.clear()
            for mm in mats:
                o.data.materials.append(mm)
            for p, i in zip(o.data.polygons, idx):
                p.material_index = i
        return False


def main():
    args = argv()
    if len(args) < 2:
        raise SystemExit('usage: heroshot.py -- <outdir> <name> [<name> ...]')
    out = args[0]
    names = args[1:]

    shots.clear()
    shots.setup_render()
    loaded = []
    for n in names:
        loaded += shots.load_glb(n)
    meshes = [o for o in loaded if o.type == 'MESH']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    lo, hi = shots.bounds(meshes)
    print('LOADED %s  %d objects  %d tris' % (', '.join(names), len(meshes), tris))
    print('BOUNDS x %+.1f..%+.1f  y %+.1f..%+.1f  z %+.1f..%+.1f'
          % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))

    # A person on the knoll beside the camera, and one on the platform toe, so
    # the levels are read against a body.
    # Heights are 6.1 levels, so a figure that does not stand on the ground is
    # a level that is wrong.
    fig = figure((70.0, -38.5, -2.70))          # the drove road, 12 m out
    fig += figure((49.6, -27.8, -4.50))         # the platform toe
    fig += figure((20.0, -36.0, 0.00))          # the berm, south of the gate

    hero_camera()

    # ---- day: the landform ----
    world(0x8FA6BC, 0.62, 'hero_day')
    sun = key_light(0xFFF2DC, 3.4)
    render(os.path.join(out, 'hero_day.png'))
    overlay(os.path.join(out, 'hero_day.png'), os.path.join(out, 'hero_grid.png'))

    # ---- rake: a key from the camera side, so slopes facing us are lit ----
    rake = key_light(0xFFF2DC, 2.6, 'rake')
    rake.rotation_euler = (mathutils.Vector((0, 0, 0))
                           - mathutils.Vector((62.0, -70.0, 26.0)))         .to_track_quat('-Z', 'Y').to_euler()
    sun.data.energy = 0.9
    render(os.path.join(out, 'hero_rake.png'))

    # ---- clay: the form, with nothing to hide behind ----
    # A hard key and almost no fill: the ambient that makes hero_day.png
    # readable also flattens every slope in it, and the whole point of this
    # frame is the shape of the slopes.
    world(0x8FA6BC, 0.14, 'hero_clay')
    rake.data.energy = 4.4
    sun.data.energy = 0.0
    with Clay(meshes + fig):
        render(os.path.join(out, 'hero_clay.png'))
    world(0x8FA6BC, 0.62, 'hero_day')
    rake.data.energy = 2.6
    sun.data.energy = 0.9

    # ---- height bands: which surface is which, countable ----
    stash = height_bands(meshes)
    render(os.path.join(out, 'hero_bands.png'))
    restore(stash)
    bpy.data.objects.remove(rake, do_unlink=True)
    sun.data.energy = 3.4

    # ---- skyline: what stands against the sky ----
    shots.show(fig, False)
    with shots.Silhouette(meshes):
        render(os.path.join(out, 'hero_sky.png'))
    shots.show(fig, True)

    # ---- night: the real value ----
    world(0x101B2C, 0.55, 'hero_night')
    sun.data.energy = 0.55
    sun.data.color = lib.srgb(0xAFC8EC)[:3]
    render(os.path.join(out, 'hero_night.png'))

    # ---- how much of the distant ridge is actually in the picture ----
    shots.show(fig, False)
    with Isolate(meshes, 'ground_ridge'):
        render(os.path.join(out, 'hero_ridge.png'))
    shots.show(fig, True)

    # ---- the intro camera, section 4.2: above the platform, so the ditch,
    #      the toe and the outfield are all in shot and can be checked ----
    world(0x8FA6BC, 0.62, 'hero_day')
    sun.data.energy = 3.4
    sun.data.color = lib.srgb(0xFFF2DC)[:3]
    hero_camera(loc=(92.0, -52.0, 1.5), target=(6.0, 5.0, 11.0))
    render(os.path.join(out, 'intro_start.png'))

    # ---- context ----
    world(0x8FA6BC, 0.62, 'hero_day')
    sun.data.energy = 3.4
    sun.data.color = lib.srgb(0xFFF2DC)[:3]
    hero_camera(loc=(240.0, -190.0, 120.0), target=(0.0, 0.0, -2.0))
    render(os.path.join(out, 'survey_high.png'))
    hero_camera(loc=(140.0, -78.0, 6.0), target=(10.0, -10.0, -3.0))
    render(os.path.join(out, 'survey_low.png'))
    hero_camera(loc=(60.0, -240.0, 40.0), target=(0.0, 0.0, -3.0))
    render(os.path.join(out, 'survey_south.png'))
    print('SHEET %s' % out)


main()
