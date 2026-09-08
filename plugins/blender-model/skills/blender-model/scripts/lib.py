# Shared modelling helpers. Nothing is built here.
#
# These wrap the Blender API so build scripts read as descriptions of shapes,
# and centralise the things that are easy to get wrong: sRGB colours converted
# to linear, consistent shading, part origins on the joint they rotate about,
# and a glTF export that lands where the app loads from.
#
# Everything project-specific lives in artconfig.py. Edit that, not this.
#
# AXES. Blender is Z-up. The glTF exporter is called with export_yup=True,
# which maps Blender (x, y, z) to glTF (x, z, -y):
#
#     Blender +X  ->  glTF +X    forward
#     Blender +Z  ->  glTF +Y    up
#     Blender +Y  ->  glTF -Z    left
#
# Model with Z up: heights go in Z.
import bpy
import bmesh
import math
import os

import artconfig as cfg

OUT = cfg.OUT


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Materials and meshes survive a scene reset by name, so clear them too or
    # a later build reuses an earlier build's materials.
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


# ---------------------------------------------------------------- colour

def srgb(hex_value, alpha=1.0):
    """0xRRGGBB authored as sRGB -> linear RGBA, which is what Blender wants.

    Every `Base Color` socket is linear. Passing sRGB byte values straight in
    lifts every mid-tone by most of a stop. The transfer function is the sRGB
    one, not a 2.2 gamma; they differ near black by enough to matter."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(((hex_value >> 16) & 255) / 255.0),
            lin(((hex_value >> 8) & 255) / 255.0),
            lin((hex_value & 255) / 255.0),
            alpha)


# ---------------------------------------------------------------- materials

def material(name, rgba, rough=0.72, metal=0.0, emissive=0.0, alpha=1.0,
             clearcoat=0.0):
    """A Principled BSDF, which is what glTF PBR is defined against, so these
    values reach the engine unchanged.

    Cached by name: two calls with the same name return the same material,
    which is why reset() clears them between builds."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    if len(rgba) == 3:
        rgba = (rgba[0], rgba[1], rgba[2], alpha)
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Alpha' in b.inputs:
        b.inputs['Alpha'].default_value = alpha
    if alpha < 1.0:
        m.blend_method = 'BLEND'
    if clearcoat and 'Coat Weight' in b.inputs:
        # Lacquer over paint: a sheen that roughness alone cannot express.
        b.inputs['Coat Weight'].default_value = clearcoat
        b.inputs['Coat Roughness'].default_value = 0.08
    if emissive > 0:
        b.inputs['Emission Color'].default_value = rgba
        b.inputs['Emission Strength'].default_value = emissive
    return m


def hexmat(name, hex_value, **kw):
    """`material` taking a palette hex directly, so srgb() cannot be forgotten
    at a call site."""
    alpha = kw.get('alpha', 1.0)
    return material(name, srgb(hex_value, alpha), **kw)


# ---------------------------------------------------------------- primitives

def _new(name):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj, mesh


def _finish(obj, mesh, loc, rot, scale=(1, 1, 1), smooth=None):
    obj.location = loc
    obj.rotation_euler = rot
    obj.scale = scale
    for p in mesh.polygons:
        p.use_smooth = cfg.SMOOTH_DEFAULT if smooth is None else smooth
    return obj


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), chamfer=0.0, taper=1.0,
        segments=1, shear=0.0, smooth=None):
    """A chamfered box, optionally narrowed at the top or sheared along Y.

    A visible chamfer catches the key light and gives the form an edge to sit
    on, which is most of what separates a modelled shape from a stretched
    cube."""
    obj, mesh = _new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    if taper != 1.0:
        for v in bm.verts:
            if v.co.z > 0:
                v.co.x *= taper
                v.co.y *= taper
    if shear:
        for v in bm.verts:
            v.co.y += v.co.z * shear
    if chamfer > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                        offset=chamfer, segments=segments, affect='EDGES',
                        profile=0.5, clamp_overlap=True)
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, loc, rot, smooth=smooth)


def wedge(name, size, loc=(0, 0, 0), rot=(0, 0, 0), pinch=0.15, smooth=None):
    """A box pinched to a ridge along +Y: crests, keels, blades, prows."""
    obj = box(name, size, loc, rot, smooth=smooth)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for v in bm.verts:
        if v.co.y > 0:
            v.co.x *= pinch
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def cyl(name, r1, r2, h, loc=(0, 0, 0), rot=(0, 0, 0), segments=None,
        chamfer=0.0, smooth=None):
    obj, mesh = _new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                          segments=cfg.CYL_SEGMENTS if segments is None else segments,
                          radius1=r1, radius2=r2, depth=h)
    if chamfer > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                        offset=chamfer, segments=1, affect='EDGES', profile=0.5,
                        clamp_overlap=True)
    bm.to_mesh(mesh)
    bm.free()
    obj = _finish(obj, mesh, loc, rot, smooth=smooth)
    if cfg.SMOOTH_DEFAULT if smooth is None else smooth:
        # Round the barrel but keep the end caps crisp; a smoothed cap reads as
        # a dent.
        for p in obj.data.polygons:
            p.use_smooth = abs(p.normal.z) < 0.9
    return obj


def tube(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), segments=None, smooth=None):
    return cyl(name, r, r, h, loc, rot, segments=segments, smooth=smooth)


def sphere(name, r, loc=(0, 0, 0), rot=(0, 0, 0), subdiv=1, scale=(1, 1, 1),
           smooth=None):
    obj, mesh = _new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, loc, rot, scale, smooth=smooth)


def plate(name, w, d, t, loc=(0, 0, 0), rot=(0, 0, 0), chamfer=0.03):
    """A thin slab with its edges cut: armour, panelling, signage."""
    return box(name, (w, d, t), loc, rot, chamfer=chamfer)


def ring(name, r_in, r_out, w, loc=(0, 0, 0), rot=(0, 0, 0), segments=9,
         smooth=None):
    """An annulus with thickness: a wheel rim, a collar, a hoop.

    A cylinder cannot stand in for this — it is solid, and the hole is most of
    what reads. Four quads a segment: outer, inner, and the two faces."""
    obj, mesh = _new(name)
    bm = bmesh.new()
    rows = [[bm.verts.new((math.cos(i / segments * math.tau) * r,
                           math.sin(i / segments * math.tau) * r, z))
             for i in range(segments)]
            for r in (r_out, r_in) for z in (w / 2, -w / 2)]
    ot, ob, it, ib = rows
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((ot[i], ot[j], ob[j], ob[i]))
        bm.faces.new((ib[i], ib[j], it[j], it[i]))
        bm.faces.new((it[i], it[j], ot[j], ot[i]))
        bm.faces.new((ob[i], ob[j], ib[j], ib[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, loc, rot, smooth=smooth)


def torus(name, r_major, r_minor, loc=(0, 0, 0), rot=(0, 0, 0),
          major_seg=20, minor_seg=10, smooth=None):
    obj, mesh = _new(name)
    bm = bmesh.new()
    for i in range(major_seg):
        a = i / major_seg * math.tau
        for j in range(minor_seg):
            b = j / minor_seg * math.tau
            bm.verts.new((
                (r_major + r_minor * math.cos(b)) * math.cos(a),
                (r_major + r_minor * math.cos(b)) * math.sin(a),
                r_minor * math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(major_seg):
        for j in range(minor_seg):
            a0 = i * minor_seg + j
            a1 = i * minor_seg + (j + 1) % minor_seg
            b0 = ((i + 1) % major_seg) * minor_seg + j
            b1 = ((i + 1) % major_seg) * minor_seg + (j + 1) % minor_seg
            bm.faces.new((bm.verts[a0], bm.verts[b0], bm.verts[b1], bm.verts[a1]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, loc, rot, smooth=True if smooth is None else smooth)


# ---------------------------------------------------------------- swept forms
#
# Anything whose cross-section is known at every station along a line is a
# sweep or a loft. Stating the sections is shorter and more accurate than
# pulling the shape out of a box.

def revolve(name, outline, segments=48, close_outline=True, smooth=None,
            arc=math.tau):
    """Spin a 2D outline around the Z axis.

    `outline` is [(r, z), ...] — radius out from the axis, height up it. The
    natural way to describe anything turned on a lathe: a goblet, a bottle, a
    finial, a wheel hub, a column base.

    With `close_outline` the outline is treated as a closed loop, so an outline
    that goes up the outside of a bowl, over the rim and back down the inside
    produces a real thin-walled shell rather than a solid lump. A point at
    r=0 becomes a pole and is welded.

    `arc` less than a full turn leaves it open, for a section cut away."""
    obj, mesh = _new(name)
    bm = bmesh.new()
    full = abs(arc - math.tau) < 1e-9
    rings = []
    steps = segments if full else segments + 1
    for i in range(steps):
        a = (i / segments) * arc
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((r * ca, r * sa, z)) for (r, z) in outline])
    n = len(outline)
    last = len(rings) if full else len(rings) - 1
    for i in range(last):
        r0 = rings[i]
        r1 = rings[(i + 1) % len(rings)]
        for j in range(n if close_outline else n - 1):
            k = (j + 1) % n
            quad = (r0[j], r0[k], r1[k], r1[j])
            # A point on the axis is the same vertex on every ring, so the
            # quad there collapses to a triangle; remove_doubles below welds
            # it and bmesh will not accept the degenerate face meanwhile.
            if len({v.co.to_tuple(5) for v in quad}) < 3:
                continue
            try:
                bm.faces.new(quad)
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, (0, 0, 0), (0, 0, 0),
                   smooth=True if smooth is None else smooth)


def profile(name, section, path, close=False, smooth=None, scales=None):
    """Sweep a 2D section along a 3D path: handrails, pipes, cables, gutters.

    `section` is [(a, b), ...] in the plane perpendicular to the path;
    `path` is [(x, y, z), ...].

    `scales`, one factor per path point, tapers the section as it goes — a
    tail, a horn, a rope under tension. Without it the sweep is a constant
    hose, which is right for a handrail and wrong for anything that grew."""
    obj, mesh = _new(name)
    bm = bmesh.new()
    rings = []
    for i, (px, py, pz) in enumerate(path):
        nxt = path[min(i + 1, len(path) - 1)]
        prv = path[max(i - 1, 0)]
        tx, ty, tz = (nxt[0] - prv[0], nxt[1] - prv[1], nxt[2] - prv[2])
        tl = math.sqrt(tx * tx + ty * ty + tz * tz) or 1.0
        tx, ty, tz = tx / tl, ty / tl, tz / tl
        # The section is framed against world up. A path that loops over
        # vertical needs a parallel transport frame instead; this will twist.
        ux, uy, uz = 0.0, 0.0, 1.0
        rx, ry, rz = ty * uz - tz * uy, tz * ux - tx * uz, tx * uy - ty * ux
        rl = math.sqrt(rx * rx + ry * ry + rz * rz)
        if rl < 1e-6:
            rx, ry, rz, rl = 0.0, 1.0, 0.0, 1.0
        rx, ry, rz = rx / rl, ry / rl, rz / rl
        ux, uy, uz = ry * tz - rz * ty, rz * tx - rx * tz, rx * ty - ry * tx
        k = 1.0 if scales is None else scales[min(i, len(scales) - 1)]
        ring = []
        for (sa, sb) in section:
            sa, sb = sa * k, sb * k
            ring.append(bm.verts.new((
                px + rx * sa + ux * sb,
                py + ry * sa + uy * sb,
                pz + rz * sa + uz * sb)))
        rings.append(ring)
    n = len(section)
    for i in range(len(rings) - 1):
        for j in range(n):
            k = (j + 1) % n
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    if close:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, (0, 0, 0), (0, 0, 0),
                   smooth=True if smooth is None else smooth)


def loft(name, stations, cap_ends=True, smooth=None):
    """Sweep a *changing* closed section along X. A hull is a loft, not a grown
    form.

    `stations` is [(x, [(y, z), ...]), ...] with the same number of points in
    every ring, wound consistently."""
    obj, mesh = _new(name)
    bm = bmesh.new()
    rings = []
    for x, section in stations:
        rings.append([bm.verts.new((x, y, z)) for (y, z) in section])
    n = len(stations[0][1])
    for i in range(len(rings) - 1):
        for j in range(n):
            k = (j + 1) % n
            a, b = rings[i][j], rings[i][k]
            c, d = rings[i + 1][k], rings[i + 1][j]
            # Skip degenerate quads where the section pinches to a point.
            if (a.co - b.co).length < 1e-6 and (d.co - c.co).length < 1e-6:
                continue
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass          # duplicate face at a pinched end
    if cap_ends:
        for r, flip in ((rings[0], True), (rings[-1], False)):
            try:
                bm.faces.new(list(reversed(r)) if flip else r)
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    return _finish(obj, mesh, (0, 0, 0), (0, 0, 0),
                   smooth=True if smooth is None else smooth)


def circle_section(r, segments=10):
    return [(math.cos(i / segments * math.tau) * r,
             math.sin(i / segments * math.tau) * r) for i in range(segments)]


def rect_section(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]


# ---------------------------------------------------------------- booleans
#
# A window, a doorway, a recess, a slot: the difference between a hole cut in a
# surface and a frame stuck on top of it. Faking those with proud geometry
# works at a distance and falls apart at a grazing angle.

def boolean(target, tool, op='DIFFERENCE', solver='EXACT', keep_tool=False,
            transfer_material=True):
    """Cut, fuse or intersect `target` with `tool`, in place.

    The tool is consumed unless `keep_tool`. With `transfer_material`, faces
    created by the cut take the *tool's* material — so a hole reveals whatever
    the tool was painted, which is usually what makes it read as a hole rather
    than a black rectangle.

    Evaluates the depsgraph rather than applying the modifier through an
    operator: `bpy.ops.object.modifier_apply` depends on an active object and a
    window context that a background render does not have.

    The EXACT solver expects closed input. A target with boundary edges will
    produce something, but not reliably what you asked for."""
    before = len(target.data.polygons)
    open_edges = _boundary_edge_count(target)
    m = target.modifiers.new('_bool', 'BOOLEAN')
    m.object = tool
    m.operation = op
    m.solver = solver
    if transfer_material and hasattr(m, 'material_mode'):
        m.material_mode = 'TRANSFER'
    # The modifier is evaluated against the tool's world matrix, which is stale
    # until the depsgraph catches up with wherever the tool was just placed.
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.remove(m)
    old = target.data
    target.data = mesh
    bpy.data.meshes.remove(old)
    if not keep_tool:
        bpy.data.objects.remove(tool, do_unlink=True)
    # A boolean against a mesh with holes in it does not fail, it quietly does
    # nothing — and a no-op that looks like success costs a whole pass before
    # anyone notices the window was never cut.
    if len(target.data.polygons) == before:
        print('WARNING boolean %s on %r changed nothing (%d faces before and '
              'after)' % (op, target.name, before))
        if open_edges:
            print('        the target has %d boundary edges; the EXACT solver '
                  'needs a closed surface' % open_edges)
        else:
            print('        check the tool actually overlaps the target')
    return target


def _boundary_edge_count(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    n = len([e for e in bm.edges if len(e.link_faces) < 2])
    bm.free()
    return n


def cut(target, tool, **kw):
    """Subtract `tool` from `target`."""
    return boolean(target, tool, 'DIFFERENCE', **kw)


def fuse(target, tool, **kw):
    """Merge `tool` into `target` as one continuous surface. Unlike
    merge_into(), which only groups meshes, this removes the interior walls
    where the two solids overlap."""
    return boolean(target, tool, 'UNION', **kw)


def intersect(target, tool, **kw):
    """Keep only the volume the two share."""
    return boolean(target, tool, 'INTERSECT', **kw)


def hole(target, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, through='y'):
    """Cut a rectangular opening through `target`.

    `size` is the opening; the axis named by `through` is stretched so the tool
    passes clear of both faces — a tool that stops flush with a surface leaves
    a zero-thickness sliver the solver has to guess about.

    `mat` paints the reveal, and is usually a shade darker than the wall."""
    s = list(size)
    s[{'x': 0, 'y': 1, 'z': 2}[through]] *= 4.0
    tool = box('_cut', s, loc, rot)
    if mat:
        attach(tool, None, mat)
    return cut(target, tool)


# ---------------------------------------------------------------- hierarchy
#
# A model that animates exports as a tree of named nodes. The animator drives
# it by name, so those names are a contract with the app.

def part(name, loc=(0, 0, 0), parent=None):
    """An empty at a joint. Its origin is the pivot the animator rotates about,
    so an arm's `part` sits at the shoulder and the meshes hang below it."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.08
    bpy.context.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


def attach(obj, parent, mat=None):
    """Parent a mesh to a part without moving it. Everything is authored in
    world coordinates and the parent's origin is subtracted here."""
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    if parent:
        # Setting an empty's location does not update its matrix_world until
        # the depsgraph is evaluated, so inverting it first yields the identity
        # and displaces the child by its parent's position.
        bpy.context.view_layer.update()
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def merge_into(name, parts, parent=None, mat=None):
    """Join a bag of meshes into one and hang it off a part: fewer draw calls
    and fewer nodes, for everything that does not move on its own.

    The join preserves each part's own materials, including per-face ones from
    repaint(). Passing `mat` replaces all of them with the single material
    given, so leave it out whenever the parts are already painted."""
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    # A join leaves the origin wherever the active object's was. Reset it to
    # the world origin so the parenting above is predictable.
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return attach(obj, parent, mat)


def repaint(obj, rules):
    """Per-face materials on a grown mesh.

    A form grown out of another is the same mesh, so a second colour on it
    cannot be a second object; it has to be a face assignment. Rules are
    (material, test) applied in order, so a later rule wins where they overlap
    and the list reads outermost-last.

    `test` takes the face centre, or (centre, normal) if it accepts two
    arguments — painting a deck but not a side wall needs the normal."""
    slot = {}
    for mat, _ in rules:
        if mat.name not in slot:
            obj.data.materials.append(mat)
            slot[mat.name] = len(obj.data.materials) - 1
    prepared = []
    for mat, test in rules:
        try:
            nargs = test.__code__.co_argcount
        except AttributeError:
            nargs = 1
        prepared.append((mat, test, nargs >= 2))
    for p in obj.data.polygons:
        for mat, test, wants_normal in prepared:
            if test(p.center, p.normal) if wants_normal else test(p.center):
                p.material_index = slot[mat.name]
    return obj


def shade_auto(obj, angle_deg=38):
    """Smooth shading with a sharp-edge threshold, so a formed panel flows and
    the hard corner between two panels does not."""
    mesh = obj.data
    for p in mesh.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(mesh)
    lim = math.radians(angle_deg)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim:
            e.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    return obj


# ---------------------------------------------------------------- export

def export(name, report=None):
    """Write <name>.glb to cfg.OUT and record what came out.

    The floor and top heights are reported because a model whose lowest vertex
    is off zero sits sunk into or floating above the ground in the app, and
    nothing in the Blender scene shows that."""
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True,
        export_apply=True, export_yup=cfg.EXPORT_YUP, export_cameras=False,
        export_lights=False, export_extras=False,
        export_normals=True, export_tangents=False,
    )
    if report is not None:
        tris = 0
        lo, hi = 1e9, -1e9
        for o in bpy.context.scene.objects:
            if o.type != 'MESH':
                continue
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
            for v in o.data.vertices:
                z = (o.matrix_world @ v.co).z
                lo = min(lo, z)
                hi = max(hi, z)
        report.append((name, tris, lo, hi, os.path.getsize(path)))
    return path


def summarise(report, budget=None):
    budget = cfg.TRI_BUDGET if budget is None else budget
    print('=== exported ===')
    worst = 0
    for name, tris, lo, hi, size in sorted(report):
        flag = ''
        if budget and tris > budget:
            flag += '  OVER BUDGET (%d)' % budget
        if lo < -0.02:
            flag += '  SUNK %.2f' % lo
        if lo > 0.05:
            flag += '  FLOATING %.2f' % lo
        worst = max(worst, tris)
        print('%-26s %6d tris  %7.1f KB   floor %+.2f  top %+.2f%s'
              % (name, tris, size / 1024.0, lo, hi, flag))
    print('%d models, heaviest %d tris, %d tris total'
          % (len(report), worst, sum(r[1] for r in report)))
