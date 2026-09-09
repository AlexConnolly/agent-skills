// The by-name material tune-up — ART-DIRECTION §8.5.
//
// This is the tuning surface for the entire scene and it is meant to be the
// first place anyone looks. Every emissive intensity, every transparency and
// every roughness override lives in TUNING as plain data, dispatched on the
// material name the build script gave the object in Blender. Editing a number
// here and reloading takes a second; rebuilding a .glb takes a minute, which is
// why §3.6 says to keep the numbers on this side of the export.
//
// The build scripts export every emissive material at emissive = 1.0 and let
// this table set the real intensity.

import * as THREE from 'three';
import { WARM, COOL } from './palette.js';

// name -> what to do with it. Longest matching prefix wins.
export const TUNING = {
  // ---- emissive, §3.6 ------------------------------------------------
  // `bloom` is a note to the reader, not a switch: with UnrealBloomPass at
  // threshold 0.85, these are the only materials in the scene that cross it.
  emis_fire_core:  { emissive: WARM.fireCore,  intensity: 5.2, bloom: true },
  emis_fire_flame: { emissive: WARM.fireFlame, intensity: 3.0, bloom: true },
  emis_tallow:     { emissive: WARM.tallow,    intensity: 2.0, bloom: true },
  emis_ember:      { emissive: WARM.ember,     intensity: 2.5, bloom: false },

  // ---- translucent, §3 group 3 and §7 -------------------------------
  plume_vapour: { transparent: true, opacity: 0.13, depthWrite: false, side: 'double', color: COOL.mistPale, roughness: 1.0 },
  // build_mist.py names the material plain `mist`; the prefix match covers
  // `mist_*` too if that ever changes.
  mist:         { transparent: true, opacity: 0.11, depthWrite: false, side: 'double', color: COOL.mistPale, roughness: 1.0 },

  // ---- surfaces ------------------------------------------------------
  water_: { roughness: 0.06, metalness: 0.0, envMapIntensity: 0 },
  track_: { roughness: 0.35 },

  // timber_evergreen is set here to the value the glb ALREADY carries, not as a
  // correction. An earlier note in this file claimed build_trees.py shipped
  // #55705C, a mid green; it does not. That value lives only behind its
  // TREE_LOOK=1 debug flag, and the exported base-colour factors read back as
  // #0C1310 on tree_yew, tree_pine and scrub_gorse — checked in the glb bytes.
  // Left explicit because the yews and gorse are the pieces most at risk of
  // reading as green blobs if anything ever does drift.
  timber_evergreen: { color: 0x0C1310, roughness: 0.9, metalness: 0.0, envMapIntensity: 0.25 },
};

// §3.6 gives one intensity for the bonfire heart (6.0) and another for the
// brazier baskets (4.5), but both are the same Blender material. Splitting them
// by the object they belong to keeps the table honest and the look right.
export const PER_OBJECT_EMISSIVE = {
  bonfire: { emis_fire_core: 6.0 },
  brazier: { emis_fire_core: 4.5 },
  cresset: { emis_fire_flame: 3.5 },
  // §3.6 says 2.2. Pulled back to 1.8 because the bridge lantern is the nearest
  // emissive object to the lens (36 m) and at 2.2 its bloom disc is the largest
  // bright area in the frame — which puts the eye at 47 % and holds it there,
  // against the §7 plan that wants it as step 2 of the path and no more.
  lantern: { emis_tallow: 1.8 },
  pane_window: { emis_tallow: 1.6 },
  pane_hall: { emis_tallow: 1.6 },
  pane_loop: { emis_tallow: 1.6 },
  pane_lancet: { emis_tallow: 1.6 },
  pane_passage: { emis_tallow: 1.2 },
  oven_mouth: { emis_ember: 2.5 },
};

// Everything not named above.
const DEFAULT = { envMapIntensity: 0.25 };

function lookup(name) {
  let hit = null, hitLen = -1;
  for (const key of Object.keys(TUNING)) {
    if (name.startsWith(key) && key.length > hitLen) { hit = TUNING[key]; hitLen = key.length; }
  }
  return hit;
}

/**
 * Walk a loaded glTF scene and apply the table.
 * @param {THREE.Object3D} root
 * @param {object} opts  { assetId, castShadow, receiveShadow }
 * @returns {{emissive: THREE.Material[], transparent: THREE.Material[]}}
 */
export function tuneMaterials(root, opts = {}) {
  const found = { emissive: [], transparent: [] };
  const perObject = PER_OBJECT_EMISSIVE[opts.assetId] || {};

  root.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];

    o.castShadow = opts.castShadow !== false;
    o.receiveShadow = opts.receiveShadow === true;

    for (const m of mats) {
      const name = m.name || '';
      const t = lookup(name);

      if (t && t.intensity !== undefined) {
        // Emissive: never shadowed, never a shadow caster. A shadowed glowing
        // plate is a stain, and an emissive plate casting a shadow is a lie.
        m.emissive = new THREE.Color(t.emissive);
        m.emissiveIntensity = perObject[name] !== undefined ? perObject[name] : t.intensity;
        m.color = new THREE.Color(0x000000);
        m.roughness = 1.0;
        m.metalness = 0.0;
        m.toneMapped = true;
        m.userData.emissiveBase = m.emissiveIntensity;
        o.castShadow = false;
        o.receiveShadow = false;
        found.emissive.push(m);
      } else if (t && t.transparent) {
        m.transparent = true;
        m.opacity = t.opacity;
        m.depthWrite = false;
        m.side = t.side === 'double' ? THREE.DoubleSide : THREE.FrontSide;
        if (t.color !== undefined) m.color = new THREE.Color(t.color);
        if (t.roughness !== undefined) m.roughness = t.roughness;
        m.metalness = 0.0;
        m.fog = true;
        // Not on the mist: a shadowed translucent slab is a grey stain.
        o.castShadow = false;
        o.receiveShadow = false;
        found.transparent.push(m);
      } else if (t) {
        for (const [k, v] of Object.entries(t)) {
          if (k === 'color' || k === 'emissive') m[k] = new THREE.Color(v);
          else m[k] = v;
        }
        m.shadowSide = THREE.FrontSide;
      } else {
        m.envMapIntensity = DEFAULT.envMapIntensity;
        m.shadowSide = THREE.FrontSide;
      }

      m.needsUpdate = true;
    }
  });

  return found;
}
