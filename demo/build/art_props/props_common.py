# Shared by build_rocks / build_crossing / build_track / build_clutter.
#
# Four scripts, one scene, one palette, one set of levels, one definition of
# where the hero frame is. Anything that would otherwise be typed out four
# times and drift three ways lives here.
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)

import artconfig as cfg     # noqa: E402
import lib                  # noqa: E402


# ---------------------------------------------------------------- palette (2)

SKY_ZENITH = 0x080D18
SKY_HORIZON = 0x1C2C42
MOON_COLD = 0xAFC8EC
STONE_LIT = 0x6A7787
STONE_DARK = 0x151D29
TURF_NIGHT = 0x1A2419
EARTH_WET = 0x20211C
TIMBER_NIGHT = 0x100D0A
MIST_PALE = 0x5E7488
WATER_BLACK = 0x0A121A

# Rock, section 5 group 2: "grey-brown rock darkening in the crevices and
# greening at the base". These three are the ends of that ramp; every rock
# vertex is somewhere between them.
ROCK_LIT = 0x3A3A34
ROCK_DARK = 0x191C18
ROCK_MOSS = 0x232A1E


# ---------------------------------------------------------------- noise
#
# Value noise from a hash of the integer lattice. Deterministic from the
# coordinates, so a rock that reads well is the same rock on the next machine
# and the same rock after a rebuild.

def _hash(i, j, k, s):
    n = (i * 374761393 + j * 668265263 + k * 1103515245 + s * 1442695041) \
        & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF) / 8388607.5 - 1.0


def _smoother(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise3(x, y, z, seed=0):
    i, j, k = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = _smoother(x - i), _smoother(y - j), _smoother(z - k)
    out = 0.0
    for dk in (0, 1):
        for dj in (0, 1):
            for di in (0, 1):
                w = ((fx if di else 1 - fx) * (fy if dj else 1 - fy)
                     * (fz if dk else 1 - fz))
                out += w * _hash(int(i) + di, int(j) + dj, int(k) + dk, seed)
    return out


def fbm3(x, y, z, seed=0, octaves=2):
    out, amp, f = 0.0, 1.0, 1.0
    norm = 0.0
    for o in range(octaves):
        out += amp * noise3(x * f, y * f, z * f, seed + o * 17)
        norm += amp
        amp *= 0.5
        f *= 2.03
    return out / norm


class Rng(object):
    """A tiny reproducible PRNG, so a piece is the same piece every build."""

    def __init__(self, seed):
        self.s = (seed * 2654435761 + 1013904223) & 0xFFFFFFFF

    def next(self):
        self.s = (self.s * 1664525 + 1013904223) & 0xFFFFFFFF
        return ((self.s >> 8) & 0xFFFFFF) / 16777215.0

    def uni(self, a, b):
        return a + (b - a) * self.next()


# ---------------------------------------------------------------- materials

def vertex_material(name, rough=0.92, metal=0.0):
    """A Principled whose Base Color comes from the mesh's COLOR_0 attribute.

    texlib.vertex_colour() writes the attribute; it does not wire it up, so
    without this the contact sheet renders a flat grey model and every
    judgement about the colour ramp is a judgement about nothing. The glTF
    exporter recognises this exact node pattern and writes COLOR_0 with a white
    base factor, which three.js multiplies back together."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    vc.location = (-320, 260)
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def lin(hex_value):
    return lib.srgb(hex_value)[:3]


# ---------------------------------------------------------------- geometry helpers

def blob_outline(n, rx, ry, seed, rough=0.22, reentrant=0):
    """An irregular closed plan: a polygon that is nobody's ellipse.

    `reentrant` pulls that many vertices sharply inward, which is what stops a
    rock plan or a pool reading as a lozenge."""
    rng = Rng(seed)
    pulls = set()
    while len(pulls) < reentrant:
        pulls.add(int(rng.uni(0, n)) % n)
    pts = []
    for i in range(n):
        a = (i / float(n)) * math.tau + rng.uni(-0.10, 0.10)
        k = 1.0 + rng.uni(-rough, rough)
        if i in pulls:
            k *= rng.uni(0.55, 0.70)
        pts.append((math.cos(a) * rx * k, math.sin(a) * ry * k))
    return pts


def bbox(objs):
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for o in objs:
        if o.type != 'MESH':
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


# ---------------------------------------------------------------- the hero frame
#
# Section 4.1. Where a thing lands in the published picture is a fact about the
# build, not an opinion about it, so every script prints it.

_CAM = (78.9, -1.0, 43.3)
_TGT = (3.9, 9.3, -6.4)
_FWD = None
_RIGHT = None


def _axes():
    global _FWD, _RIGHT
    if _FWD is None:
        d = (_TGT[0] - _CAM[0], _TGT[2] - _CAM[2])
        L = math.hypot(*d)
        _FWD = (d[0] / L, d[1] / L)
        _RIGHT = (-_FWD[1], _FWD[0])
    return _FWD, _RIGHT


def hero_frame(x, z):
    """(distance in metres, percent across the 16:9 hero frame) for a Three.js
    ground point. 0 % is the left edge."""
    fwd, right = _axes()
    d = (x - _CAM[0], z - _CAM[2])
    along = d[0] * fwd[0] + d[1] * fwd[1]
    lat = d[0] * right[0] + d[1] * right[1]
    if along <= 0.1:
        return along, float('nan')
    half = along * math.tan(math.radians(27.0))
    return along, 50.0 + 50.0 * lat / half


def px_per_metre(distance):
    """What a 1920-wide render gives at that distance, 54 deg horizontal."""
    return 1920.0 / (2.0 * distance * math.tan(math.radians(27.0)))


# ---------------------------------------------------------------- reporting

def budget_table(rows):
    """rows: [(name, tris, budget, 'w x d x h', note)]"""
    print('=== against the section 5 budget ===')
    for name, tris, budget, dims, note in rows:
        flag = ''
        if budget and tris > budget * 1.15:
            flag = '   OVER by %d%%' % round((tris / float(budget) - 1) * 100)
        elif budget and tris < budget * 0.5:
            flag = '   under by %d%%' % round((1 - tris / float(budget)) * 100)
        print('%-18s %5d tris  (budget %5s)  %-26s %s%s'
              % (name, tris, budget or '-', dims, note, flag))
