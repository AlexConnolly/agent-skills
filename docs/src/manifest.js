// The manifest is the spine of this page.
//
// It is the single list that says, for every object in the world: which .glb it
// is, where it goes, which build script generated it, and which brief that
// script was written from. The loader reads it to build the scene and the
// credits panel reads it to print the claim, so the page cannot advertise a
// provenance it does not actually have — if a link here is wrong or missing,
// it is wrong or missing on the page too.
//
// Coordinates are Three.js metres per ART-DIRECTION §0.2: +X east, +Y up,
// +Z south, ward floor at y = 0.

export const REPO = 'https://github.com/AlexConnolly/agent-skills';
export const REF = 'main';

export const repoUrl = (p) => `${REPO}/blob/${REF}/${p}`;

// Every build script that produced something in this scene, with the brief it
// was written from. `brief: null` means the brief has not been committed yet
// and the page says so rather than pretending otherwise.
export const SOURCES = {
  castle: {
    label: 'build_castle.py + skin_castle.py',
    script: 'plugins/blender-model/skills/blender-model/examples/build_castle.py',
    extra: [
      ['skin_castle.py', 'plugins/blender-texture/skills/blender-texture/examples/skin_castle.py'],
    ],
    brief: null,
    briefNote: 'worked example of the two skills chaining; brief not yet committed',
  },
  ground: {
    label: 'build_ground.py',
    script: 'demo/build/build_ground.py',
    brief: 'demo/build/briefs/ground.md',
  },
  mist: {
    label: 'build_mist.py',
    script: 'demo/build/build_mist.py',
    brief: 'demo/build/briefs/mist.md',
  },
  trees: {
    label: 'build_trees.py',
    script: 'demo/build/build_trees.py',
    brief: 'demo/build/briefs/trees.md',
  },
  lights: {
    label: 'build_lights.py',
    script: 'demo/build/build_lights.py',
    brief: 'demo/build/briefs/lights.md',
  },
};

const D = Math.PI / 180;

// ---------------------------------------------------------------- the castle
// and the ground: single meshes at a fixed transform.

export const SCENERY = [
  {
    id: 'castle', file: 'castle.glb', source: 'castle', group: 'The castle',
    at: [{ pos: [0, 0, 0] }],
    castShadow: true, receiveShadow: true,
    note: '71 m across, baked at 14.7 texels/m. The only asset in the scene carrying a baked map.',
  },
  {
    id: 'ground_platform', file: 'ground_platform.glb', source: 'ground', group: 'The ground',
    at: [{ pos: [0, 0, 0] }],
    castShadow: true, receiveShadow: true,
    note: 'The limestone shoulder the castle is cut from. The ditch is a negative feature of this same mesh, not a separate object. Vertex-coloured, no baked map.',
  },
  {
    id: 'ground_outfield', file: 'ground_outfield.glb', source: 'ground', group: 'The ground',
    at: [{ pos: [0, 0, 0] }],
    castShadow: false, receiveShadow: true,
    note: '400 × 400 m heightfield. Carries the drover’s knoll the camera stands on and the hollow the mist pools in.',
  },
  {
    id: 'ground_ridge', file: 'ground_ridge.glb', source: 'ground', group: 'The ground',
    at: [{ pos: [0, 0, 0] }],
    castShadow: false, receiveShadow: true,
    note: 'The distant swell that keeps the far walls off a dead-flat horizon.',
  },
];

// ------------------------------------------------------- fires, lamps, panes
// Fixed transforms, positions straight out of ART-DIRECTION §3.4 / §5.

export const FIXTURES = [
  {
    id: 'bonfire', file: 'bonfire.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [{ pos: [24.0, 0, -2.0], rotY: 18 * D }],
    note: 'The picture. Sits just inside the breach so its light escapes through the gap.',
  },
  {
    id: 'brazier', file: 'brazier.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [
      { pos: [6.0, 0, 26.2], rotY: 0, tag: 'gate passage' },
      { pos: [6.0, 10.4, 22.0], rotY: 140 * D, tag: 'gate wall-walk' },
      { pos: [-19.0, 0, 6.0], rotY: 210 * D, tag: 'hall door' },
      { pos: [12.0, 0, 8.0], rotY: 70 * D, tag: 'ward' },
    ],
  },
  {
    id: 'cresset', file: 'cresset.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [
      { pos: [1.6, 6.4, 28.3], rotY: 0, tag: 'gatehouse front W' },
      { pos: [10.4, 6.4, 28.3], rotY: 0, tag: 'gatehouse front E' },
      { pos: [31.9, 11.4, 24.1], rotY: 42 * D, tag: 'SE great tower' },
      { pos: [7.5, 2.4, 25.6], rotY: 180 * D, tag: 'gate passage' },
    ],
  },
  {
    id: 'lamp_post', file: 'lamp_post.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [
      { pos: [48.0, -1.0, 24.6], rotY: 200 * D, tag: 'bridge post', dependsOn: 'ditch_bridge' },
      { pos: [3.2, 0.2, 30.6], rotY: 0, tag: 'causeway W', dependsOn: 'causeway_apron' },
      { pos: [8.8, 0.2, 30.6], rotY: 0, tag: 'causeway E', dependsOn: 'causeway_apron' },
    ],
  },
  {
    id: 'lantern', file: 'lantern.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [
      { pos: [48.0, -0.4, 24.6], rotY: 200 * D, tag: 'bridge post', dependsOn: 'ditch_bridge' },
      { pos: [3.2, 1.9, 30.6], rotY: 0, tag: 'causeway W' },
      { pos: [8.8, 1.9, 30.6], rotY: 0, tag: 'causeway E' },
      { pos: [-19.35, 2.3, 6.3], rotY: 90 * D, tag: 'hall door' },
      { pos: [1.5, 2.45, 1.0], rotY: 25 * D, tag: 'well beam' },
      { pos: [6.0, 3.3, 27.4], rotY: 0, tag: 'gate arch' },
    ],
  },
  {
    id: 'plume_tall', file: 'plume_tall.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [{ pos: [-14.9, 23.5, -9.1] }],
    note: 'Keep chimney. Rises 8–10 m, then flattens under the inversion and drifts NE, like the other two.',
  },
  {
    id: 'plume_low', file: 'plume_low.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [
      { pos: [-24.8, 8.9, 3.5], rotY: -8 * D, tag: 'hall ridge' },
      { pos: [23.6, 3.1, 16.6], rotY: 11 * D, tag: 'oven flue' },
    ],
  },
  {
    id: 'oven_mouth', file: 'oven_mouth.glb', source: 'lights', group: 'Lit-opening plates',
    at: [{ pos: [23.6, 0.45, 17.5], rotY: 0, tag: 'bake-house' }],
  },
  // Every coordinate below is read off the opening it covers in
  // build_castle.py, converted with the §0.2 table, and set 25 mm proud of that
  // opening's own outer face. The §5 group 4 coordinates are the opening
  // CENTRES; these assets have their origin at the bottom of the plate, so the
  // y here is the centre less half the height.
  {
    id: 'pane_window', file: 'pane_window.glb', source: 'lights', group: 'Lit-opening plates',
    at: [
      // build_castle.py kwin: loc (kx-5+5j, ky-KEEP_D/2-0.32, 14.5), size (1.40, 0.34, 2.10)
      { pos: [-14.5, 13.45, 1.185], rotY: 0, tag: 'keep top storey W' },
      { pos: [-4.5, 13.45, 1.185], rotY: 0, tag: 'keep top storey E' },
    ],
    note: 'Two of the keep’s three top-storey windows. The third stays cold — that is the point.',
  },
  {
    id: 'shutter', file: 'shutter.glb', source: 'lights', group: 'Lit-opening plates',
    at: [
      { pos: [-15.28, 13.45, 1.27], rotY: -34 * D, tag: 'keep W, half open' },
      { pos: [-5.28, 13.45, 1.27], rotY: -58 * D, tag: 'keep E, further open' },
    ],
    note: 'The whole trick. A bare lit rectangle is a decal; a lit rectangle with a timber shutter swung across it is a room.',
  },
  {
    id: 'pane_hall', file: 'pane_hall.glb', source: 'lights', group: 'Lit-opening plates',
    at: [
      // hall_win: loc (hall_c.x+3.92, hall_c.y-4.8+3.2i, 5.6), size (0.28, 1.05, 1.40)
      { pos: [-19.605, 4.9, 12.3], rotY: 90 * D, tag: 'hall, near end' },
      { pos: [-19.605, 4.9, 9.1], rotY: 90 * D, tag: 'hall, near end' },
    ],
  },
  {
    id: 'pane_loop', file: 'pane_loop.glb', source: 'lights', group: 'Lit-opening plates',
    // gt1_loop1: on_ring(east drum centre (11.6, 23.8), theta -pi/2+0.55, r 3.08, z 9.4)
    at: [{ pos: [13.294, 8.675, 26.568], rotY: 31.4 * D, tag: 'gate drum loop' }],
    note: 'The only lit arrow loop in the castle.',
  },
  {
    id: 'pane_lancet', file: 'pane_lancet.glb', source: 'lights', group: 'Lit-opening plates',
    // chapel_e: loc (11.4, 11.0, 3.2), size (0.30, 1.20, 2.40) — on the chapel's west face
    at: [{ pos: [11.315, 2.0, -11.0], rotY: -90 * D, tag: 'chapel west window' }],
  },
  {
    id: 'pane_passage', file: 'pane_passage.glb', source: 'lights', group: 'Lit-opening plates',
    at: [{ pos: [6.0, 0.1, 24.0], rotY: 0, tag: 'gate passage, 4 m back' }],
    note: 'Makes the gateway read as a way through rather than a black slot.',
  },
];

// ------------------------------------------------------ ground mist, §7
//
// Not instanced: twenty transparent objects need individual renderOrder, which
// main.js assigns back-to-front from the hero camera and then freezes.
//
// Every sheet is seated on the sampled terrain (`seat: true`) rather than given
// a written-down y, so it follows build_ground.py instead of drifting from it.
// Every instance gets a different yaw, a different plan scale and a different
// height scale, and the §7 ceiling holds throughout: base lift plus scaled
// height never reaches 2.4 m above the local ground, and nothing comes near the
// camera's own eye at y = −1.0.
export const MIST = [
  {
    id: 'mist_sheet_a', file: 'mist_sheet_a.glb', source: 'mist', group: 'Ground mist sheets',
    // The hollow. build_ground.py put its floor at (−10, −92) rather than the
    // NE corner §6.3 names, so the sheets follow the ground that exists.
    at: [
      { pos: [-18, 0, -86], rotY: 12 * D, scale: [1.00, 1.30, 1.00], seat: true, lift: 0.15 },
      { pos: [14, 0, -96], rotY: 48 * D, scale: [0.85, 1.60, 0.95], seat: true, lift: 0.32 },
      { pos: [-34, 0, -100], rotY: 118 * D, scale: [1.10, 1.00, 1.15], seat: true, lift: 0.05 },
      { pos: [4, 0, -74], rotY: 205 * D, scale: [0.95, 1.45, 0.90], seat: true, lift: 0.28 },
      { pos: [-26, 0, -118], rotY: 155 * D, scale: [1.05, 1.20, 1.05], seat: true, lift: 0.20 },
    ],
    note: 'The hollow behind the breach, where cold air sinks and the ground goes black.',
  },
  {
    id: 'mist_sheet_b', file: 'mist_sheet_b.glb', source: 'mist', group: 'Ground mist sheets',
    // The ditch, following the ring. Floor is −6.8 and the water surface −6.0,
    // so the lift puts every sheet's underside just above the standing water.
    at: [
      { pos: [61.8, 0, -16.6], rotY: -15 * D, scale: [1.00, 1.20, 0.80], seat: true, lift: 0.95 },
      { pos: [58.0, 0, 15.5], rotY: 20 * D, scale: [0.90, 1.00, 0.95], seat: true, lift: 1.05 },
      { pos: [43.1, 0, 43.1], rotY: 48 * D, scale: [1.05, 1.30, 0.85], seat: true, lift: 0.85 },
      { pos: [15.5, 0, 58.0], rotY: 76 * D, scale: [0.95, 1.10, 1.00], seat: true, lift: 1.15 },
      { pos: [46.0, 0, -46.0], rotY: -44 * D, scale: [1.00, 0.90, 1.10], seat: true, lift: 0.90 },
    ],
  },
  {
    id: 'mist_sheet_c', file: 'mist_sheet_c.glb', source: 'mist', group: 'Ground mist sheets',
    at: [
      { pos: [120, 0, 30], rotY: 25 * D, scale: [1.20, 1.40, 1.00], seat: true, lift: 0.20 },
      { pos: [60, 0, 120], rotY: 70 * D, scale: [1.00, 1.10, 1.15], seat: true, lift: 0.40 },
      { pos: [-70, 0, 130], rotY: 115 * D, scale: [1.10, 1.50, 0.90], seat: true, lift: 0.10 },
      { pos: [130, 0, -60], rotY: -25 * D, scale: [0.95, 1.20, 1.05], seat: true, lift: 0.30 },
    ],
  },
  {
    id: 'mist_wisp', file: 'mist_wisp.glb', source: 'mist', group: 'Ground mist sheets',
    // The near foreground, 16-30 m out, all of it well under the lens.
    at: [
      { pos: [60.6, 0, 38.4], rotY: 35 * D, scale: [1.20, 1.30, 1.10], seat: true, lift: 0.08 },
      { pos: [62.8, 0, 27.8], rotY: 105 * D, scale: [1.00, 0.90, 1.25], seat: true, lift: 0.16 },
      { pos: [55.6, 0, 42.3], rotY: 160 * D, scale: [1.35, 1.10, 0.95], seat: true, lift: 0.05 },
      { pos: [59.7, 0, 19.8], rotY: 20 * D, scale: [1.10, 1.50, 1.20], seat: true, lift: 0.22 },
      { pos: [71.7, 0, 25.3], rotY: 78 * D, scale: [0.90, 0.80, 1.05], seat: true, lift: 0.12 },
      { pos: [53.7, 0, 43.4], rotY: 130 * D, scale: [1.25, 1.20, 1.00], seat: true, lift: 0.18 },
    ],
    note: 'Thin, low and close. These are what stop the bottom third being one flat black wedge.',
  },
];

// ----------------------------------------------------------------- the kits
// One InstancedMesh per piece. `place` names the rule set in place.js.

export const KITS = [
  { id: 'tree_oak_bare', file: 'tree_oak_bare.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 34, place: 'oak', castShadow: true,
    note: 'Field boundaries, ditch outer lip and both frame edges. Two are placed by hand as repoussoir.' },
  { id: 'tree_ash_bare', file: 'tree_ash_bare.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 16, place: 'ash', castShadow: true },
  { id: 'tree_hawthorn', file: 'tree_hawthorn.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 26, place: 'hawthorn', castShadow: true,
    note: 'Leans away from the south-west, like everything else in the scene that leans.' },
  { id: 'tree_yew', file: 'tree_yew.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 10, place: 'yew', castShadow: true },
  { id: 'tree_pine', file: 'tree_pine.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 20, place: 'pine', castShadow: false,
    note: 'One stand only, on the ridge behind the castle.' },
  { id: 'scrub_gorse', file: 'scrub_gorse.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 70, place: 'gorse', castShadow: true },
  { id: 'deadfall', file: 'deadfall.glb', source: 'trees', group: 'Tree and scrub kit',
    count: 8, place: 'deadfall', castShadow: true },
];

// ------------------------------------------------- what is not built yet
// Named here so the page can be honest about the hole rather than quietly
// rendering a smaller world. main.js prints this list to the console and the
// notes panel shows it.

export const PENDING = [
  { group: 'Group 2 — rock and outcrop kit', script: 'demo/build/build_rocks.py',
    pieces: 'rock_outcrop_a/b, boulder_a/b, scree_run' },
  { group: 'Group 5 — the crossing', script: 'demo/build/build_crossing.py',
    pieces: 'ditch_bridge, causeway_apron, ditch_water, rut_pool',
    affects: 'The bridge lantern and its post are placed at the deck level they will sit at (y = −1.0); until the bridge lands they stand over the ditch on nothing.' },
  { group: 'Group 6 — track and field edges', script: 'demo/build/build_edges.py',
    pieces: 'track_ribbon, wall_mod_a/b, hurdle, field_gate',
    affects: 'The track polyline in place.js is already frozen and trees are rejected within 5.2 m of it, so the ribbon will land in cleared ground.' },
  { group: 'Group 8 — outfield clutter', script: 'demo/build/build_clutter.py',
    pieces: 'wayside_cross, carriers_cart, woodstack, tether_post, hay_heap',
    affects: 'The wayside cross is the closest object in the hero frame and the one thing that sets scale for everything behind it. Its absence is the biggest hole in the picture.' },
];

// What on this page is scene code rather than a generated object. §8.3 asks for
// this to be said out loud, so it is data and the panel cannot drift from it.
export const HAND_WRITTEN = [
  ['The sky', 'A ~40-line GLSL gradient with a moon glow lobe and a hashed star field. src/scene.js'],
  ['The lighting', 'One directional moon, one hemisphere fill, seven point lights and their flicker. src/lights.js'],
  ['The camera', 'Hero framing, the 24 s push and the fenced orbit controls. src/camera.js'],
  ['Placement', 'Seeded PRNG and the rejection rules that decide where instances land. src/place.js'],
  ['Material tune-up', 'Emissive intensities and transparency, set by material name on load. src/materials.js'],
  ['This page', 'Plain ES modules, no bundler, three.js vendored. src/*.js'],
];
