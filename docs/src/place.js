// Seeded, frozen placement — ART-DIRECTION §8.6.
//
// Never Math.random(). The hero shot has to be reproducible from a cold load or
// every screenshot is a different picture, so everything here runs off
// mulberry32 with a fixed constant and one independent stream per kit piece
// (adding a piece therefore cannot reshuffle the pieces beside it).
//
// This module is deliberately free of three.js: it emits plain numbers, so
// tools/bake-placement.mjs can run exactly this code under node to freeze
// data/placement.json, and the page and the bake step cannot disagree.

export const SEED = 0x6D617263; // "marc" — of the March

// -------------------------------------------------------------------- PRNG

export function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ------------------------------------------------------- world constants

// §4.1 hero camera and §0.2 breach, the two ends of the protected sight line.
export const HERO_EYE = [78.9, -1.0, 43.3];
export const BREACH = [28.8, 1.4, -2.0];

// §3 — wind is from the south-west, so everything that leans leans toward the
// north-east. Consistency here is free and its absence is instantly legible.
export const WIND_DIR = [Math.SQRT1_2, -Math.SQRT1_2]; // (+x east, −z north)

// The drove road, ART-DIRECTION §5 group 5: up from the east, over the ditch by
// timber bridge on the ESE, onto the berm, then anticlockwise round the south
// side of the platform to the gate. Frozen here because the tree rejection
// needs it before build_edges.py exists; build_edges.py must sweep this same
// polyline.
export const TRACK = [
  [128, 64], [104, 55], [ 88, 48], [ 72, 40], [ 60, 32],
  [ 48, 24], [ 45, 30], [ 40, 35], [ 30, 37.5], [ 18, 35.5],
  [ 10, 32], [  6, 29.6],
];

// 3 m of clearance either side of the 4.4 m ribbon, measured from its centre.
const TRACK_CLEAR = 3.0 + 2.2;

// ---------------------------------------------------------------- geometry

function distToPolyline(x, z, poly) {
  let best = Infinity;
  for (let i = 0; i < poly.length - 1; i++) {
    const [ax, az] = poly[i], [bx, bz] = poly[i + 1];
    const dx = bx - ax, dz = bz - az;
    const len2 = dx * dx + dz * dz;
    let t = len2 > 0 ? ((x - ax) * dx + (z - az) * dz) / len2 : 0;
    t = Math.min(1, Math.max(0, t));
    const d = Math.hypot(x - (ax + t * dx), z - (az + t * dz));
    if (d < best) best = d;
  }
  return best;
}

// The 22° wedge on the hero bearing between 35 m and 80 m. Nothing stands in
// the line between the camera and the breach — the breach is the picture.
function inSightWedge(x, z) {
  const vx = x - HERO_EYE[0], vz = z - HERO_EYE[2];
  const d = Math.hypot(vx, vz);
  // §5 group 1 says 35 m to 80 m, on the assumption that nothing stands nearer.
  // Things do, so the wedge starts at the camera clearance instead: the rule it
  // states is "never on the sight line between the camera and the breach", and
  // a tree at 25 m blocks that line just as completely as one at 40 m.
  if (d < CAMERA_CLEAR || d > 85) return false;
  const bx = BREACH[0] - HERO_EYE[0], bz = BREACH[2] - HERO_EYE[2];
  const bl = Math.hypot(bx, bz);
  const cos = (vx * bx + vz * bz) / (d * bl);
  return cos > Math.cos(11 * Math.PI / 180); // half-angle
}

// ----------------------------------------------------------- the rule sets
//
// One entry per kit piece. `count` comes from the manifest; everything else is
// the piece's own idea of where it belongs, from ART-DIRECTION §5 group 1.

export const RULES = {
  oak:      { rMin: 52, rMax: 168, minSep: 11, scale: [0.82, 1.24], lean: 1.5, ditch: false },
  ash:      { rMin: 78, rMax: 158, minSep: 13, scale: [0.86, 1.20], lean: 1.5, ditch: false },
  hawthorn: { rMin: 42, rMax: 142, minSep:  7, scale: [0.82, 1.24], lean: 3.0, ditch: false },
  yew:      { rMin: 122, rMax: 188, minSep: 10, scale: [0.85, 1.18], lean: 1.0, ditch: false },
  pine:     { rMin: 138, rMax: 196, minSep:  9, scale: [0.84, 1.22], lean: 1.5, ditch: false,
              ridge: true },
  gorse:    { rMin: 26, rMax: 98, minSep: 3.2, scale: [0.75, 1.30], lean: 2.0, ditch: true },
  deadfall: { rMin: 45, rMax: 124, minSep: 14, scale: [0.88, 1.16], lean: 0, ditch: false },
};

// Nothing the rules place may stand in the near foreground. The camera is 90 m
// out from the origin, which is inside several pieces' radius bands, so without
// this a 1.2 m gorse bush lands 13 m from the lens and fills a sixth of the
// frame. Only the hand-placed hero instances below are allowed inside it.
const CAMERA_CLEAR = 18;

// Placed by hand against the hero frame, not by the rules — ART-DIRECTION §7
// "repoussoir", and the two yews the brief puts beside the wayside cross.
// These go in first and the rules place around them.
//
// §5 group 1 also asks for two yews beside the wayside cross. They are not
// here, and that is deliberate. The near foreground on this camera is a narrow
// band: the platform toe begins about 35 m out, so anything standing in front
// of it is between 18 and 35 m from the lens, and at that range a 7 m yew
// covers 10 % to 45 % of the frame width — precisely where the gatehouse, the
// gate brazier and the SE great tower are. §7 protects all three by name. The
// foreground objects that paragraph actually calls for are short ones: a 2.8 m
// wayside cross, mist, rut pools. So all ten yews go to the treeline by rule,
// and the two by the cross should be placed once build_clutter.py exists and
// the cross's final position is known — placing them beside an object that has
// not been built yet would be guessing twice.
export const HERO_FIXED = {
  oak: [
    { x: 58.4, z: 41.7, yaw: 2.35, scale: 1.22, tag: 'repoussoir, frame left' },
    { x: 61.9, z: 14.7, yaw: 0.85, scale: 1.06, tag: 'repoussoir, frame right' },
  ],
};

// ------------------------------------------------------------- the builder

function accept(t, rule, x, z) {
  if (!t.covers(x, z)) return false;
  const r = Math.hypot(x, z);
  if (r < rule.rMin || r > rule.rMax) return false;
  if (Math.hypot(x - HERO_EYE[0], z - HERO_EYE[2]) < CAMERA_CLEAR) return false;

  const y = t.height(x, z);

  // On the platform top or its berm. The castle footprint sits inside this,
  // so one test covers both.
  if (r < 72 && y > -1.2) return false;

  // In the ditch. Only gorse and (later) the mist are allowed down there.
  if (!rule.ditch && r < 82 && y < -5.2) return false;

  // The pine stand is the ridge and nowhere else.
  if (rule.ridge && y < 2.5) return false;
  if (!rule.ridge && y > 4.6) return false;

  if (t.slope(x, z) > 30) return false;
  if (distToPolyline(x, z, TRACK) < TRACK_CLEAR) return false;
  if (inSightWedge(x, z)) return false;
  return true;
}

/**
 * Generate the frozen transform list for one kit piece.
 * @param {Terrain} terrain
 * @param {string} key      a key of RULES
 * @param {number} count    how many instances the manifest asks for
 * @param {number} streamIx a stable per-piece index, so streams stay independent
 */
export function placePiece(terrain, key, count, streamIx) {
  const rule = RULES[key];
  if (!rule) throw new Error(`no placement rule for "${key}"`);
  const rnd = mulberry32(SEED + streamIx * 7919);

  const out = [];
  const push = (x, z, yaw, scale, tag) => {
    const y = terrain.height(x, z);
    const n = terrain.normal(x, z);

    // Tilt with the slope, up to 12°, then clamp — §8.6 step 3.
    let [nx, ny, nz] = n;
    const tilt = Math.acos(Math.min(1, ny));
    const maxTilt = 12 * Math.PI / 180;
    if (tilt > maxTilt) {
      const k = Math.tan(maxTilt) / Math.tan(tilt);
      nx *= k; nz *= k;
      const l = Math.hypot(nx, 1, nz);
      nx /= l; ny = 1 / l; nz /= l;
    }

    // Then lean on the wind bearing, on top of the slope.
    const lean = (rule.lean ? (rnd() * 2 - 1) * rule.lean : 0) * Math.PI / 180;
    if (lean !== 0) {
      nx += WIND_DIR[0] * Math.tan(lean);
      nz += WIND_DIR[1] * Math.tan(lean);
      const l = Math.hypot(nx, ny, nz);
      nx /= l; ny /= l; nz /= l;
    }

    const e = (v) => Math.round(v * 1000) / 1000;
    out.push({ p: [e(x), e(y), e(z)], up: [e(nx), e(ny), e(nz)], yaw: e(yaw), s: e(scale), ...(tag ? { tag } : {}) });
  };

  // 1. the hand-placed hero instances, if this piece has any
  for (const f of (HERO_FIXED[key] || [])) {
    if (out.length >= count) break;
    push(f.x, f.z, f.yaw, f.scale, f.tag);
  }

  // 2. candidates from a jittered grid over the sampled world
  const cell = 7.5;
  const lo = -200, hi = 200;
  const cand = [];
  for (let gz = lo; gz < hi; gz += cell) {
    for (let gx = lo; gx < hi; gx += cell) {
      const x = gx + rnd() * cell;
      const z = gz + rnd() * cell;
      if (accept(terrain, rule, x, z)) cand.push([x, z]);
    }
  }

  // 3. deterministic shuffle, then take with a minimum separation
  for (let i = cand.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [cand[i], cand[j]] = [cand[j], cand[i]];
  }

  const sep2 = rule.minSep * rule.minSep;
  for (const [x, z] of cand) {
    if (out.length >= count) break;
    let clear = true;
    for (const o of out) {
      const dx = o.p[0] - x, dz = o.p[2] - z;
      if (dx * dx + dz * dz < sep2) { clear = false; break; }
    }
    if (!clear) continue;
    const yaw = rnd() * Math.PI * 2;
    const scale = rule.scale[0] + rnd() * (rule.scale[1] - rule.scale[0]);
    push(x, z, yaw, scale);
  }

  return out;
}

/** Every piece in one object, keyed by kit id. */
export function placeAll(terrain, kits) {
  const out = {};
  kits.forEach((kit, i) => { out[kit.id] = placePiece(terrain, kit.place, kit.count, i + 1); });
  return out;
}
