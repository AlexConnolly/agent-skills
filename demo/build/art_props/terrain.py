# Read the ground agent's terrain.json and answer questions about it.
#
# Section 6.3 is explicit: build_ground.py writes docs/data/terrain.json and it
# is the ONE source of truth for ground height. Everything in these four build
# scripts that has to meet the ground — the track ribbon, the ditch water, the
# rut pools, the bridge abutments — samples it here rather than reimplementing
# the height function, because two implementations of a height field are two
# height fields.
#
# terrain.json is in THREE.JS axes (x east, y up, z south). Blender is
# (x, -z_three, y_three). Everything in this module takes and returns Three.js
# unless the name says blender.
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# Section 8.8 draws it under demo/docs/; build_ground.py actually writes it to
# the repo-root docs/ that GitHub Pages serves. Look in both rather than pick a
# side, because the failure mode of getting this wrong is silent: the fallback
# is a flat plane and everything floats.
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, '..', '..', '..', 'docs', 'data',
                                 'terrain.json')),
    os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'data',
                                 'terrain.json')),
]
DEFAULT = next((p for p in CANDIDATES if os.path.exists(p)), CANDIDATES[0])


class Terrain(object):
    def __init__(self, path=None):
        self.path = path or os.environ.get('ART_TERRAIN') or DEFAULT
        self.ok = os.path.exists(self.path)
        if not self.ok:
            print('WARNING no terrain.json at %s — falling back to the flat '
                  'level plan from section 6.1. Every height in this build is '
                  'then a guess and the assets WILL float.' % self.path)
            self.levels = {'outfield': -4.5, 'ditch_floor': -6.8,
                           'ditch_water': -6.0, 'ward': 0.0}
            return
        with open(self.path) as fh:
            d = json.load(fh)
        self.min = d['min']
        self.max = d['max']
        self.step = d['step']
        self.n = d['n']
        self.heights = d['heights']
        self.levels = d['levels']

    def h(self, x, z):
        """Bilinear ground height at a Three.js ground point."""
        if not self.ok:
            return self.levels['outfield']
        fx = (x - self.min[0]) / self.step
        fz = (z - self.min[1]) / self.step
        ix = max(0, min(self.n[0] - 2, int(math.floor(fx))))
        iz = max(0, min(self.n[1] - 2, int(math.floor(fz))))
        tx = max(0.0, min(1.0, fx - ix))
        tz = max(0.0, min(1.0, fz - iz))
        h = self.heights
        a = h[iz][ix] * (1 - tx) + h[iz][ix + 1] * tx
        b = h[iz + 1][ix] * (1 - tx) + h[iz + 1][ix + 1] * tx
        return a * (1 - tz) + b * tz

    def normal(self, x, z, e=1.5):
        """Surface normal, Three.js, from central differences."""
        dx = (self.h(x + e, z) - self.h(x - e, z)) / (2 * e)
        dz = (self.h(x, z + e) - self.h(x, z - e)) / (2 * e)
        n = (-dx, 1.0, -dz)
        L = math.sqrt(sum(c * c for c in n))
        return tuple(c / L for c in n)

    # ------------------------------------------------------------ the ditch

    def crossings(self, cx, cz, bearing, level, r0=20.0, r1=90.0, step=0.25):
        """Every radius on a bearing where the ground crosses `level`.

        `bearing` is a unit (dx, dz) in Three.js. Returns [(radius, going_down)]
        so a ditch reads as [(inner lip, True), (outer lip, False)]."""
        out = []
        prev = self.h(cx + bearing[0] * r0, cz + bearing[1] * r0)
        r = r0 + step
        while r <= r1:
            cur = self.h(cx + bearing[0] * r, cz + bearing[1] * r)
            if (prev - level) * (cur - level) < 0:
                t = (level - prev) / (cur - prev)
                out.append((r - step + t * step, cur < prev))
                prev = cur
            else:
                prev = cur
            r += step
        return out

    def water_edges(self, cx, cz, bearing, level=-6.0):
        """The inner and outer radius of standing water on one bearing.

        The pair that brackets the deepest point, so a puddle in the outfield
        or a dip on the batter cannot be mistaken for the ditch."""
        xs = self.crossings(cx, cz, bearing, level)
        if len(xs) < 2:
            return None
        # deepest sample between the first down-crossing and the last up one
        best, best_r = 1e9, None
        r = xs[0][0]
        while r <= xs[-1][0]:
            hh = self.h(cx + bearing[0] * r, cz + bearing[1] * r)
            if hh < best:
                best, best_r = hh, r
            r += 0.25
        inner = max([c[0] for c in xs if c[0] <= best_r] or [xs[0][0]])
        outer = min([c[0] for c in xs if c[0] >= best_r] or [xs[-1][0]])
        return inner, outer
