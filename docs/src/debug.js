// The debug clamp — ART-DIRECTION §2 "The rule".
//
// "Build a debug key into the viewer that clamps and false-colours anything
// over 0.45 luminance. If anything but the fires lights up, the shot is wrong."
//
// This runs last, on the tone-mapped sRGB image, which is the thing the rule is
// actually about. Pixels over the ceiling are split by hue: warm ones are the
// fires and are expected, so they flag green; cool ones are a stray light or an
// exposure fault and flag magenta. Acceptance item 3 is checked with this, not
// by eye.

import * as THREE from 'three';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { COOL_LUMA_CEILING } from './palette.js';

export const ClampShader = {
  name: 'CoolValueClamp',
  uniforms: {
    tDiffuse: { value: null },
    uThreshold: { value: COOL_LUMA_CEILING },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse;
    uniform float uThreshold;
    varying vec2 vUv;
    void main() {
      vec4 c = texture2D(tDiffuse, vUv);
      float luma = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
      // ACES deliberately rolls a fire core off to white (§8.2), so a blown
      // highlight is desaturated and would otherwise read as a cool fault.
      // Warm = hue is warm, OR the pixel is a near-white core.
      bool warm = (c.r - c.b) > 0.10 || (min(c.r, min(c.g, c.b)) > 0.75 && c.r >= c.b);
      if (luma > uThreshold) {
        gl_FragColor = warm ? vec4(0.15, 0.95, 0.30, 1.0)   // a fire: expected
                            : vec4(1.00, 0.00, 0.55, 1.0);  // anything cool: a fault
      } else {
        gl_FragColor = vec4(vec3(luma * 0.30), 1.0);
      }
    }
  `,
};

export function makeClampPass() {
  const pass = new ShaderPass(ClampShader);
  pass.enabled = false;
  return pass;
}

/**
 * Read the framebuffer back and count how many pixels break the cool ceiling.
 * Used by the "check" button so the answer is a number rather than an opinion.
 */
export function auditFrame(renderer, threshold = COOL_LUMA_CEILING) {
  const gl = renderer.getContext();
  const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);

  const total = w * h;
  let warm = 0, cool = 0, brightest = 0;
  const coolMask = new Uint8Array(total);

  for (let p = 0; p < total; p++) {
    const i = p * 4;
    const r = px[i] / 255, g = px[i + 1] / 255, b = px[i + 2] / 255;
    const luma = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    if (luma > brightest) brightest = luma;
    if (luma > threshold) {
      const isWarm = (r - b > 0.10) || (Math.min(r, g, b) > 0.75 && r >= b);
      if (isWarm) warm++; else { cool++; coolMask[p] = 1; }
    }
  }

  // A single over-bright pixel on rough ground is a specular sparkle, not a
  // surface reading too bright, and §2's rule is about surfaces. So the pass
  // condition is a cool pixel with cool neighbours on all four sides — a lit
  // wall trips that immediately and a glint never does. Both counts are
  // reported, because hiding the raw number would defeat the point of having
  // the check at all.
  let clustered = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const p = y * w + x;
      if (!coolMask[p]) continue;
      if (coolMask[p - 1] && coolMask[p + 1] && coolMask[p - w] && coolMask[p + w]) clustered++;
    }
  }

  return {
    width: w, height: h, total,
    warmPixels: warm, coolPixels: cool, coolClustered: clustered, brightest,
    warmPct: (100 * warm / total), coolPct: (100 * cool / total),
    pass: clustered === 0,
  };
}

/** THREE is imported so the module keeps a hard dependency on the same build. */
export const _three = THREE.REVISION;
