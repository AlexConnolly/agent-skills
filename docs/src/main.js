// Boot, loop, resize — ART-DIRECTION §8.

import * as THREE from 'three';
import { makeScene, makeRenderer, makeComposer, makeSky, BLOOM, EXPOSURE } from './scene.js';
import { makeCamera, CameraRig, HERO } from './camera.js';
import { Lighting } from './lights.js';
import { Terrain } from './terrain.js';
import { placeAll, SEED } from './place.js';
import { SceneAssets } from './load.js';
import { makeClampPass, auditFrame } from './debug.js';
import { SCENERY, FIXTURES, MIST, KITS, PENDING, HAND_WRITTEN, SOURCES, repoUrl } from './manifest.js';

const ASSET_BASE = 'assets';
const $ = (id) => document.getElementById(id);
const say = (msg) => { const el = $('loading-note'); if (el) el.textContent = msg; };

async function boot() {
  const canvas = $('view');
  const aspect = window.innerWidth / window.innerHeight;

  const scene = makeScene();
  const camera = makeCamera(aspect);
  const renderer = makeRenderer(canvas);
  const lighting = new Lighting(scene);
  scene.add(makeSky(lighting.moonDir));

  const { composer, bloom } = makeComposer(renderer, scene, camera);
  const clampPass = makeClampPass();
  composer.addPass(clampPass);

  // ---- terrain, then placement -----------------------------------------
  say('reading terrain.json');
  let terrain = null;
  try {
    terrain = await Terrain.load('data/terrain.json');
  } catch (err) {
    console.warn('[nightfall] no terrain.json — instanced kits cannot be seated', err);
  }

  // §8.6 step 5: prefer the frozen placement file; fall back to generating it
  // from the same seeded code so the page still works before the bake step has
  // been run. Either way the result is identical from a cold load.
  let placement = {}, placementSource = 'none';
  if (terrain) {
    try {
      const res = await fetch('data/placement.json');
      if (res.ok) {
        const file = await res.json();
        if (file.seed === SEED) { placement = file.pieces; placementSource = 'data/placement.json (frozen)'; }
        else console.warn('[nightfall] placement.json seed mismatch, regenerating');
      }
    } catch { /* fall through */ }
    if (placementSource === 'none') {
      placement = placeAll(terrain, KITS);
      placementSource = 'generated in-page from place.js (seed ' + SEED.toString(16) + ')';
    }
  }

  // ---- assets ----------------------------------------------------------
  const assets = new SceneAssets();
  say('loading the castle (19 MB of baked maps)');
  await assets.loadScenery(SCENERY, ASSET_BASE);
  say('loading fires, lamps and lit openings');
  await assets.loadFixtures(FIXTURES, ASSET_BASE, terrain);
  say('laying the ground mist');
  await assets.loadFixtures(MIST, ASSET_BASE, terrain);
  say('placing the tree and scrub kit');
  await assets.loadKits(KITS, ASSET_BASE, placement);

  const groundMissing = SCENERY
    .filter((e) => e.id.startsWith('ground_'))
    .every((e) => assets.missing.some((m) => m.id === e.id));
  if (groundMissing) {
    console.warn('[nightfall] no ground_*.glb — placing a TEMPORARY ground at the §6.1 levels');
    assets.addTemporaryGround();
  }

  scene.add(assets.root);
  lighting.bind(assets.emissiveByPlacement);

  // §8.5: renderOrder on the translucent things, back-to-front from the hero
  // camera, and then frozen. The camera barely moves, so sorting once is right
  // and sorting every frame is waste.
  assets.transparent.forEach((m) => { m.depthWrite = false; });
  const translucent = [];
  assets.root.traverse((o) => {
    if (o.isMesh && o.material && !Array.isArray(o.material) && o.material.transparent) translucent.push(o);
  });
  translucent
    .map((o) => ({ o, d: o.getWorldPosition(new THREE.Vector3()).distanceTo(HERO.position) }))
    .sort((a, b) => b.d - a.d)
    .forEach(({ o }, i) => { o.renderOrder = 10 + i; });

  // ---- report ----------------------------------------------------------
  const report = {
    triangles: Math.round(assets.triangles),
    loaded: assets.loaded.length,
    missing: assets.missing,
    instancedMeshes: assets.instancedMeshes,
    placementSource,
    temporaryGround: !!assets.temporaryGround,
    three: THREE.REVISION,
  };
  console.log('[nightfall] scene report', report);
  if (assets.missing.length) {
    console.warn('[nightfall] not loaded:', assets.missing.map((m) => m.file).join(', '));
  }

  buildNotes(report, translucent.length);
  $('loading').classList.add('gone');

  // ---- camera and loop -------------------------------------------------
  const rig = new CameraRig(camera, renderer.domElement, { intro: true });
  rig.onCancel = () => $('hint').classList.add('faded');

  let firstFrameDone = false;
  const clock = new THREE.Timer();   // THREE.Clock is deprecated in r185
  let acc = 0, frames = 0, fps = 0, ms = 0;

  // Each composer pass resets renderer.info, so left alone the HUD reports the
  // OutputPass's single full-screen quad. Reset once per frame instead and the
  // counters accumulate across every pass, which is the real per-frame cost.
  renderer.info.autoReset = false;

  function frame() {
    requestAnimationFrame(frame);
    renderer.info.reset();
    clock.update();
    const dt = Math.min(clock.getDelta(), 0.1);
    const t = clock.getElapsed();

    rig.update(dt);
    lighting.update(t);

    const t0 = performance.now();
    composer.render(dt);
    ms = ms * 0.9 + (performance.now() - t0) * 0.1;

    // §8.4: nothing in the scene moves and the flickering point lights cast no
    // shadows, so the shadow map is drawn once and then frozen. Free win.
    if (!firstFrameDone) {
      renderer.shadowMap.autoUpdate = false;
      firstFrameDone = true;
    }

    frames++; acc += dt;
    if (acc >= 0.5) { fps = frames / acc; frames = 0; acc = 0; updateHud(); }
  }

  function updateHud() {
    const info = renderer.info.render;
    $('hud-body').innerHTML = [
      `${fps.toFixed(0)} fps &nbsp; ${ms.toFixed(1)} ms`,
      `${info.triangles.toLocaleString()} tris drawn`,
      `${info.calls} draw calls`,
      `${report.triangles.toLocaleString()} tris in scene`,
      `three r${THREE.REVISION}`,
    ].join('<br>');
  }

  window.addEventListener('resize', () => {
    const a = window.innerWidth / window.innerHeight;
    rig.resize(a);
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
  });

  // ---- keys ------------------------------------------------------------
  window.addEventListener('keydown', (e) => {
    const k = e.key.toLowerCase();
    if (k === 'r') rig.reset();
    if (k === ' ') { e.preventDefault(); rig.reset(); }
    if (k === 'l') {
      clampPass.enabled = !clampPass.enabled;
      $('clamp-state').textContent = clampPass.enabled ? 'on' : 'off';
      document.body.classList.toggle('clamping', clampPass.enabled);
    }
    if (k === 'h') $('hud').classList.toggle('gone');
    if (k === 'n') $('notes').classList.toggle('open');
    if (k === 'c') runAudit();
  });

  $('btn-hero').addEventListener('click', () => rig.reset());
  $('btn-notes').addEventListener('click', () => $('notes').classList.toggle('open'));
  $('btn-close-notes').addEventListener('click', () => $('notes').classList.remove('open'));
  $('btn-clamp').addEventListener('click', () => {
    clampPass.enabled = !clampPass.enabled;
    $('clamp-state').textContent = clampPass.enabled ? 'on' : 'off';
    document.body.classList.toggle('clamping', clampPass.enabled);
  });
  $('btn-audit').addEventListener('click', runAudit);

  function runAudit() {
    const wasOn = clampPass.enabled;
    clampPass.enabled = false;
    composer.render(0);
    const a = auditFrame(renderer);
    clampPass.enabled = wasOn;
    const line = a.pass
      ? `clean — no cool surface over 0.45 (${a.coolPixels} isolated sparkle${a.coolPixels === 1 ? '' : 's'}); `
        + `fires cover ${a.warmPct.toFixed(2)}% of frame; brightest ${a.brightest.toFixed(3)}`
      : `FAIL — ${a.coolClustered} clustered cool pixels over 0.45 of ${a.coolPixels} total `
        + `(${a.coolPct.toFixed(3)}% of frame); brightest ${a.brightest.toFixed(3)}`;
    $('audit-out').textContent = line;
    $('audit-out').className = a.pass ? 'ok' : 'bad';
    console.log('[nightfall] §2 cool-value audit', a);
  }

  // Expose just enough for a screenshot script and for poking at it in the
  // console. Not used by the page itself.
  window.nightfall = { scene, camera, renderer, composer, rig, lighting, assets, report, runAudit, clampPass, THREE };
  frame();
}

// -------------------------------------------------------- the notes panel
// Built from manifest.js, so the page cannot claim a provenance the repo does
// not have. If a brief is missing, the panel says the brief is missing.

function sourceLinks(key) {
  const s = SOURCES[key];
  if (!s) return '<span class="warn">no source recorded</span>';
  const bits = [`<a href="${repoUrl(s.script)}">${s.script.split('/').pop()}</a>`];
  for (const [label, path] of (s.extra || [])) bits.push(`<a href="${repoUrl(path)}">${label}</a>`);
  bits.push(s.brief
    ? `<a href="${repoUrl(s.brief)}">brief</a>`
    : `<span class="warn" title="${s.briefNote || ''}">brief not committed</span>`);
  return bits.join(' &middot; ');
}

function buildNotes(report, translucentCount) {
  const missingIds = new Set(report.missing.map((m) => m.id));
  const groups = new Map();
  for (const e of [...SCENERY, ...FIXTURES, ...MIST, ...KITS]) {
    if (!groups.has(e.group)) groups.set(e.group, []);
    groups.get(e.group).push(e);
  }

  let html = '';
  for (const [group, entries] of groups) {
    html += `<h3>${group}</h3><table class="assets">`;
    for (const e of entries) {
      const gone = missingIds.has(e.id);
      const count = e.count ? `&times;${e.count}` : (e.at && e.at.length > 1 ? `&times;${e.at.length}` : '');
      html += `<tr class="${gone ? 'gone-row' : ''}">
        <td class="a-id">${e.id} <span class="a-count">${count}</span></td>
        <td class="a-src">${sourceLinks(e.source)}</td>
      </tr>`;
      if (e.note) html += `<tr class="${gone ? 'gone-row' : ''}"><td colspan="2" class="a-note">${e.note}</td></tr>`;
      if (gone) html += `<tr><td colspan="2" class="a-note warn">not loaded — ${e.file} is not built yet</td></tr>`;
    }
    html += '</table>';
  }
  $('notes-assets').innerHTML = html;

  $('notes-hand').innerHTML = HAND_WRITTEN
    .map(([what, how]) => `<li><b>${what}.</b> ${how}</li>`).join('');

  $('notes-pending').innerHTML = PENDING.map((p) => `
    <li><b>${p.group}</b> — <code>${p.script}</code><br>
    <span class="a-note">${p.pieces}</span>
    ${p.affects ? `<br><span class="a-note warn">${p.affects}</span>` : ''}</li>`).join('');

  $('notes-stats').innerHTML = [
    `${report.triangles.toLocaleString()} triangles in the loaded world`,
    `${report.instancedMeshes} InstancedMeshes carrying the tree and scrub kit`,
    `${translucentCount} translucent objects, renderOrder frozen back-to-front from the hero camera`,
    `placement: ${report.placementSource}`,
    `bloom ${BLOOM.strength} / ${BLOOM.radius} / threshold ${BLOOM.threshold}, before ACES at exposure ${EXPOSURE}`,
    `three.js r${report.three}, vendored — this page fetches nothing from a CDN`,
    report.temporaryGround ? '<span class="warn">TEMPORARY ground plane in use — the real ground is not built</span>' : '',
  ].filter(Boolean).map((s) => `<li>${s}</li>`).join('');

  if (report.missing.length) {
    $('missing-banner').innerHTML =
      `${report.missing.length} asset${report.missing.length > 1 ? 's' : ''} not built yet` +
      (report.temporaryGround ? ' &middot; temporary ground in use' : '');
    $('missing-banner').classList.add('show');
  }
}

boot().catch((err) => {
  console.error(err);
  say(`failed: ${err.message}`);
  $('loading').classList.add('failed');
});
