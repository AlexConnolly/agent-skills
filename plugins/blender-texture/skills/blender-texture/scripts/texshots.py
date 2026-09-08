# The material contact sheet: what you look at between passes.
#
#   blender --background --python texshots.py -- <model-name>
#
# Modelling has the flat-black silhouette — the shot that strips away
# everything you could hide behind. Texturing needs a different one, because a
# material has no correct outline to check against. The equivalent here is
# `mask_*.png`: each placement mask rendered on its own, in grey, on the model.
#
# That shot exists because "the moss is wrong" is not actionable and "the moss
# mask is covering the whole south wall instead of the bottom two metres" is.
# You cannot fix a placement you cannot see, and a colour render only tells you
# the model got greener.
#
# The other shot that earns its place is `rake.png`. Under flat front light a
# painted-on suggestion of texture and real micro-surface relief look the same;
# under a light skimming along the surface they do not. A material that only
# reads under flat light is not finished.
import bpy
import bmesh
import sys
import os
import math
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
import texconfig as cfg     # noqa: E402
import texlib as tx         # noqa: E402


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def setup(engine='CYCLES'):
    """Cycles by default, not EEVEE.

    EEVEE evaluates the Ambient Occlusion node as a constant, so `mask_cavity`
    - the one mask that works on flat-faced geometry - renders as flat grey and
    the mask view lies. EEVEE is fine for a quick colour look; it is not fine
    for anything you intend to judge a placement from."""
    sc = bpy.context.scene
    avail = [i.identifier for i in
             sc.render.bl_rna.properties['engine'].enum_items]
    for cand in (engine, 'BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        if cand in avail:
            sc.render.engine = cand
            break
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.resolution_x = sc.render.resolution_y = cfg.RES
    try:
        sc.eevee.taa_render_samples = 32
    except AttributeError:
        pass


def world(hex_value, strength=0.85, name='texworld'):
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = tx.srgb(hex_value)
    bg.inputs['Strength'].default_value = strength
    return w


def sun(from_vec, energy, name='sun'):
    d = bpy.data.lights.new(name, type='SUN')
    d.energy = energy
    d.color = tx.srgb(cfg.SUN)[:3]
    d.angle = math.radians(2.0)
    o = bpy.data.objects.new(name, d)
    v = mathutils.Vector((0, 0, 0)) - mathutils.Vector(from_vec)
    o.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(o)
    return o


def rake_light(target_size):
    """A sun almost level with the surface. Grazing light is the only thing
    that separates relief from a picture of relief."""
    el = math.radians(cfg.RAKE_ELEVATION_DEG)
    az = math.radians(cfg.RAKE_AZIMUTH_DEG)
    d = target_size * 8
    return sun((math.cos(el) * math.sin(az) * d,
                -math.cos(el) * math.cos(az) * d,
                math.sin(el) * d), cfg.SUN_ENERGY * 1.6, 'rake')


def camera(loc, look, lens=50, ortho=None):
    cam = bpy.data.cameras.new('cam')
    cam.lens = lens
    cam.clip_start = 0.001
    cam.clip_end = 5000
    if ortho:
        cam.type = 'ORTHO'
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    d = mathutils.Vector(look) - mathutils.Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    return ob


def bounds(objs):
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


def render(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('SHOT', path)


# ---------------------------------------------------------------- mask view

class MaskView:
    """Render one mask on the model as flat grey.

    Swaps every material for an emission driven by the mask socket, so what
    you see is exactly where the mask is strong — no lighting, no base colour,
    nothing to misread. White is 1, black is 0.

    This is the shot to reach for first when a material is wrong. Nine times
    out of ten the surface is fine and the placement is not."""

    def __init__(self, objs, build_mask):
        self.objs = [o for o in objs if o.type == 'MESH']
        self.build_mask = build_mask
        self.stash = []

    def __enter__(self):
        mat = bpy.data.materials.new('_maskview')
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nt.nodes.remove(n)
        out = nt.nodes['Material Output']
        em = nt.nodes.new('ShaderNodeEmission')
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])

        g = tx.Graph.__new__(tx.Graph)
        g.mat, g.nt, g._x, g._coord = mat, nt, -400, None
        g.bsdf = em
        socket = self.build_mask(g)
        nt.links.new(socket, em.inputs['Color'])

        self.mat = mat
        for o in self.objs:
            self.stash.append((o, list(o.data.materials),
                               [p.material_index for p in o.data.polygons]))
            o.data.materials.clear()
            o.data.materials.append(mat)
        self.world = bpy.context.scene.world
        world(0x000000, strength=0.0, name='texworld_mask')
        return self

    def __exit__(self, *exc):
        for o, mats, idx in self.stash:
            o.data.materials.clear()
            for m in mats:
                o.data.materials.append(m)
            for p, i in zip(o.data.polygons, idx):
                p.material_index = i
        bpy.context.scene.world = self.world
        bpy.data.materials.remove(self.mat)
        return False


def mask_stats(mask_png, all_png):
    """Measure a mask view: what fraction of the model it actually covers.

    "The moss looks thin" is not something you can act on twice. "8.5 percent,
    target 15" is. Reported against `all_png`, a constant-1 render of the same
    view, so coverage is a fraction of the *model* rather than of the frame.

    `soft` is the fraction sitting in the mushy middle — a mask that is mostly
    soft is a gradient, and a gradient is what weathering never looks like."""
    import numpy as np
    out = {}
    ref = bpy.data.images.load(all_png)
    ref.colorspace_settings.name = 'Non-Color'
    w, h = ref.size
    rbuf = np.empty(w * h * 4, dtype=np.float32)
    ref.pixels.foreach_get(rbuf)
    body = rbuf.reshape(-1, 4)[:, 0] > 0.02
    bpy.data.images.remove(ref)
    n_body = int(body.sum())
    if not n_body:
        return {'error': 'the constant-1 view is empty; is the model in frame?'}

    img = bpy.data.images.load(mask_png)
    # Non-Color, because the render is written display-referred and reading it
    # as sRGB inflates every value — enough to report coverage roughly twenty
    # points optimistic.
    img.colorspace_settings.name = 'Non-Color'
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    v = buf.reshape(-1, 4)[:, 0][body]
    bpy.data.images.remove(img)
    out['strong'] = float((v > 0.5).mean() * 100.0)
    out['soft'] = float(((v > 0.15) & (v < 0.5)).mean() * 100.0)
    out['mean'] = float(v.mean())
    return out


def sheet(objs, name, masks=None, hero=None):
    """The full set. `masks` is {label: fn(graph) -> socket}."""
    out = os.path.join(cfg.SHOTS, name)
    lo, hi = bounds(objs)
    size = max(hi[i] - lo[i] for i in range(3))
    centre = tuple((lo[i] + hi[i]) / 2 for i in range(3))

    el = math.radians(35.264389682754654)
    az = math.radians(45.0)
    hero_loc = (centre[0] + math.cos(el) * math.sin(az) * size * 4,
                centre[1] - math.cos(el) * math.cos(az) * size * 4,
                centre[2] + math.sin(el) * size * 4)

    # 1. lit hero
    key = sun(cfg.SUN_FROM, cfg.SUN_ENERGY)
    world(cfg.SKY)
    camera(hero_loc, centre, ortho=size * 1.5)
    render(os.path.join(out, 'hero.png'))

    # 2. close, under raking light
    bpy.data.objects.remove(key, do_unlink=True)
    rake_light(size)
    world(cfg.SKY, strength=0.15)
    close = (centre[0] + size * 0.75, centre[1] - size * 0.75,
             centre[2] + size * 0.35)
    camera(close, centre, lens=85)
    render(os.path.join(out, 'rake.png'))

    # 3. flat front light: the albedo on its own, no relief, no shadow
    for o in list(bpy.context.scene.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    world(0xFFFFFF, strength=1.0)
    camera(close, centre, lens=85)
    render(os.path.join(out, 'flat.png'))

    # 4. every mask, on its own — at hero framing and close, with numbers.
    #
    # Close framing matters: a 2.5 m band is about twenty pixels wide in the
    # hero shot, and you cannot judge whether an edge is ragged or smooth at
    # twenty pixels. Two passes of a mask can look identical at hero size and
    # obviously different close up.
    if masks:
        all_png = os.path.join(out, 'mask__all.png')
        with MaskView(objs, lambda g: g.colour(0xFFFFFF)):
            camera(hero_loc, centre, ortho=size * 1.5)
            render(all_png)
        stats = {}
        for label, fn in masks.items():
            with MaskView(objs, fn):
                camera(hero_loc, centre, ortho=size * 1.5)
                p = os.path.join(out, 'mask_%s.png' % label)
                render(p)
                camera(close, centre, lens=85)
                render(os.path.join(out, 'maskc_%s.png' % label))
            try:
                stats[label] = mask_stats(p, all_png)
            except Exception as e:                      # numpy or a bad render
                stats[label] = {'error': str(e)}
        print()
        print('%-14s %8s %8s %8s' % ('mask', 'strong%', 'soft%', 'mean'))
        for label, s in sorted(stats.items()):
            if 'error' in s:
                print('%-14s  %s' % (label, s['error']))
            else:
                print('%-14s %8.1f %8.1f %8.3f'
                      % (label, s['strong'], s['soft'], s['mean']))
        print('strong is the fraction of the model the mask actually covers.')
        print('a high soft fraction means a gradient, and weathering is not a')
        print('gradient - if soft exceeds strong, tighten the mask.')

    print('SHEET  %s' % out)
    return out


def main():
    args = argv()
    if not args:
        raise SystemExit('usage: texshots.py -- <model-name>')
    name = args[0]
    path = os.path.join(cfg.MODELS, name + '.glb')
    if not os.path.exists(path):
        raise SystemExit('no such model: ' + path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup()
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o not in before]
    sheet(objs, name)
    print()
    print('NOTE  no mask views were rendered.')
    print('      A baked glb carries no procedural graph, so there are no masks')
    print('      left to show. The mask views are the point of this sheet, so')
    print('      call sheet(objs, name, masks={...}) from your own skin script,')
    print('      before baking, while the graph still exists.')


if __name__ == '__main__':
    main()
