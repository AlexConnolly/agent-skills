# Regression tests for the blender-model toolkit.
#
#   blender --background --python tests/test_toolkit.py
#
# Exits non-zero on failure. Every test here corresponds to a fault that
# actually shipped and was caught by looking at a render — the point of the
# file is that the next one gets caught here instead, in two seconds.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SCRIPTS = os.path.join(ROOT, 'plugins', 'blender-model', 'skills',
                       'blender-model', 'scripts')
sys.path.insert(0, SCRIPTS)

# Keep test output out of the way of any real project.
os.environ.setdefault('ART_OUT', os.path.join(HERE, '.out'))
os.environ.setdefault('ART_SHOTS', os.path.join(HERE, '.shots'))

import bpy                          # noqa: E402
import bmesh                        # noqa: E402
import lib                          # noqa: E402
from boxmodel import Form           # noqa: E402

FAILED = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('ok' if cond else 'FAIL', name,
                         '' if cond else '   -> ' + detail))
    if not cond:
        FAILED.append(name)


def extent(form, axis):
    i = {'x': 0, 'y': 1, 'z': 2}[axis]
    vs = [v.co[i] for v in form.bm.verts]
    return min(vs), max(vs)


# --------------------------------------------------------------- Form basics

def test_size_is_full_extent():
    """`size` is the full extent, matching lib.box() — not the half extent
    bmesh.ops.create_cube takes."""
    f = Form(size=(2.0, 4.0, 6.0))
    for axis, want in (('x', 2.0), ('y', 4.0), ('z', 6.0)):
        lo, hi = extent(f, axis)
        check('Form size is full extent (%s)' % axis, abs((hi - lo) - want) < 1e-6,
              'got %.3f, want %.3f' % (hi - lo, want))


def test_cut_at_preserves_the_mesh():
    """cut_at once collapsed the entire form onto the cut plane: it diffed the
    vertex set across subdivide_edges, which invalidates the old wrappers, so
    every vertex tested as new and got snapped."""
    f = Form(size=(6.0, 4.2, 2.3))
    f.cut_at('y', [0.0])
    lo, hi = extent(f, 'y')
    check('cut_at preserves width', abs(hi - lo - 4.2) < 1e-6,
          'collapsed to %.3f wide' % (hi - lo))

    g = Form(size=(6.0, 4.2, 2.3))
    g.cut_at('x', [1.0])
    lo, hi = extent(g, 'x')
    xs = sorted({round(v.co.x, 4) for v in g.bm.verts})
    check('cut_at preserves length', abs(hi - lo - 6.0) < 1e-6,
          'collapsed to %.3f long' % (hi - lo))
    check('cut_at puts the ring on the station', 1.0 in xs,
          'distinct x = %s' % xs)


def test_unknown_face_direction_raises():
    """An unrecognised direction name must not silently match every face."""
    f = Form(size=(1, 1, 1))
    try:
        f.faces(normal='up')
        check('faces() rejects a bad direction', False, 'no exception raised')
    except KeyError:
        check('faces() rejects a bad direction', True)


def test_inset_returns_inner_faces():
    """inset must return the shrunk inner face, not bmesh's ring of new rim
    faces — extruding the rim grows a fin instead of a limb."""
    f = Form(size=(2.0, 2.0, 2.0))
    top = f.face(normal='+z')
    before = top[0].calc_area()
    inner = f.inset(top, thickness=0.4)
    check('inset returns one face', len(inner) == 1, 'got %d' % len(inner))
    if inner:
        after = inner[0].calc_area()
        check('inset shrinks the returned face', after < before,
              'area %.3f -> %.3f' % (before, after))


def test_extrude_leaves_no_internal_wall():
    f = Form(size=(1, 1, 1))
    f.extrude(f.face(normal='+z'), move=(0, 0, 1))
    interior = [e for e in f.bm.edges if len(e.link_faces) > 2]
    check('extrude leaves no internal wall', not interior,
          '%d non-manifold edges' % len(interior))


# --------------------------------------------------------------- lib

def test_srgb_endpoints():
    check('srgb(0x000000) is black', lib.srgb(0x000000)[:3] == (0.0, 0.0, 0.0))
    w = lib.srgb(0xFFFFFF)
    check('srgb(0xFFFFFF) is white', all(abs(c - 1.0) < 1e-9 for c in w[:3]))
    mid = lib.srgb(0x808080)[0]
    # 0x80 is ~0.216 linear, not 0.502. Getting this wrong washes out a palette.
    check('srgb is a transfer function, not a pass-through',
          0.20 < mid < 0.23, 'got %.4f' % mid)


def test_merge_into_keeps_per_face_materials():
    """merge_into(mat=...) replaces every part's materials. Without it, the
    join must preserve per-face assignments made by repaint()."""
    lib.reset()
    red = lib.hexmat('t_red', 0xFF0000)
    blue = lib.hexmat('t_blue', 0x0000FF)
    a = lib.box('a', (1, 1, 1), (0, 0, 0.5))
    lib.repaint(a, [(red, lambda c: True), (blue, lambda c: c.z > 0.4)])
    b = lib.box('b', (1, 1, 1), (2, 0, 0.5))
    lib.attach(b, None, red)
    merged = lib.merge_into('m', [a, b], None)
    names = {m.name for m in merged.data.materials if m}
    check('merge_into without mat keeps both materials',
          {'t_red', 't_blue'} <= names, 'slots = %s' % sorted(names))
    used = {merged.data.materials[p.material_index].name
            for p in merged.data.polygons}
    check('merge_into without mat keeps the per-face assignment',
          't_blue' in used, 'materials actually used = %s' % sorted(used))


def test_merge_into_with_mat_overrides():
    lib.reset()
    red = lib.hexmat('t_red', 0xFF0000)
    green = lib.hexmat('t_green', 0x00FF00)
    a = lib.box('a', (1, 1, 1), (0, 0, 0.5))
    lib.attach(a, None, red)
    merged = lib.merge_into('m', [a], None, green)
    names = [m.name for m in merged.data.materials if m]
    check('merge_into with mat replaces materials', names == ['t_green'],
          'slots = %s' % names)


def test_repaint_accepts_a_normal_aware_test():
    lib.reset()
    base = lib.hexmat('t_base', 0x888888)
    top = lib.hexmat('t_top', 0x00FF00)
    o = lib.box('o', (2, 2, 2))
    lib.repaint(o, [(base, lambda c: True), (top, lambda c, n: n.z > 0.7)])
    used = {o.data.materials[p.material_index].name for p in o.data.polygons}
    check('repaint accepts a (centre, normal) test', 't_top' in used,
          'materials used = %s' % sorted(used))


def test_loft_is_closed():
    lib.reset()
    stations = [(x, [(-1, 0), (1, 0), (1, 2), (-1, 2)]) for x in (0.0, 1.0, 2.0)]
    o = lib.loft('l', stations)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    open_edges = [e for e in bm.edges if len(e.link_faces) < 2]
    check('loft with cap_ends is closed', not open_edges,
          '%d boundary edges' % len(open_edges))
    bm.free()


def test_ring_has_a_hole():
    """A ring must not be a solid disc — the hole is most of what reads."""
    lib.reset()
    o = lib.ring('r', 0.5, 1.0, 0.2)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    inner = [v for v in bm.verts if v.co.x ** 2 + v.co.y ** 2 < 0.6 ** 2]
    check('ring has an inner wall', inner, 'no vertices at the inner radius')
    centre = [v for v in bm.verts if v.co.x ** 2 + v.co.y ** 2 < 0.1 ** 2]
    check('ring has no centre vertex', not centre,
          '%d vertices at the axis' % len(centre))
    bm.free()


# --------------------------------------------------------------- shots.py

def test_silhouette_restores_materials_and_sky():
    """materials.clear() zeroes every polygon's material_index, and the
    silhouette pass must put both the slots and the indices back — otherwise
    every shot rendered after it comes out in one flat colour. The white sky
    must not leak either."""
    import shots
    lib.reset()
    shots.world_colour(0x336699)
    sky_before = tuple(bpy.context.scene.world.node_tree
                       .nodes['Background'].inputs['Color'].default_value)

    red = lib.hexmat('t_red', 0xFF0000)
    blue = lib.hexmat('t_blue', 0x0000FF)
    o = lib.box('o', (2, 2, 2))
    lib.repaint(o, [(red, lambda c: True), (blue, lambda c: c.z > 0.9)])
    idx_before = [p.material_index for p in o.data.polygons]
    names_before = [m.name for m in o.data.materials if m]

    with shots.Silhouette([o]):
        inside = [m.name for m in o.data.materials if m]
        check('silhouette swaps the material', inside == ['_silhouette'],
              'got %s' % inside)

    check('silhouette restores the material slots',
          [m.name for m in o.data.materials if m] == names_before,
          'got %s want %s' % ([m.name for m in o.data.materials if m],
                              names_before))
    check('silhouette restores per-face material indices',
          [p.material_index for p in o.data.polygons] == idx_before,
          'indices changed')

    sky_after = tuple(bpy.context.scene.world.node_tree
                      .nodes['Background'].inputs['Color'].default_value)
    check('silhouette does not leak its white sky', sky_after == sky_before,
          'sky %s -> %s' % (sky_before, sky_after))


# --------------------------------------------------------------- export

def test_export_reports_ground_contact():
    lib.reset()
    lib.box('floating', (1, 1, 1), (0, 0, 3.0))
    report = []
    lib.export('t_floating', report)
    name, tris, lo, hi, size = report[0]
    check('export reports the floor height', abs(lo - 2.5) < 1e-4,
          'floor reported as %.3f, expected 2.5' % lo)
    check('export reports triangles', tris == 12, 'got %d' % tris)


def test_bounds_are_tight_for_a_rotated_object():
    """bound_box is the object's LOCAL axis-aligned box. Transforming its eight
    corners through a rotation measures the box around the rotated box, which
    is bigger than the mesh — enough to misreport dimensions and misframe every
    shot."""
    import math
    import shots
    lib.reset()
    o = lib.box('spun', (4.0, 1.0, 1.0))
    o.rotation_euler = (0.0, 0.0, math.radians(45.0))
    bpy.context.view_layer.update()
    lo, hi = shots.bounds([o])
    want = 4.0 / math.sqrt(2.0) + 1.0 / math.sqrt(2.0)     # 3.536
    got = hi[0] - lo[0]
    check('bounds are tight for a rotated object', abs(got - want) < 1e-3,
          'got %.3f, want %.3f' % (got, want))


def main():
    for fn in (test_size_is_full_extent,
               test_cut_at_preserves_the_mesh,
               test_unknown_face_direction_raises,
               test_inset_returns_inner_faces,
               test_extrude_leaves_no_internal_wall,
               test_srgb_endpoints,
               test_merge_into_keeps_per_face_materials,
               test_merge_into_with_mat_overrides,
               test_repaint_accepts_a_normal_aware_test,
               test_loft_is_closed,
               test_ring_has_a_hole,
               test_silhouette_restores_materials_and_sky,
               test_export_reports_ground_contact,
               test_bounds_are_tight_for_a_rotated_object):
        print('--- %s' % fn.__name__)
        fn()
    print()
    if FAILED:
        print('%d FAILED: %s' % (len(FAILED), ', '.join(FAILED)))
        sys.exit(1)
    print('all tests passed')


main()
