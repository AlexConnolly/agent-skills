// Renderer, post chain, sky and fog — ART-DIRECTION §8.2 and §8.3.
//
// THE SKY IS SCENE CODE, NOT A GENERATED OBJECT. About forty lines of GLSL,
// below, sitting in the repo like everything else. The claim this page makes is
// about the objects in the world; it is not about the sky, the lighting, the
// camera or the page, and the notes panel says so.

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { COOL } from './palette.js';

export const BLOOM = { strength: 0.55, radius: 0.5, threshold: 0.85 };
export const EXPOSURE = 1.10;

// ------------------------------------------------------------------- sky

const SKY_VERT = /* glsl */`
varying vec3 vDir;
void main() {
  vDir = position;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const SKY_FRAG = /* glsl */`
precision highp float;
uniform vec3  uZenith;
uniform vec3  uHorizon;
uniform vec3  uMoon;
uniform vec3  uMoonDir;
uniform float uGlow;
uniform float uStarThreshold;
uniform float uStarValue;
uniform float uClamp;
varying vec3 vDir;

float hash31(vec3 p) {
  p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419));
  p *= 17.0;
  return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

void main() {
  vec3 d = normalize(vDir);
  float up = clamp(d.y, 0.0, 1.0);

  // Vertical gradient. pow(1 - y, 3) keeps the lift tight to the horizon
  // instead of washing the whole dome.
  vec3 col = mix(uZenith, uHorizon, pow(1.0 - up, 3.0));

  // The moon is out of frame at 34 degrees in the south-west, but its glow lobe
  // lifts the left-hand sky, and that lift is what silhouettes the gatehouse.
  float lobe = pow(max(dot(d, uMoonDir), 0.0), 8.0);
  col += uMoon * lobe * uGlow;

  // Hash star field. Fades out below 12 degrees and inside the moon lobe.
  vec3 sp = d * 90.0;
  vec3 cell = floor(sp);
  float h = hash31(cell);
  if (h > uStarThreshold) {
    vec3 jitter = vec3(hash31(cell + 1.7), hash31(cell + 3.1), hash31(cell + 5.3)) - 0.5;
    float dd = length(sp - (cell + 0.5 + jitter * 0.6));
    float mag = (h - uStarThreshold) / (1.0 - uStarThreshold);
    float star = smoothstep(0.085, 0.0, dd) * mix(0.35, 1.0, mag);
    star *= smoothstep(0.04, 0.24, d.y);
    star *= 1.0 - clamp(lobe * 2.5, 0.0, 1.0);
    col += vec3(0.86, 0.91, 1.0) * star * uStarValue;
  }

  // The sky can never fight the fires. Everything above uClamp luminance is
  // scaled back rather than clipped, so the gradient stays smooth.
  float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));
  if (luma > uClamp) col *= uClamp / luma;

  gl_FragColor = vec4(col, 1.0);
}
`;

export function makeSky(moonDir) {
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uZenith:        { value: new THREE.Color(COOL.skyZenith) },
      uHorizon:       { value: new THREE.Color(COOL.skyHorizon) },
      uMoon:          { value: new THREE.Color(COOL.moonCold) },
      uMoonDir:       { value: moonDir.clone().normalize() },
      uGlow:          { value: 0.35 },
      uStarThreshold: { value: 0.9915 },  // about 430 stars over the visible dome
      uStarValue:     { value: 0.30 },
      uClamp:         { value: 0.30 },
    },
    vertexShader: SKY_VERT,
    fragmentShader: SKY_FRAG,
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: false,
    fog: false,
    toneMapped: true,
  });

  // §8.3 asks for `scene.background = <a BackSide sphere>`. scene.background
  // only accepts a Color, Texture or CubeTexture, so the dome goes in as a
  // child mesh drawn first with depth writes off. Same picture, real API.
  const sky = new THREE.Mesh(new THREE.SphereGeometry(700, 48, 32), mat);
  sky.name = 'sky_dome';
  sky.renderOrder = -1000;
  sky.frustumCulled = false;
  sky.matrixAutoUpdate = false;
  return sky;
}

// ------------------------------------------------------- renderer and post

export function makeRenderer(canvas) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: false,               // §8.2: pointless with a composer; samples:4 below is the MSAA
    powerPreference: 'high-performance',
    stencil: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  // §8.2 writes `renderer.toneMapping = NoToneMapping` with the comment
  // "OutputPass does it". In three r185 OutputPass reads its tone mapping mode
  // off the renderer, so NoToneMapping there means no tone mapping anywhere.
  // The order the spec actually wants — bloom on linear HDR, ACES last — comes
  // out right like this instead: scene materials skip tone mapping
  // automatically because RenderPass draws into a render target rather than the
  // canvas, and OutputPass then applies ACES to the bloomed result.
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = EXPOSURE;

  renderer.shadowMap.enabled = true;
  // §8.2 asks for PCFSoftShadowMap. r185 deprecates it and silently falls back
  // to PCFShadowMap with a console warning, so it is named explicitly here and
  // the softness comes from moon.shadow.radius instead, which is what the spec
  // wanted moonlight to look like anyway.
  renderer.shadowMap.type = THREE.PCFShadowMap;
  return renderer;
}

export function makeComposer(renderer, scene, camera) {
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const target = new THREE.WebGLRenderTarget(size.x, size.y, {
    type: THREE.HalfFloatType,
    samples: 4,
    colorSpace: THREE.LinearSRGBColorSpace,
  });

  const composer = new EffectComposer(renderer, target);
  composer.setPixelRatio(renderer.getPixelRatio());
  composer.setSize(window.innerWidth, window.innerHeight);

  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  // Bloom BEFORE tone mapping. Backwards, it is a washed grey halo instead of a
  // hot core. At threshold 0.85 only the fires and the lantern panes cross it;
  // moonlit stone peaks near 0.35 and never blooms.
  const bloom = new UnrealBloomPass(
    new THREE.Vector2(size.x, size.y), BLOOM.strength, BLOOM.radius, BLOOM.threshold,
  );
  composer.addPass(bloom);

  const out = new OutputPass();
  composer.addPass(out);

  return { composer, bloom, renderPass, out, target };
}

export function makeScene() {
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(COOL.fog, 0.0045);
  return scene;
}
