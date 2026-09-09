# The four prop groups in the world they belong to, from the camera that will
# see them.
#
#   blender --background --python props_shots.py -- crossing
#   blender --background --python props_shots.py -- crossing night
#   blender --background --python props_shots.py -- kit          (rocks/clutter)
#
# WHY THIS EXISTS INSTEAD OF shots.py
#
# shots.py renders one model against a ground plane at z=0 with a figure beside
# it, and that is the right sheet for a prop whose origin is its own footprint.
# Three of these pieces are not that. The bridge, the water and the track
# ribbon are authored in world coordinates 60 m from the origin and 3 to 7 m
# below the castle datum, so a ground plane at z=0 buries all three and every
# render in that sheet is of a black rectangle.
#
# More to the point, the questions worth asking about a crossing are: does the
# deck stand clear of the near lip from the lens; does the track meet the
# abutment; is the water where the ditch is. None of those can be asked of a
# model on its own, and all of them can be asked here, because this loads the
# ground agent's own ground_platform / ground_outfield / ground_ridge and puts
# the camera exactly where section 4.1 puts it.
import math
import os
import sys

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
sys.path.append(os.path.join(HERE, 'art_props'))

import artconfig as cfg      # noqa: E402
import lib                   # noqa: E402
import shots                 # noqa: E402
import props_common as pc    # noqa: E402
import route                 # noqa: E402


ASSETS = [os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'assets')),
          os.path.abspath(os.path.join(HERE, '..', 'docs', 'assets'))]

GROUND = ['ground_platform', 'ground_outfield', 'ground_ridge']

GROUPS = {
    'crossing': ['ditch_water', 'ditch_bridge', 'causeway_apron',
                 'track_ribbon'],
    'track': ['track_ribbon', 'causeway_apron'],
    'all': ['ditch_water', 'ditch_bridge', 'causeway_apron', 'track_ribbon'],
    'clutter': ['ditch_water', 'ditch_bridge', 'track_ribbon',
                'causeway_apron'],
}

# Where the group 8 pieces go, Three.js, for the in-place check. The wayside
# cross's position is argued in build_clutter.py; the rest are indicative and
# the scene's own placement.json is the authority.
#   (model, x, z, yaw about Blender Z in degrees, roll in degrees, y or None)
CLUTTER = [
    ('wayside_cross', 60.90, 37.80, 56.5, 0.0, None),
    ('carriers_cart', 66.30, 32.60, -26.0, 0.0, None),
    ('carriers_cart', 55.20, 40.40, 128.0, 96.0, None),      # tipped
    ('woodstack', 51.60, 41.80, 40.0, 0.0, None),
    ('tether_post', 63.90, 34.10, 0.0, 0.0, None),
    ('tether_post', 64.60, 35.60, 0.0, 0.0, None),
    ('hay_heap', 44.00, 47.00, 20.0, 0.0, None),
    ('rock_outcrop_a', 47.5, 20.0, 70.0, 0.0, None),
    ('boulder_a', 69.0, 30.0, 15.0, 0.0, None),
    ('boulder_b', 71.5, 36.5, 200.0, 0.0, None),
    ('scree_run', 52.0, 22.5, 55.0, 0.0, None),
    ('wall_mod_a', None, None, 0, 0, None),
]


def argv():
    a = sys.argv
    return a[a.index('--') + 1:] if '--' in a else []


def load(name, where=None):
    """Import <name>.glb from cfg.OUT, or from the shared assets directory."""
    paths = ([os.path.join(cfg.OUT, name + '.glb')] if where is None
             else [os.path.join(d, name + '.glb') for d in where])
    for p in paths:
        if os.path.exists(p):
            before = set(bpy.context.scene.objects)
            bpy.ops.import_scene.gltf(filepath=p)
            got = [o for o in bpy.context.scene.objects if o not in before]
            # The glTF importer leaves every node in QUATERNION rotation mode,
            # and assigning rotation_euler to an object in quaternion mode is
            # silently ignored. Nine wall modules and a cart that was supposed
            # to be lying on its side all came in bolt upright and axis-aligned
            # because of it, and the render looked like a kit that would not
            # tile. Anything that imports a glb and then orients it needs this
            # line.
            for o in got:
                o.rotation_mode = 'XYZ'
            print('LOAD %-18s %d objects' % (name, len(got)))
            return got
    print('MISS %-18s (looked in %s)' % (name, '; '.join(paths)))
    return []


def three_to_blender_cam(pos, target, lens, res_x, res_y):
    cam = bpy.data.cameras.new('hero')
    cam.lens = lens
    cam.clip_start = 0.2
    cam.clip_end = 900
    ob = bpy.data.objects.new('hero', cam)
    bpy.context.collection.objects.link(ob)
    p = cfg.to_blender(*pos)
    t = cfg.to_blender(*target)
    ob.location = p
    d = mathutils.Vector(t) - mathutils.Vector(p)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    sc = bpy.context.scene
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    return ob


def moon(energy, colour=pc.MOON_COLD):
    d = bpy.data.lights.new('moon', type='SUN')
    d.energy = energy
    d.color = lib.srgb(colour)[:3]
    d.angle = math.radians(0.6)
    o = bpy.data.objects.new('moon', d)
    v = mathutils.Vector((0, 0, 0)) - mathutils.Vector(cfg.SUN_FROM)
    o.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(o)
    return o


def figure_at(x, z, y=None):
    """A 1.75 m person standing on the ground at a Three.js point."""
    from terrain import Terrain
    t = Terrain()
    yy = t.h(x, z) if y is None else y
    return shots.scale_figure(at=cfg.to_blender(x, yy, z))


def main():
    args = argv()
    group = args[0] if args else 'crossing'
    night = 'night' in args

    shots.clear()
    shots.setup_render()
    if night:
        shots.world_colour(pc.SKY_HORIZON, strength=0.30)
        moon(2.4)
    else:
        shots.world_colour(0x9DB0C0, strength=0.9)
        moon(4.5, 0xFFF4E0)

    for g in GROUND:
        load(g, ASSETS)
    for name in GROUPS.get(group, GROUPS['all']):
        load(name)

    if group == 'clutter':
        from terrain import Terrain
        tr = Terrain()
        for (name, x, z, yaw, roll, y) in CLUTTER:
            if x is None:
                # a 9-module run of the wall kit, on the pitch, flipped
                # alternately: the only way to see whether the kit tiles.
                for i in range(9):
                    wx = 46.0 + i * 2.00 * 0.62
                    wz = 50.0 + i * 2.00 * 0.78
                    for o in load(name):
                        o.location = cfg.to_blender(wx, tr.h(wx, wz) - 0.05, wz)
                        o.rotation_euler = (0, 0, math.radians(
                            -51.4 + (180 if i % 2 else 0) + (1.5 if i % 3 else -1.2)))
                continue
            for o in load(name):
                o.location = cfg.to_blender(x, tr.h(x, z) if y is None else y, z)
                o.rotation_euler = (math.radians(roll), 0.0, math.radians(yaw))

    # Two figures: one on the bridge deck, one on the knoll where the camera
    # stands, so the scale of the crossing can be read against a person from
    # the same frame that judges its position.
    bx, bz = route.bridge_station(0.62)
    figure_at(bx + 1.2, bz + 0.6, route.deck_y(0.62))
    figure_at(74.0, 39.5)

    out = os.path.join(cfg.SHOTS, '_scene_' + group + ('_night' if night
                                                       else ''))

    # 1. the hero frame, section 4.1, at the real aspect and field of view
    three_to_blender_cam((78.9, -1.0, 43.3), (3.9, 9.3, -6.4), 35.33,
                         1920, 1080)
    shots.render(os.path.join(out, 'hero.png'), 1920, 1080)

    # 2. the same frame cropped to the crossing, so the bridge can be read at
    #    the size it is drawn rather than at the size it matters
    three_to_blender_cam((78.9, -1.0, 43.3), (route.bridge_station(0.5)[0],
                                              -3.4,
                                              route.bridge_station(0.5)[1]),
                         100.0, 1600, 900)
    shots.render(os.path.join(out, 'hero_crop.png'), 1600, 900)

    # 3. off the hero bearing, from the fenced end of the OrbitControls arc in
    #    section 4.3, where the bridge is seen across rather than along and the
    #    trestles have to hold up
    a = math.radians(-30.0)
    cx, cz = 3.9, -6.4
    dx, dz = 78.9 - cx, 43.3 - cz
    rx = dx * math.cos(a) - dz * math.sin(a)
    rz = dx * math.sin(a) + dz * math.cos(a)
    three_to_blender_cam((cx + rx * 0.72, 4.0, cz + rz * 0.72),
                         (route.bridge_station(0.5)[0], -4.0,
                          route.bridge_station(0.5)[1]), 50.0, 1600, 900)
    shots.render(os.path.join(out, 'oblique.png'), 1600, 900)

    # 4. a walk-up: what the bridge is, close, at the elevation of a person
    #    standing on the road
    ox, oz = route.bridge_station(1.0)
    ux, uz = route.crossing_axis()[1]
    three_to_blender_cam((ox + ux * 13.0, -1.2, oz + uz * 13.0),
                         (route.bridge_station(0.45)[0], -4.2,
                          route.bridge_station(0.45)[1]), 40.0, 1600, 900)
    shots.render(os.path.join(out, 'walkup.png'), 1600, 900)

    # 5. down the track from just behind and above the lens: whether the
    #    ribbon sits ON the ground or hovers over it, which no other view here
    #    can answer.
    three_to_blender_cam((82.0, 2.6, 47.0), (58.0, -3.0, 30.5), 35.33,
                         1600, 900)
    shots.render(os.path.join(out, 'track_down.png'), 1600, 900)

    # 6b. the near foreground at the real framing: the wayside cross against
    #     the horizon, which is the shot this whole group is judged on.
    three_to_blender_cam((78.9, -1.0, 43.3), (55.0, 2.0, 30.0), 60.0,
                         1600, 900)
    shots.render(os.path.join(out, 'foreground.png'), 1600, 900)

    # 6c. the drystone kit as a RUN. A module judged alone cannot show whether
    #     the kit tiles: what matters is the joint, the 4 cm overlap and
    #     whether nine modules flipped alternately read as one wall or as nine
    #     copies of one wall.
    if group == 'clutter':
        three_to_blender_cam((57.0, -1.2, 44.0), (52.0, -2.4, 57.0), 45.0,
                             1600, 700)
        shots.render(os.path.join(out, 'wall_run.png'), 1600, 700)

    # 6. straight down on the road where it passes the lens, for the ruts
    three_to_blender_cam((74.0, 14.0, 39.0), (74.0, -2.7, 39.0), 50.0,
                         1200, 1200)
    shots.render(os.path.join(out, 'track_plan.png'), 1200, 1200)

    print('SHEET   %s' % out)


if __name__ == '__main__':
    main()
