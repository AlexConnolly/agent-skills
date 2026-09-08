// Bilinear sampler over data/terrain.json.
//
// ART-DIRECTION §6.3: the height function has one source of truth. build_ground.py
// writes the station grid it actually built the mesh from, and this reads it.
// Nothing here reimplements the height function — that is how trees end up
// floating over ground they were never told about.
//
// No three.js import: this module is used unchanged by tools/bake-placement.mjs
// under node.

export class Terrain {
  constructor(data) {
    this.data = data;
    this.min = data.min;          // [xMin, zMin]
    this.max = data.max;
    this.step = data.step;
    this.n = data.n;              // [nx, nz]
    this.h = data.heights;        // heights[iz][ix]
    this.levels = data.levels || {};
  }

  static async load(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`terrain.json: ${res.status}`);
    return new Terrain(await res.json());
  }

  /** True if (x, z) is inside the sampled grid. Outside it, height() clamps. */
  covers(x, z) {
    return x >= this.min[0] && x <= this.max[0] && z >= this.min[1] && z <= this.max[1];
  }

  /** Ground y at (x, z), bilinear, clamped at the grid edge. */
  height(x, z) {
    const [nx, nz] = this.n;
    let fx = (x - this.min[0]) / this.step;
    let fz = (z - this.min[1]) / this.step;
    fx = Math.min(Math.max(fx, 0), nx - 1.0001);
    fz = Math.min(Math.max(fz, 0), nz - 1.0001);
    const ix = Math.floor(fx), iz = Math.floor(fz);
    const tx = fx - ix, tz = fz - iz;
    const h = this.h;
    const a = h[iz][ix], b = h[iz][ix + 1], c = h[iz + 1][ix], d = h[iz + 1][ix + 1];
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz;
  }

  /**
   * Surface normal from central differences on the same grid, so a thing on a
   * slope tilts with the slope it is actually standing on.
   * Returns [nx, ny, nz], unit length.
   */
  normal(x, z) {
    const e = this.step;
    const dhdx = (this.height(x + e, z) - this.height(x - e, z)) / (2 * e);
    const dhdz = (this.height(x, z + e) - this.height(x, z - e)) / (2 * e);
    const inv = 1 / Math.hypot(dhdx, 1, dhdz);
    return [-dhdx * inv, inv, -dhdz * inv];
  }

  /** Slope in degrees. */
  slope(x, z) {
    const n = this.normal(x, z);
    return Math.acos(Math.min(1, Math.max(-1, n[1]))) * 180 / Math.PI;
  }
}
