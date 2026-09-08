// The moon, the hemisphere, the seven, and the flicker — ART-DIRECTION §3.
//
// The budget is one shadow-casting light, seven point lights, no shadows on any
// of them. All eight are created up front and none is ever added or removed at
// runtime: MeshStandardMaterial recompiles per light count, and a recompile
// mid-scene is a visible hitch.
//
// The discipline the whole look rests on: emissive materials do the look, point
// lights do the spill. An emissive material does not illuminate its
// neighbours, so without a point light beside it a brazier is an orange sticker
// on a black wall.

import * as THREE from 'three';
import { WARM, COOL, AMBIENT } from './palette.js';

export const MOON_POSITION = new THREE.Vector3(-115, 112, 115);
export const MOON_TARGET = new THREE.Vector3(0, 6, 0);

// §3.4's point-light intensities are candela-per-legacy-units: three removed
// `useLegacyLights` at r165, and the factor of PI that used to be folded into
// punctual lights went with it. Applied straight, the spec's numbers put the
// bonfire's spill about three and a half stops under where the table clearly
// intends it. One documented constant restores the whole table's balance at
// once rather than seven hand-edited numbers, so §3.4 stays readable as
// written and the ratios between the seven lights are preserved exactly.
export const POINT_SCALE = Math.PI;

// And then one exception. §3.4 calls light 1 "The picture" and §9 item 7 makes
// it an acceptance condition: the breach must be the brightest thing in the
// frame. It cannot be, on the scaled value alone — see the note in POINTS —
// so the bonfire carries a further tuning boost. §3.4 authorises exactly this:
// "Tune every intensity against the final exposure; these are starting values,
// not gospel."
const BONFIRE_BOOST = 2.3;

// §3.4. `binds` names the fixture placements whose emissive materials should
// ride the same flicker signal as the light — that agreement between the light
// and the flame is what sells it.
export const POINTS = [
  // The fire itself cannot be seen from the hero camera and no tuning changes
  // that: the eye is 1 m BELOW the ward floor (§4.1), the breach stub as built
  // stands 0.94-2.13 m above it, and the bonfire is 1.40 m tall sitting 4.8 m
  // further in. The sight line clears the stub at about 2.4 m, so the flames
  // are behind it. What reaches the frame is the light — up the inside of the
  // east wall, along the parapet, across the chapel roof and out over the spoil
  // heap — which is what §1 actually describes: "through the gap comes the
  // light of a fire burning in the ward". Nothing here was moved to fake it.
  { key: 'bonfire',   name: 'Ward bonfire',
    pos: [24.0, 1.6, -2.0],  color: WARM.fireSpill, intensity: 26,  distance: 32,
    boost: BONFIRE_BOOST,
    flicker: true, binds: [['bonfire', 0]],
    job: 'The picture. Just inside the breach, so its light escapes through the gap and rakes the spoil heap outside.' },

  { key: 'gate_brazier', name: 'Gate-passage brazier',
    pos: [6.0, 2.2, 26.2],   color: WARM.fireFlame, intensity: 9,   distance: 18,
    flicker: true, binds: [['brazier', 0]],
    job: 'Lights the passage vault and the causeway; the frame-left anchor.' },

  { key: 'walk_brazier', name: 'Wall-walk brazier over the gate',
    pos: [6.0, 11.6, 22.0],  color: WARM.fireFlame, intensity: 6,   distance: 15,
    flicker: true, binds: [['brazier', 1]],
    job: 'A warm top-note on the gatehouse so it is not purely a moon silhouette.' },

  { key: 'oven',      name: 'Bake-house oven',
    pos: [23.6, 1.8, 16.6],  color: WARM.fireSpill, intensity: 6,   distance: 14,
    flicker: true, binds: [['oven_mouth', 0]],
    job: 'Second warm point inside the ward, visible over the south wall as a glow on the smoke.' },

  { key: 'hall_door', name: 'Hall doorway',
    pos: [-19.6, 2.2, 6.3],  color: WARM.tallow,    intensity: 5,   distance: 18,
    flicker: false, binds: [['brazier', 2]],
    job: 'Never directly seen. Its job is to light the far side of the ward so the breach reads as depth, not a hole.' },

  { key: 'keep_window', name: 'Keep window',
    pos: [-9.5, 14.6, 1.5],  color: WARM.tallow,    intensity: 3,   distance: 10,
    flicker: false, binds: [],
    job: 'Warms the ashlar around the lit windows so they are set into stone rather than stuck on. Steady — a candle behind a shutter does not flicker.' },

  { key: 'bridge_lantern', name: 'Bridge lantern',
    pos: [48.0, -0.4, 24.6], color: WARM.fireCore,  intensity: 3.5, distance: 12,
    flicker: true, binds: [['lantern', 0]],
    job: 'Foreground. Its reflection in the ditch water is the whole reason it exists.' },
];

// Golden-ratio phases: three incommensurate offsets per light, so no two fires
// ever beat together.
const PHI = 1.6180339887;
const phases = (i) => [
  (i * PHI * 6.2831853) % 6.2831853,
  (i * PHI * PHI * 6.2831853) % 6.2831853,
  (i * PHI * PHI * PHI * 6.2831853) % 6.2831853,
];

export class Lighting {
  constructor(scene) {
    // ---- the moon, §3.1 -------------------------------------------------
    // South-west at 34 degrees, which puts it behind and to the camera's left.
    // It lights the south elevation, the west flanks of the round towers and
    // everything upward-facing. It does not light the east elevation, which is
    // the whole camera-facing mass, and that is deliberate.
    const moon = new THREE.DirectionalLight(COOL.moonCold, 0.85);
    moon.position.copy(MOON_POSITION);
    moon.target.position.copy(MOON_TARGET);
    moon.castShadow = true;
    moon.shadow.mapSize.set(2048, 2048);
    const c = moon.shadow.camera;
    c.left = -75; c.right = 75; c.top = 62; c.bottom = -62; c.near = 60; c.far = 340;
    c.updateProjectionMatrix();
    moon.shadow.bias = -0.0006;
    moon.shadow.normalBias = 0.35;
    moon.shadow.radius = 3;
    scene.add(moon, moon.target);

    // ---- the fill, §3.2 -------------------------------------------------
    // A hemisphere, not an AmbientLight. Upward-facing surfaces pick up cold
    // sky and downward-facing ones go near-black, which is what makes unlit
    // geometry read at all. An ambient light flattens the castle to grey.
    const hemi = new THREE.HemisphereLight(AMBIENT.sky, AMBIENT.ground, 0.55);
    scene.add(hemi);

    // ---- the seven, §3.4 ------------------------------------------------
    this.points = POINTS.map((spec, i) => {
      const intensity = spec.intensity * POINT_SCALE * (spec.boost || 1);
      const light = new THREE.PointLight(spec.color, intensity, spec.distance, 2);
      light.position.fromArray(spec.pos);
      light.castShadow = false;
      light.name = spec.key;
      scene.add(light);
      return {
        spec, light,
        base: intensity,
        home: light.position.clone(),
        phase: phases(i + 1),
        materials: [],   // filled by bind()
      };
    });

    this.moon = moon;
    this.hemi = hemi;
    this.scene = scene;
    this.moonDir = MOON_POSITION.clone().sub(MOON_TARGET).normalize();
  }

  /**
   * Attach emissive materials to the lights that share their flicker signal.
   * @param {Map<string, THREE.Material[]>} byPlacement  key `${assetId}#${index}`
   */
  bind(byPlacement) {
    for (const p of this.points) {
      for (const [id, idx] of p.spec.binds) {
        const mats = byPlacement.get(`${id}#${idx}`);
        if (mats) p.materials.push(...mats);
      }
    }
  }

  /**
   * §3.5. One signal per light drives intensity, a +/-3 cm position jitter and
   * the bound materials' emissiveIntensity, so the light and the flame agree.
   */
  update(t) {
    for (const p of this.points) {
      let f = 1;
      if (p.spec.flicker) {
        const [a, b, c] = p.phase;
        f = 1
          + 0.07 * Math.sin(2.3 * t + a)
          + 0.05 * Math.sin(3.7 * t + b)
          + 0.04 * Math.sin(0.9 * t + c);
        p.light.position.set(
          p.home.x + 0.03 * Math.sin(2.3 * t + a),
          p.home.y + 0.03 * Math.sin(3.7 * t + b),
          p.home.z + 0.03 * Math.sin(0.9 * t + c),
        );
      }
      p.light.intensity = p.base * f;
      for (const m of p.materials) {
        if (m.userData.emissiveBase !== undefined) m.emissiveIntensity = m.userData.emissiveBase * f;
      }
    }
  }
}
