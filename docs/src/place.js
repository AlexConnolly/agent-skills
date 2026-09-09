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

// The hero camera and §0.2's breach, the two ends of the protected sight line.
// Kept in step with HERO in camera.js by hand — this module stays free of
// three.js so the bake tool can run it under node, so it cannot import it.
export const HERO_EYE = [87.24, -1.0, 48.82];
export const HERO_AIM = [3.9, 11.3, -6.4];
export const BREACH = [28.8, 1.4, -2.0];

// The camera's ground-plane basis, so things can be placed by where they land
// in the frame instead of by a coordinate that silently rots the next time the
// camera moves.
const _fx = HERO_AIM[0] - HERO_EYE[0], _fz = HERO_AIM[2] - HERO_EYE[2];
const _fl = Math.hypot(_fx, _fz);
export const HERO_FWD = [_fx / _fl, _fz / _fl];
export const HERO_RIGHT = [-HERO_FWD[1], HERO_FWD[0]];

// Half the frame width per metre of depth, at the 54 degree horizontal FOV.
const HALF_W = Math.tan(27 * Math.PI / 180);

/** `along` metres down the view axis, `across` metres right of it. */
function fromCamera(along, across) {
  return {
    x: HERO_EYE[0] + HERO_FWD[0] * along + HERO_RIGHT[0] * across,
    z: HERO_EYE[2] + HERO_FWD[1] * along + HERO_RIGHT[1] * across,
  };
}

// §3 — wind is from the south-west, so everything that leans leans toward the
// north-east. Consistency here is free and its absence is instantly legible.
export const WIND_DIR = [Math.SQRT1_2, -Math.SQRT1_2]; // (+x east, −z north)

// The drove road. data/route.json is generated from demo/build/route.py, the
// same module build_crossing.py and build_track.py sweep, so the ribbon on the
// ground and the clearance the trees are rejected against cannot disagree —
// which they would the moment there were two copies of the road.
//
// setRoad() is called by main.js and by the bake tool once route.json is read.
// The fallback below is only what the rules use if that file is missing.
let TRACK = [
  [130, 78], [104, 61], [79, 43], [62, 32], [49, 26],
  [46, 34], [31, 40], [15, 41], [6, 30],
];
export const setRoad = (points) => { if (points && points.length > 1) TRACK = points; };
export const getRoad = () => TRACK;

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
  // Things do, so the wedge starts much closer: the rule it states is "never on
  // the sight line between the camera and the breach", and a tree at 25 m
  // blocks that line just as completely as one at 40 m. Independent of the
  // camera clearance, because a foreground boulder may stand at 9 m and must
  // still not sit in front of the breach.
  if (d < 12 || d > 85) return false;
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

  // ---- group 2, the rock kit -----------------------------------------
  // These are the one group that belongs ON the landforms the trees are kept
  // off: §5 group 2 puts the outcrops on the platform's batter and the scree
  // below them, so they take terrain-height bands instead of the blanket
  // "never on the platform, never in the ditch" the trees use.
  outcrop_a: { rMin: 44, rMax: 66, minSep: 9, scale: [0.85, 1.20], lean: 0,
               platform: true, yMin: -4.3, yMax: -0.6, slopeMax: 52,
               note: 'breaking through the turf on the platform batter' },
  outcrop_b: { rMin: 40, rMax: 96, minSep: 6, scale: [0.80, 1.25], lean: 0,
               platform: true, ditch: true, yMin: -6.4, yMax: -1.0, slopeMax: 52,
               note: 'ditch sides and the knoll crest' },
  boulder_a: { rMin: 26, rMax: 130, minSep: 5, scale: [0.78, 1.30], lean: 0,
               platform: true, camClear: 9, slopeMax: 40 },
  boulder_b: { rMin: 24, rMax: 130, minSep: 4, scale: [0.75, 1.35], lean: 0,
               platform: true, camClear: 9, slopeMax: 40 },
  scree:     { rMin: 46, rMax: 70, minSep: 11, scale: [0.85, 1.20], lean: 0,
               platform: true, yMin: -5.0, yMax: -2.6, slopeMax: 34,
               note: 'below the outcrops, continuous with the castle rubble spill' },
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
//
// The two repoussoir oaks are positioned by frame, not by coordinate: each
// stands a couple of metres OUTSIDE its edge of the frame so only the upper
// limbs come in, which is what §7 asks for ("its upper limbs break the
// top-left corner and run out of frame") and is also what keeps them off the
// ridge. The ridge is only visible in the outer 0-6 % and 89-100 % of the
// frame — the castle covers the rest of the horizon — and it is the one thing
// stopping the image reading as an object on a table, so a trunk parked in
// either band would be blocking the only horizon there is. A bare oak's limbs
// are mostly gaps and cross those bands high, above the horizon line at ~70 %.
export const HERO_FIXED = {
  oak: [
    { ...fromCamera(20, -(HALF_W * 20 + 2.0)), yaw: 2.35, scale: 1.22, tag: 'repoussoir, frame left' },
    { ...fromCamera(30, +(HALF_W * 30 + 2.2)), yaw: 0.85, scale: 1.06, tag: 'repoussoir, frame right' },
  ],
};

// ------------------------------------------------------------- the builder

function accept(t, rule, x, z) {
  if (!t.covers(x, z)) return false;
  const r = Math.hypot(x, z);
  if (r < rule.rMin || r > rule.rMax) return false;
  if (Math.hypot(x - HERO_EYE[0], z - HERO_EYE[2]) < (rule.camClear ?? CAMERA_CLEAR)) return false;

  const y = t.height(x, z);

  // An explicit height band wins outright: the rock kit is specified by the
  // landform it breaks out of, not by what it must avoid.
  if (rule.yMin !== undefined || rule.yMax !== undefined) {
    if (rule.yMin !== undefined && y < rule.yMin) return false;
    if (rule.yMax !== undefined && y > rule.yMax) return false;
  } else {
    // On the platform top or its berm. The castle footprint sits inside this,
    // so one test covers both.
    if (!rule.platform && r < 72 && y > -1.2) return false;
    // In the ditch. Only gorse, the rocks and the mist are allowed down there.
    if (!rule.ditch && r < 82 && y < -5.2) return false;
    // The pine stand is the ridge and nowhere else.
    if (rule.ridge && y < 2.5) return false;
    if (!rule.ridge && y > 4.6) return false;
  }

  if (t.slope(x, z) > (rule.slopeMax ?? 30)) return false;
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

// ---------------------------------------------------------------- the runs
//
// A drystone wall and a line of hurdles are not scattered objects: they follow
// a boundary, module by module, at a fixed pitch. §5 group 6 and SKILL.md's kit
// rules — 2.00 m pitch on a 2.04 m module, origin on the pitch centre, alternate
// modules flipped 180 degrees, and all the variety in the placement rather than
// in the geometry, because one distinctive module drawn 44 times reads as a
// repeat.
//
// Where a run meets the drove road it simply stops and starts again on the far
// side. A wall does not cross a road; that gap is where the field gate goes.

export const RUNS = [
  {
    id: 'wall_north', piece: 'wall_mod_a', fallen: 'wall_mod_b', pitch: 2.0,
    // Frame-right, running away from the camera across the open field east of
    // the ditch. The near end is inside 25 m of the lens, which §5 group 6 asks
    // for so one stretch is close enough to read as masonry.
    line: [[96.0, 64.0], [78.0, 38.0], [66.0, 14.0], [44.0, 2.0]],
    fallenAt: [[9, 11], [27, 29], [37, 39]],
  },
  {
    id: 'wall_south', piece: 'wall_mod_a', fallen: 'wall_mod_b', pitch: 2.0,
    // Frame-left, along the field edge south of the road. Both runs stop short
    // of the platform toe — a field wall does not climb a castle's batter.
    line: [[86.0, 60.0], [71.0, 45.5], [50.0, 43.0], [38.0, 36.0]],
    fallenAt: [[6, 8], [20, 22]],
  },
  {
    id: 'hurdle_east', piece: 'hurdle', pitch: 1.9,
    // §5: stock fencing across the wet ground east of the ditch.
    line: [[90.0, 29.0], [77.0, 4.0]],
  },
  {
    id: 'hurdle_knoll', piece: 'hurdle', pitch: 1.9,
    line: [[75.5, 55.0], [58.0, 45.5]],
  },
];

function resample(line, pitch) {
  const out = [];
  let carry = 0;
  for (let i = 0; i < line.length - 1; i++) {
    const [ax, az] = line[i], [bx, bz] = line[i + 1];
    const dx = bx - ax, dz = bz - az;
    const len = Math.hypot(dx, dz);
    const ux = dx / len, uz = dz / len;
    for (let s = carry; s < len; s += pitch) out.push([ax + ux * s, az + uz * s, Math.atan2(ux, uz)]);
    carry = (out.length ? pitch - ((len - carry) % pitch) : 0) % pitch;
  }
  return out;
}

/**
 * Walk one boundary and emit a transform per module slot, skipping the slots
 * the road passes through.
 * @returns {{[pieceId: string]: object[]}}
 */
export function placeRun(terrain, run, streamIx) {
  const rnd = mulberry32(SEED + 104729 + streamIx * 6151);
  const slots = resample(run.line, run.pitch);
  const out = {};
  const push = (piece, rec) => { (out[piece] ||= []).push(rec); };

  slots.forEach(([x, z, heading], i) => {
    if (distToPolyline(x, z, TRACK) < TRACK_CLEAR) return;   // the gap for the gate
    if (!terrain.covers(x, z)) return;
    if (terrain.slope(x, z) > 34) return;

    const fallen = (run.fallenAt || []).some(([a, b]) => i >= a && i <= b);
    const piece = fallen ? run.fallen : run.piece;
    if (!piece) return;

    // Alternate 180 degree flip, plus +/-2 cm and +/-1.5 degrees of jitter.
    const flip = (i % 2) ? Math.PI : 0;
    const yaw = heading + flip + (rnd() * 2 - 1) * 1.5 * Math.PI / 180;
    const jx = (rnd() * 2 - 1) * 0.02, jz = (rnd() * 2 - 1) * 0.02;
    const px = x + jx, pz = z + jz;

    // Follow the terrain, so the top line of the wall undulates with the field.
    const n = terrain.normal(px, pz);
    const e = (v) => Math.round(v * 1000) / 1000;
    push(piece, {
      p: [e(px), e(terrain.height(px, pz)), e(pz)],
      up: [e(n[0]), e(n[1]), e(n[2])],
      yaw: e(yaw), s: 1, tag: `${run.id}#${i}`,
    });
  });
  return out;
}

/** Every piece in one object, keyed by kit id. */
export function placeAll(terrain, kits) {
  const out = {};
  // Run-based pieces have no scatter rule: RUNS below fills them in.
  kits.forEach((kit, i) => {
    if (kit.run || !kit.place) return;
    out[kit.id] = placePiece(terrain, kit.place, kit.count, i + 1);
  });
  RUNS.forEach((run, i) => {
    const got = placeRun(terrain, run, i + 1);
    for (const piece of Object.keys(got)) (out[piece] ||= []).push(...got[piece]);
  });
  return out;
}
