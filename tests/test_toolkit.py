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


def test_boolean_cuts_a_hole_and_stays_closed():
    lib.reset()
    stone = lib.hexmat('t_stone', 0xC6C0B4)
    dark = lib.hexmat('t_dark', 0x1A1A1A)
    wall = lib.box('wall', (6.0, 0.6, 3.0), (0, 0, 1.5))
    lib.attach(wall, None, stone)
    before = sum(len(p.vertices) - 2 for p in wall.data.polygons)

    lib.hole(wall, (0.7, 0.6, 1.1), (0.0, 0, 1.7), mat=dark)

    after = sum(len(p.vertices) - 2 for p in wall.data.polygons)
    check('boolean adds geometry', after > before,
          '%d -> %d tris' % (before, after))

    bm = bmesh.new()
    bm.from_mesh(wall.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    openings = [e for e in bm.edges if len(e.link_faces) < 2]
    check('boolean leaves the mesh closed', not openings,
          '%d boundary edges' % len(openings))
    bm.free()

    used = {wall.data.materials[p.material_index].name
            for p in wall.data.polygons}
    check('boolean transfers the tool material to the reveal',
          't_dark' in used, 'materials used = %s' % sorted(used))

    # the hole must actually pass through: no faces left spanning its middle
    inside = [p for p in wall.data.polygons
              if abs(p.center.x) < 0.3 and abs(p.center.z - 1.7) < 0.4
              and abs(p.normal.y) > 0.9]
    check('boolean leaves no web across the opening', not inside,
          '%d faces spanning the hole' % len(inside))


def test_fuse_removes_the_interior_wall():
    lib.reset()
    a = lib.box('a', (2, 2, 2))
    b = lib.box('b', (2, 2, 2), (1.0, 0, 0))
    lib.fuse(a, b)
    bm = bmesh.new()
    bm.from_mesh(a.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    interior = [e for e in bm.edges if len(e.link_faces) > 2]
    openings = [e for e in bm.edges if len(e.link_faces) < 2]
    check('fuse leaves one closed surface',
          not interior and not openings,
          '%d non-manifold, %d boundary' % (len(interior), len(openings)))
    bm.free()


def test_revolve_makes_a_closed_shell():
    """A goblet outline - up the outside, over the rim, down the inside -
    revolved must give a real thin-walled shell, not a solid lump."""
    lib.reset()
    outline = [(0.20, 0.00), (0.45, 0.00), (0.45, 0.60), (0.40, 0.60),
               (0.40, 0.05), (0.20, 0.05)]
    o = lib.revolve('bowl', outline, segments=24)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    openings = [e for e in bm.edges if len(e.link_faces) < 2]
    check('revolve is closed', not openings,
          '%d boundary edges' % len(openings))
    bm.free()
    zs = [v.co.z for v in o.data.vertices]
    xs = [v.co.x for v in o.data.vertices]
    check('revolve spans the outline height', abs(max(zs) - 0.60) < 1e-4,
          'top at %.3f' % max(zs))
    check('revolve spans the outline radius', abs(max(xs) - 0.45) < 1e-3,
          'radius %.3f' % max(xs))


def test_revolve_welds_an_axis_pole():
    lib.reset()
    o = lib.revolve('cone', [(0.0, 1.0), (0.5, 0.0)], segments=16,
                    close_outline=False)
    axis = [v for v in o.data.vertices
            if v.co.x ** 2 + v.co.y ** 2 < 1e-8]
    check('revolve welds the axis pole to one vertex', len(axis) == 1,
          '%d vertices on the axis' % len(axis))


def test_profile_scales_taper_the_sweep():
    lib.reset()
    path = [(x * 0.5, 0, 0) for x in range(5)]
    o = lib.profile('tail', lib.circle_section(0.2, 8), path,
                    scales=[1.0, 0.75, 0.5, 0.25, 0.05])
    near = [v for v in o.data.vertices if v.co.x < 0.01]
    far = [v for v in o.data.vertices if v.co.x > 1.99]
    def radius(vs):
        return max((v.co.y ** 2 + v.co.z ** 2) ** 0.5 for v in vs)
    check('profile scales taper the section',
          radius(near) > radius(far) * 4,
          'start %.3f, end %.3f' % (radius(near), radius(far)))


def test_sweep_changes_section_along_the_path():
    """profile() scales one section uniformly; sweep() takes a different
    section per station, so a form can be round at one end and keeled at the
    other."""
    lib.reset()
    path = [(x * 0.5, 0, 0) for x in range(5)]
    round_s = lib.circle_section(0.2, 8)
    flat_s = [(a * 1.6, b * 0.25) for (a, b) in round_s]
    sections = [round_s, round_s, flat_s, flat_s, flat_s]
    o = lib.sweep('morph', path, sections)
    def spread(vs, i):
        return max(v.co[i] for v in vs) - min(v.co[i] for v in vs)
    near = [v for v in o.data.vertices if v.co.x < 0.01]
    far = [v for v in o.data.vertices if v.co.x > 1.99]
    check('sweep changes the section shape',
          spread(far, 1) > spread(near, 1) * 1.3
          and spread(far, 2) < spread(near, 2) * 0.6,
          'near %.2f x %.2f, far %.2f x %.2f'
          % (spread(near, 1), spread(near, 2), spread(far, 1), spread(far, 2)))
    try:
        lib.sweep('bad', path, sections[:3])
        check('sweep rejects a section count mismatch', False, 'no error')
    except ValueError:
        check('sweep rejects a section count mismatch', True)


def test_path_frames_are_orthonormal():
    frames = lib.path_frames([(0, 0, 0), (1, 0, 0), (2, 1, 0)])
    ok = True
    for _o, r, u, t in frames:
        if abs(r.length - 1) > 1e-5 or abs(u.length - 1) > 1e-5:
            ok = False
        if abs(r.dot(t)) > 1e-5 or abs(r.dot(u)) > 1e-5:
            ok = False
    check('path_frames returns an orthonormal frame per point', ok)


def test_rounded_box_uses_two_radii():
    """box(chamfer=) puts one radius on all twelve edges; almost no
    manufactured object is made that way."""
    lib.reset()
    a = lib.rounded_box('a', (1, 1, 1), r_upright=0.2, r_horizontal=0.02)
    b = lib.box('b', (1, 1, 1), chamfer=0.2)
    check('rounded_box builds geometry', len(a.data.polygons) > 6,
          '%d faces' % len(a.data.polygons))
    check('rounded_box differs from a single-radius chamfer',
          len(a.data.vertices) != len(b.data.vertices),
          'both %d verts' % len(a.data.vertices))
    zs = sorted({round(v.co.z, 3) for v in a.data.vertices})
    check('rounded_box keeps the horizontal radius tight',
          abs(max(zs) - 0.5) < 1e-6 and (0.5 - zs[-2]) < 0.05,
          'top rings at %s' % zs[-3:])


def test_path_frames_survive_a_nearly_vertical_leg():
    """The guard has to be relative to the tangent. An absolute epsilon catches
    the exactly-vertical case and misses the nearly-vertical one, which is the
    one that actually occurs - a straight leg whose neighbours differ by a
    millimetre has a horizontal component around 0.0016, and the frame then
    takes its whole azimuth from that crumb."""
    path = [(0, 0, 0), (0.0000, 0, 1), (0.0016, 0, 2), (0, 0, 3), (0, 0, 4)]
    frames = lib.path_frames(path)
    worst = 0.0
    for i in range(len(frames) - 1):
        a, b = frames[i][1], frames[i + 1][1]
        worst = max(worst, a.angle(b))
    import math as _m
    check('path_frames stay continuous on a nearly-vertical path',
          worst < _m.radians(20),
          'frame swings %.1f degrees between stations' % _m.degrees(worst))


def test_text_is_welded_and_centred():
    """Unwelded glyphs are not closed surfaces, so a boolean against them
    silently does nothing - and typographic centring leaves a ring of numerals
    sitting high."""
    lib.reset()
    o = lib.text('VIII', 'VIII', size=0.014, depth=0.0006)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    openings = [e for e in bm.edges if len(e.link_faces) < 2]
    n_before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    check('text() welds its doubled vertices', len(bm.verts) == n_before,
          '%d verts weld down to %d' % (n_before, len(bm.verts)))
    check('text() returns a closed surface', not openings,
          '%d boundary edges' % len(openings))
    bm.free()
    ys = [v.co.y for v in o.data.vertices]
    check('text() centres on the mesh, not the em box',
          abs((min(ys) + max(ys)) / 2.0) < 1e-5,
          'centre off by %.4f' % ((min(ys) + max(ys)) / 2.0))


def test_text_resolution_controls_cost():
    lib.reset()
    lo = lib.text('lo', '8', size=0.02, depth=0.001, resolution=1)
    hi = lib.text('hi', '8', size=0.02, depth=0.001, resolution=12)
    check('text() resolution changes triangle cost',
          len(hi.data.polygons) > len(lo.data.polygons),
          'res1 %d faces, res12 %d' % (len(lo.data.polygons),
                                       len(hi.data.polygons)))


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
               test_bounds_are_tight_for_a_rotated_object,
               test_boolean_cuts_a_hole_and_stays_closed,
               test_fuse_removes_the_interior_wall,
               test_revolve_makes_a_closed_shell,
               test_revolve_welds_an_axis_pole,
               test_profile_scales_taper_the_sweep,
               test_sweep_changes_section_along_the_path,
               test_path_frames_are_orthonormal,
               test_rounded_box_uses_two_radii,
               test_path_frames_survive_a_nearly_vertical_leg,
               test_text_is_welded_and_centred,
               test_text_resolution_controls_cost):
        print('--- %s' % fn.__name__)
        fn()
    print()
    if FAILED:
        print('%d FAILED: %s' % (len(FAILED), ', '.join(FAILED)))
        sys.exit(1)
    print('all tests passed')


main()
