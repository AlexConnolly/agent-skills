# What the exporter actually wrote, read back out of the .glb.
#
#   python inspect_glb.py <file.glb> [more.glb ...]
#
# Plain Python, no Blender: it parses the GLB container and prints the JSON
# chunk's material table. It exists because the Blender viewport is not
# evidence. The castle shipped with opaque smoke for exactly this reason --
# build_castle.py asks for alpha=0.34, skin_castle.py replaces the material,
# and nobody read the file that came out the other end.
#
# Reports, per material: base colour and its alpha, the alpha mode, the
# emissive factor, and any KHR_materials_emissive_strength or
# KHR_materials_transmission that changed the meaning of either.
import json
import os
import struct
import sys


def chunks(path):
    with open(path, 'rb') as fh:
        magic, version, _length = struct.unpack('<III', fh.read(12))
        if magic != 0x46546C67:
            raise SystemExit('%s is not a GLB' % path)
        out = {}
        while True:
            head = fh.read(8)
            if len(head) < 8:
                break
            size, kind = struct.unpack('<II', head)
            out[kind] = fh.read(size)
        return version, out


def fmt(v, n=3):
    if v is None:
        return '-'
    if isinstance(v, list):
        return '[' + ', '.join('%.*f' % (n, x) for x in v) + ']'
    return '%.*f' % (n, v)


def report(path):
    version, ch = chunks(path)
    doc = json.loads(ch[0x4E4F534A].decode('utf-8'))
    print('== %s   glTF %d, %d bytes' % (os.path.basename(path), version,
                                         os.path.getsize(path)))
    tris = 0
    for mesh in doc.get('meshes', []):
        for prim in mesh.get('primitives', []):
            if 'indices' in prim:
                tris += doc['accessors'][prim['indices']]['count'] // 3
    print('   %d mesh(es), %d primitives, %d triangles, extensions used: %s'
          % (len(doc.get('meshes', [])),
             sum(len(m.get('primitives', [])) for m in doc.get('meshes', [])),
             tris, ', '.join(doc.get('extensionsUsed', [])) or 'none'))
    for m in doc.get('materials', []):
        pbr = m.get('pbrMetallicRoughness', {})
        base = pbr.get('baseColorFactor', [1, 1, 1, 1])
        ext = m.get('extensions', {})
        strength = ext.get('KHR_materials_emissive_strength', {}).get(
            'emissiveStrength')
        print('   %-18s base %s  alpha %.3f  mode %-6s  emissive %s%s%s'
              % (m.get('name', '?'), fmt(base[:3]), base[3],
                 m.get('alphaMode', 'OPAQUE'),
                 fmt(m.get('emissiveFactor', [0, 0, 0])),
                 '  x%.2f' % strength if strength is not None else '',
                 '  doubleSided' if m.get('doubleSided') else ''))
        for k in ext:
            if k != 'KHR_materials_emissive_strength':
                print('      + %s %s' % (k, json.dumps(ext[k])))
    if not doc.get('materials'):
        print('   NO MATERIALS AT ALL')
    colour_0(doc, ch.get(0x004E4942, b''))


# --------------------------------------------------------------- COLOR_0
#
# Added for asset group 7. The mist sheets carry their whole vertical gradient
# in the alpha channel of COLOR_0, which glTF multiplies into baseColorFactor,
# so "alphaMode is BLEND" is only half the proof: a VEC3 COLOR_0, or a VEC4
# whose alpha came out flat at 1.0, is a sheet at one constant opacity, which
# is the grey plane this asset exists to not be.

_CTYPE = {5120: ('b', 1, 127.0), 5121: ('B', 1, 255.0), 5122: ('h', 2, 32767.0),
          5123: ('H', 2, 65535.0), 5126: ('f', 4, None)}


def colour_0(doc, blob):
    for mi, mesh in enumerate(doc.get('meshes', [])):
        for prim in mesh.get('primitives', []):
            idx = prim.get('attributes', {}).get('COLOR_0')
            if idx is None:
                continue
            acc = doc['accessors'][idx]
            fmt, width, norm = _CTYPE[acc['componentType']]
            n = {'VEC3': 3, 'VEC4': 4}[acc['type']]
            view = doc['bufferViews'][acc['bufferView']]
            start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
            stride = view.get('byteStride') or width * n
            vals = []
            for i in range(acc['count']):
                off = start + i * stride
                row = struct.unpack_from('<' + fmt * n, blob, off)
                vals.append([v / norm if norm else v for v in row])
            print('   COLOR_0 on mesh %s: %s %s, %d verts'
                  % (mesh.get('name', mi), acc['type'],
                     acc['componentType'], acc['count']))
            for c, label in enumerate(('r', 'g', 'b', 'a')[:n]):
                col = [v[c] for v in vals]
                print('      %s  min %.3f  max %.3f  mean %.3f%s'
                      % (label, min(col), max(col), sum(col) / len(col),
                         '   FLAT - no gradient' if max(col) - min(col) < 0.01
                         else ''))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('usage: inspect_glb.py <file.glb> ...')
    for p in sys.argv[1:]:
        report(p)
