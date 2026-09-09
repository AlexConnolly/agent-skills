# Throwaway capability probe: what does Blender 5.2 accept for blend_method,
# and does an alpha + RGBA vertex-colour material survive the glTF exporter?
import bpy
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
OUT = os.environ['ART_OUT']

bpy.ops.wm.read_factory_settings(use_empty=True)

m = bpy.data.materials.new('probe')
m.use_nodes = True
b = m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.3, 0.4, 0.5, 1.0)
b.inputs['Alpha'].default_value = 0.11

print('MAT PROPS', [p.identifier for p in m.bl_rna.properties
                    if 'blend' in p.identifier or 'render_method' in p.identifier
                    or 'transp' in p.identifier])
if hasattr(m, 'blend_method'):
    print('blend_method items:',
          [i.identifier for i in m.bl_rna.properties['blend_method'].enum_items])
    m.blend_method = 'BLEND'
    print('blend_method now', m.blend_method)
if hasattr(m, 'surface_render_method'):
    print('surface_render_method items:',
          [i.identifier for i in
           m.bl_rna.properties['surface_render_method'].enum_items])
    m.surface_render_method = 'BLENDED'
    print('surface_render_method now', m.surface_render_method)

# a quad with an RGBA vertex colour attribute, wired into base colour + alpha
me = bpy.data.meshes.new('q')
ob = bpy.data.objects.new('q', me)
bpy.context.collection.objects.link(ob)
me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 1), (-1, 1, 1)], [],
               [(0, 1, 2, 3)])
me.update()
ob.data.materials.append(m)
layer = me.color_attributes.new(name='Col', type='FLOAT_COLOR', domain='POINT')
for i, v in enumerate(me.vertices):
    a = 1.0 if v.co.z < 0.5 else 0.0
    layer.data[i].color = (1.0, 1.0, 1.0, a)

nt = m.node_tree
ca = nt.nodes.new('ShaderNodeVertexColor')
ca.layer_name = 'Col'
mult = nt.nodes.new('ShaderNodeMath')
mult.operation = 'MULTIPLY'
mult.inputs[1].default_value = 0.11
nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
nt.links.new(ca.outputs['Alpha'], mult.inputs[0])
nt.links.new(mult.outputs['Value'], b.inputs['Alpha'])

os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, 'probe.glb')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                          use_selection=True, export_apply=True,
                          export_yup=True, export_cameras=False,
                          export_lights=False, export_extras=False)

with open(path, 'rb') as fh:
    fh.read(12)
    size, kind = struct.unpack('<II', fh.read(8))
    doc = json.loads(fh.read(size).decode('utf-8'))
print('MATERIALS', json.dumps(doc['materials'], indent=1))
print('PRIM ATTRS', doc['meshes'][0]['primitives'][0]['attributes'])
for i, acc in enumerate(doc['accessors']):
    print('ACC %d %s %s count=%d' % (i, acc['type'],
                                     acc.get('componentType'), acc['count']))
