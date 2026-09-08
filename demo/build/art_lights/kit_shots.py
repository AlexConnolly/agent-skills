# The whole fire kit in one frame, under the scene's own lights.
#
#   blender --background --python kit_shots.py
#
# shots.py renders one model at a time against a moon and a sky. That is the
# right sheet for judging a shape, and it is the wrong sheet for judging a
# LIGHT, because ART-DIRECTION 3.4 is explicit that in this scene the emissive
# materials do the look and seven point lights do the spill -- an emissive
# material illuminates nothing, so without the point light beside it a brazier
# is an orange sticker on a black wall. This script puts the point lights in.
#
# It also answers the question a single-model sheet cannot: whether eleven
# separately-built pieces agree with each other about scale and about how
# bright fire is.
#
# Faithful to the Three.js scene where it can be, and honest where it cannot:
#
#   * point lights only, no ray-traced GI, because a THREE.MeshStandardMaterial
#     with an emissive factor does not light its neighbours either;
#   * Blender point lights are in watts and Three.js point lights are in
#     candela with decay 2, so power = 4*pi*intensity;
#   * no bloom. EEVEE Next has no bloom pass, and the published scene runs
#     UnrealBloomPass at threshold 0.85 BEFORE tone mapping, which will spread
#     and soften every fire core here. Read these renders as the fires at their
#     hardest and least flattering.
import bpy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

import artconfig as cfg      # noqa: E402
import lib                   # noqa: E402
import shots                 # noqa: E402


# ART-DIRECTION 2 and 3.
SKY_ZENITH = 0x080D18
TURF_NIGHT = 0x1A2419
MOON_COLD = 0xAFC8EC

# (model, x, yaw, point light or None)
#   light = (colour, three.js intensity, distance, height above the base,
#            y offset -- panes are lit from BEHIND the wall they sit in)
LAYOUT = [
    ('bonfire',      0.0,   0.0, (0xFF7A2E, 26.0, 32.0, 1.10, 0.0)),
    ('brazier',      2.9,   0.0, (0xFF9A3C,  9.0, 18.0, 1.05, 0.0)),
    ('lamp_post',    4.4, 180.0, None),
    ('lantern',      4.4, 180.0, (0xFFD08A,  3.5, 12.0, 0.17, 0.0)),
    ('cresset',      5.7,   0.0, None),          # section 3.4 gives it no light
    ('pane_window',  7.3,   0.0, (0xFFBE6A,  3.0, 10.0, 1.20, 0.9)),
    ('shutter',      8.0,   0.0, None),
    ('pane_hall',    9.4,   0.0, None),
    ('pane_loop',   10.4,   0.0, None),
    ('pane_lancet', 11.4,   0.0, None),
    ('pane_passage', 13.0,  0.0, None),
    ('oven_mouth',  14.6,   0.0, (0xFF7A2E,  6.0, 14.0, 0.35, 0.0)),
    ('plume_low',   18.0,   0.0, None),
    ('plume_tall',  22.5,   0.0, None),
]

# ART-DIRECTION 3.6, applied here the way docs/js/materials.js will apply it on
# load. Without this every emissive surface renders at the 1.0 it was built at,
# a lit window comes out as bright as the heart of a bonfire, and the balance
# the whole picture depends on cannot be judged at all -- which is exactly what
# the first version of this render showed.
#
# Keyed by (model, material) because 3.6 gives one material name two
# intensities: the bonfire heart is 6.0 and a brazier basket core is 4.5.
INTENSITY = {
    ('bonfire', 'emis_fire_core'): 6.0,
    ('brazier', 'emis_fire_core'): 4.5,
    ('*', 'emis_fire_flame'): 3.0,
    ('cresset', 'emis_fire_flame'): 3.5,
    ('*', 'emis_ember'): 2.0,
    ('oven_mouth', 'emis_ember'): 2.5,
    ('lantern', 'emis_tallow'): 2.2,
    ('*', 'emis_tallow'): 1.6,
    ('pane_passage', 'emis_tallow'): 1.2,
}


def tune(objs, model):
    """Set Emission Strength from the table, on this model's own copies of the
    materials. Every glb import brings in its own datablock, so a per-model
    number is reachable here just as it is in scene code."""
    seen = set()
    for o in objs:
        for slot in getattr(o.data, 'materials', []) or []:
            if slot is None or slot.name in seen:
                continue
            seen.add(slot.name)
            base = slot.name.split('.')[0]        # 'emis_tallow.001'
            k = INTENSITY.get((model, base), INTENSITY.get(('*', base)))
            if k is None:
                continue
            b = slot.node_tree.nodes.get('Principled BSDF')
            if b and 'Emission Strength' in b.inputs:
                b.inputs['Emission Strength'].default_value = k

# The lantern hangs off the lamp post's hook rather than standing on the floor.
HUNG = {'lantern': (0.0, -0.262, 1.86)}   # on the hook, which reaches -Y


def view_transform():
    """Three.js runs ACESFilmicToneMapping through an OutputPass, with
    NeutralToneMapping named in ART-DIRECTION 8.2 as the fallback if the fires
    clip. Take the closest thing this build offers, so the fire cores roll off
    the way they will on the page instead of clipping to a flat orange plate
    under Standard."""
    sc = bpy.context.scene
    avail = [i.identifier for i in
             sc.view_settings.bl_rna.properties['view_transform'].enum_items]
    for cand in ('Khronos PBR Neutral', 'AgX', 'Filmic', 'Standard'):
        if cand in avail:
            sc.view_settings.view_transform = cand
            print('VIEW    %s   / available: %s' % (cand, ', '.join(avail)))
            return


def point_light(name, at, hexcolour, intensity, distance):
    d = bpy.data.lights.new(name, type='POINT')
    # Three.js decay 2 gives illuminance I / d^2; a Blender point lamp of P
    # watts gives P / (4 pi d^2). Same falloff, so the powers convert exactly.
    d.energy = 4.0 * math.pi * intensity
    d.color = lib.srgb(hexcolour)[:3]
    d.shadow_soft_size = 0.10
    d.use_custom_distance = True
    d.cutoff_distance = distance
    o = bpy.data.objects.new(name, d)
    o.location = at
    bpy.context.collection.objects.link(o)
    return o


def main():
    shots.clear()
    shots.setup_render()
    view_transform()
    # The sky itself, not a stand-in: at night the hemisphere fill IS most of
    # what a camera-facing surface gets.
    shots.world_colour(SKY_ZENITH, strength=1.4)
    shots.sun()
    ground = shots.ground(size=90)
    ground.data.materials.clear()
    ground.data.materials.append(lib.hexmat('_turf', TURF_NIGHT, rough=1.0))

    loaded = []
    for name, x, yaw, light in LAYOUT:
        objs = shots.load_glb(name)
        off = HUNG.get(name, (0.0, 0.0, 0.0))
        for o in objs:
            o.location = (o.location.x + x + off[0],
                          o.location.y + off[1],
                          o.location.z + off[2])
            o.rotation_euler.z += math.radians(yaw)
        tune(objs, name)
        loaded += objs
        if light:
            point_light('key_' + name, (x, light[4], off[2] + light[3]),
                        light[0], light[1], light[2])
    shots.scale_figure(at=(-2.2, 0.0, 0.0))

    out = os.path.join(cfg.SHOTS, '_kit')

    # 1. The kit, close, so all fourteen pieces can be compared with each other
    #    and with a 1.75 m figure.
    shots.camera((6.0, -26.0, 4.2), (6.0, 0.0, 1.5), lens=40)
    shots.render(os.path.join(out, 'kit_close.png'), 1900, 780)

    # 2. The fires alone at the distance the hero camera reads them from, and
    #    at the hero camera's own grazing elevation. 26 px/m at 1080 lines.
    shots.camera((2.0, -71.0, 2.6), (2.0, 0.0, 1.0), lens=cfg.HERO_LENS)
    shots.render(os.path.join(out, 'kit_71m.png'), 1920, 1080)

    # 3. The same, rendered small for real and blown up: what a viewer's eye
    #    actually receives.
    shots.camera((2.0, -71.0, 2.6), (2.0, 0.0, 1.0), lens=cfg.HERO_LENS)
    shots.render(os.path.join(out, 'kit_71m_small.png'), 480, 270)
    shots.upscale(os.path.join(out, 'kit_71m_small.png'),
                  os.path.join(out, 'kit_71m_small_x4.png'), 4)

    # 4. The plumes, from far enough back to see all thirteen metres of one.
    shots.camera((20.0, -46.0, 9.0), (20.0, 0.0, 7.0), lens=52)
    shots.render(os.path.join(out, 'kit_plumes.png'), 1400, 900)

    print('SHEET   %s' % out)


if __name__ == '__main__':
    main()
