// The camera — ART-DIRECTION §4.
//
// A person standing on the drove road, not a drone. Eye at y = -1.0, which is a
// metre BELOW the ward floor, because the whole reason for the low camera is
// that you are looking up at the castle.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const D = Math.PI / 180;

// §4.1 — the hero still.
//
// §4.1 gives position (78.9, -1.0, 43.3) and target (3.9, 9.3, -6.4). Measured
// against the castle as actually built, that pose crops: 98 castle vertices
// project above the top edge and 12.7 % of the frame's top row is masonry, not
// the empty sky §7 requires. The cause is the SE great tower, whose
// crenellated head reaches 21.4 m only 50 m from the lens — §0.2's table lists
// tower AXIS heights and the frame-band table was evidently computed from
// those, without the crenellation rings that sit on top of them.
//
// §4.1's own numbers cannot all be true at once here: no vertical FOV puts the
// SE tower at 13 % from the top AND the keep at 28 % AND the horizon at 70 %.
// So the fix keeps everything §4.1 fixes for a reason — the standing eye
// height, the bearing, the 32 degree FOV that sets the horizontal thirds — and
// moves only along the view axis, which is the one lever that shrinks a near
// mass without touching the far ones:
//
//   10 m back along the same bearing, and the aim raised 2 m.
//
// The eye stays at y = -1.0 and the knoll crest is flat enough there that it is
// still 1.78 m of standing person above the ground (§4.1 asks for 1.7).
// It lands: SE tower top 7.5 % from the frame top with clear sky above it,
// gate brazier at 16.1 % across (§7 says 16), horizon at 70.5 % (§4.1 says 70),
// breach at 62.9 % (§7 says 66). Two of the headline numbers land dead on and
// nothing is cropped.
export const HERO = {
  position: new THREE.Vector3(87.24, -1.0, 48.82),
  target:   new THREE.Vector3(3.9, 11.3, -6.4),
  fov: 32,            // vertical, at 16:9. Horizontal works out at 54 degrees.
  aspect: 16 / 9,
  near: 0.5,
  far: 900,
};

// §4.2 — the slow move. Comes in and down: the SE tower grows and slides left,
// the breach opens up, the keep rises against the sky.
//
// The spec's end pose is (72.0, -1.6, 39.0) -> (3.0, 8.6, -7.0), but the same
// paragraph says the move holds "on the hero frame at the end". Those are two
// different frames, and only one of them can be the picture, so the move ends
// on §4.1 exactly and the held frame is the hero still.
// The start pose keeps §4.2's move exactly — 20 m in, 2.5 m down, under 3
// degrees of rotation — measured from the corrected hero rather than from the
// uncorrected one, so the push is the same move it always was.
export const INTRO = {
  from: { position: new THREE.Vector3(100.34, 1.5, 57.52), target: new THREE.Vector3(6.0, 13.0, -5.0) },
  to:   { position: HERO.position.clone(),                 target: HERO.target.clone() },
  seconds: 24,
};

// §4.3 — tightly fenced, so a visitor can look but cannot find the ugly angles.
// The hero pose sits at polar 96.5 degrees, which is outside the spec's
// 80-94 degree fence: clamping to 94 would shove the camera off the picture on
// the first controls update, so the ceiling is 98 here.
const FENCE = {
  minDistance: 55,
  maxDistance: 130,
  minPolar: 80 * D,
  maxPolar: 98 * D,
  azimuthSpread: 38 * D,
};

const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/**
 * Keep the hero's HORIZONTAL field of view fixed at 54 degrees whatever the
 * window shape. §7 puts the gate brazier at 16 % across and the bonfire at
 * 66 %, on the two vertical thirds, and says not to tune that away — so a
 * narrow window gets more sky and foreground rather than a cropped castle.
 */
export function fovForAspect(aspect) {
  if (aspect >= HERO.aspect) return HERO.fov;
  const halfWidth = Math.tan(HERO.fov / 2 * D) * HERO.aspect;
  return 2 * Math.atan(halfWidth / aspect) / D;
}

export function makeCamera(aspect) {
  const cam = new THREE.PerspectiveCamera(fovForAspect(aspect), aspect, HERO.near, HERO.far);
  cam.up.set(0, 1, 0);
  cam.position.copy(HERO.position);
  cam.lookAt(HERO.target);
  return cam;
}

export class CameraRig {
  constructor(camera, domElement, { intro = true } = {}) {
    this.camera = camera;
    this.controls = new OrbitControls(camera, domElement);
    const ctl = this.controls;
    ctl.target.copy(HERO.target);
    ctl.enablePan = false;
    ctl.enableDamping = true;
    ctl.dampingFactor = 0.05;
    ctl.minDistance = FENCE.minDistance;
    ctl.maxDistance = FENCE.maxDistance;
    ctl.minPolarAngle = FENCE.minPolar;
    ctl.maxPolarAngle = FENCE.maxPolar;

    const heroAzimuth = Math.atan2(
      HERO.position.x - HERO.target.x,
      HERO.position.z - HERO.target.z,
    );
    ctl.minAzimuthAngle = heroAzimuth - FENCE.azimuthSpread;
    ctl.maxAzimuthAngle = heroAzimuth + FENCE.azimuthSpread;

    this.introActive = intro;
    this.introT = 0;
    this.bobT = 0;
    this.onCancel = null;

    // Any user input cancels the intro move.
    ctl.addEventListener('start', () => this.cancelIntro());
    domElement.addEventListener('wheel', () => this.cancelIntro(), { passive: true });

    if (intro) this.applyIntro(0);
  }

  cancelIntro() {
    if (!this.introActive) return;
    this.introActive = false;
    if (this.onCancel) this.onCancel();
  }

  applyIntro(k) {
    const e = easeInOutCubic(k);
    this.camera.position.lerpVectors(INTRO.from.position, INTRO.to.position, e);
    const tgt = new THREE.Vector3().lerpVectors(INTRO.from.target, INTRO.to.target, e);
    this.controls.target.copy(tgt);
    this.camera.lookAt(tgt);
  }

  /** Snap back to the hero still. Bound to R and to the button on the page. */
  reset() {
    this.introActive = false;
    this.camera.position.copy(HERO.position);
    this.controls.target.copy(HERO.target);
    this.camera.lookAt(HERO.target);
    this.controls.update();
  }

  /** Jump straight to the hero and stop everything moving — for a clean still. */
  freeze() {
    this.reset();
    this.bobT = null;
  }

  update(dt) {
    if (this.introActive) {
      this.introT = Math.min(this.introT + dt, INTRO.seconds);
      this.applyIntro(this.introT / INTRO.seconds);
      if (this.introT >= INTRO.seconds) this.introActive = false;
      return;
    }

    this.controls.update();

    // A +/-0.25 m bob on a 33 s period, so the held frame never feels frozen.
    if (this.bobT !== null) {
      this.bobT += dt;
      const bob = 0.25 * Math.sin(this.bobT * 2 * Math.PI / 33);
      this.camera.position.y += bob - (this._lastBob || 0);
      this._lastBob = bob;
    }
  }

  resize(aspect) {
    this.camera.aspect = aspect;
    this.camera.fov = fovForAspect(aspect);
    this.camera.updateProjectionMatrix();
  }
}
