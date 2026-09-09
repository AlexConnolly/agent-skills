# The toolkit's contact sheet, run against group 7's own artconfig.
#
#   blender --background --python shots_mist.py -- <piece-name>
#
# shots.py is the toolkit's file and is imported unmodified. Two things are
# added around it, and neither changes what is being judged:
#
# 1. art_mist/ goes ahead of art/ on sys.path, so `import artconfig` inside
#    shots.py resolves to this group's five-degree camera and night palette
#    rather than the fire kit's. Same trick as shots_trees.py.
#
# 2. every imported material gets surface_render_method = 'BLENDED'. EEVEE
#    Next defaults to DITHERED, which resolves an 11 per cent surface as
#    stochastic noise over 24 samples -- the mean is right and the picture is
#    unreadable, which is no way to judge a gradient. It is an EEVEE quality
#    setting with no glTF meaning and it is applied AFTER the import.
#
#    blend_method is deliberately NOT touched. That is the property the
#    exporter turns into alphaMode, so if a rebuild ever ships these opaque
#    again, the contact sheet must show solid slabs rather than quietly
#    correct them. What comes back off the import is printed for the record.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'art_mist'))
sys.path.insert(1, os.path.join(HERE, 'art'))

import bpy                                          # noqa: E402
import shots                                        # noqa: E402

_load = shots.load_glb


def load_glb(name):
    objs = _load(name)
    seen = set()
    for o in objs:
        for slot in getattr(o, 'material_slots', []):
            m = slot.material
            if not m or m.name in seen:
                continue
            seen.add(m.name)
            print('IMPORTED MATERIAL %-12s blend_method=%s  alpha_socket=%s'
                  % (m.name, getattr(m, 'blend_method', '?'),
                     _alpha_of(m)))
            if hasattr(m, 'surface_render_method'):
                m.surface_render_method = 'BLENDED'
            m.show_transparent_back = True
            m.use_backface_culling = False
    return objs


def _alpha_of(m):
    try:
        b = m.node_tree.nodes['Principled BSDF']
    except (AttributeError, KeyError):
        return '?'
    sock = b.inputs['Alpha']
    return 'linked' if sock.is_linked else '%.3f' % sock.default_value


shots.load_glb = load_glb
shots.main()
