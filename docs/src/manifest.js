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
  rocks: {
    label: 'build_rocks.py',
    script: 'demo/build/build_rocks.py',
    brief: 'demo/build/briefs/rocks.md',
  },
  crossing: {
    label: 'build_crossing.py',
    script: 'demo/build/build_crossing.py',
    extra: [['route.py', 'demo/build/route.py']],
    brief: 'demo/build/briefs/crossing.md',
  },
  track: {
    label: 'build_track.py',
    script: 'demo/build/build_track.py',
    extra: [['route.py', 'demo/build/route.py']],
    brief: 'demo/build/briefs/track.md',
  },
  clutter: {
    label: 'build_clutter.py',
    script: 'demo/build/build_clutter.py',
    brief: 'demo/build/briefs/clutter.md',
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

  // World-authored. These four are swept along the road and the ditch ring in
  // build_crossing.py and build_track.py from the shared route.py, so their
  // vertices are already in world coordinates: they load at the origin and are
  // not placed. Moving one would take it off the road it was cut to follow.
  {
    id: 'track_ribbon', file: 'track_ribbon.glb', source: 'track', group: 'The crossing and the road',
    at: [{ pos: [0, 0, 0] }],
    castShadow: false, receiveShadow: true,
    note: '155 m of road swept from route.py, with two rut depressions. Roughness 0.35 against the field’s 0.9 — the sheen is what makes it read as a ribbon leading into the frame.',
  },
  {
    id: 'ditch_bridge', file: 'ditch_bridge.glb', source: 'crossing', group: 'The crossing and the road',
    at: [{ pos: [0, 0, 0] }],
    castShadow: true, receiveShadow: true,
    note: 'Oak trestles, three bays, one plank missing, a handrail on one side only. Deck at y = −2.95, not §6.1’s −1.0: a deck level with the lens renders as a zero-height line and the road cannot climb to it.',
  },
  {
    id: 'causeway_apron', file: 'causeway_apron.glb', source: 'crossing', group: 'The crossing and the road',
    at: [{ pos: [0, 0, 0] }],
    castShadow: true, receiveShadow: true,
  },
  {
    id: 'ditch_water', file: 'ditch_water.glb', source: 'crossing', group: 'The crossing and the road',
    at: [{ pos: [0, 0, 0] }],
    castShadow: false, receiveShadow: true,
    note: 'Flat, roughness 0.06, no normal map and no animation. A dead-still black ditch on a windless night is better than a shader.',
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
      { pos: [60.24, -2.95, 33.36], rotY: 208 * D, tag: 'bridge, outer handrail post' },
      { pos: [3.2, 0.2, 30.6], rotY: 0, tag: 'causeway W' },
      { pos: [8.8, 0.2, 30.6], rotY: 0, tag: 'causeway E' },
    ],
  },
  {
    id: 'lantern', file: 'lantern.glb', source: 'lights', group: 'Fire, lamp and plume kit',
    at: [
      { pos: [60.24, -1.05, 33.36], rotY: 208 * D, tag: 'bridge, outer handrail post' },
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

// ------------------------------------- the crossing's pools and the clutter
//
// Fixed placements. `seat: true` samples terrain.json for y; the rut pools
// instead carry the absolute y build_crossing.py froze for them, because they
// are cut into the ribbon's rut depressions rather than laid on the field.

export const PROPS = [
  {
    id: 'rut_pool', file: 'rut_pool.glb', source: 'crossing', group: 'The crossing and the road',
    // The nine frozen positions printed by build_crossing.py. The first three
    // sit 12-18 m out under the bridge lantern, which is the only place a
    // specular glint can actually land — the mirror angle puts the ditch's own
    // reflection 6 m outside the frame.
    at: [
      { pos: [68.31, -2.78, 37.34], tag: '12.3 m, under the lantern' },
      { pos: [66.74, -2.72, 33.73], tag: '15.3 m, under the lantern' },
      { pos: [63.31, -2.97, 33.89], tag: '18.3 m, under the lantern' },
      { pos: [45.84, -4.49, 33.30] },
      { pos: [46.13, -4.49, 32.82] },
      { pos: [48.25, -4.49, 28.56] },
      { pos: [48.41, -4.49, 28.05] },
      { pos: [38.73, -4.09, 36.97] },
      { pos: [40.75, -4.52, 37.90] },
    ],
    castShadow: false, receiveShadow: false,
    note: 'Two centimetres deep and worth more than the ditch, because they are 12-45 m from the lens in the bottom of frame.',
  },
  {
    id: 'wayside_cross', file: 'wayside_cross.glb', source: 'clutter', group: 'Outfield clutter',
    // §5 group 8 gives (57.8, ground, 37.2) and then says the placement
    // constraints beat the coordinate. On the ground as built they have to:
    // that point stands on the ditch counterscarp with its base 13.4 degrees
    // down, below the frame's bottom edge at -9.47, so only the head would show,
    // growing out of nothing. build_clutter.py solved for a point that keeps all
    // three constraints — on the track, head above the horizon, clear of the
    // gatehouse and the SE tower — and this is it.
    // build_clutter.py solved for (60.90, -3.22, 37.80) against §4.1's original
    // pose. This page's camera is 10 m further back (see HERO in camera.js), and
    // at that point the cross lands 33.7 % across — directly in front of the SE
    // great tower, which is the one overlap §5 group 8 forbids by name. Re-solved
    // on the same three constraints against the camera that is actually used:
    // on the track (5.7 m off the centreline, a roadside cross), head above the
    // horizon, clear of the gatehouse and the tower. Lands at 22.9 % across with
    // its head at 57 % against the castle's dark base.
    at: [{ pos: [69.09, 0, 43.63], rotY: -18 * D, seat: true }],
    castShadow: true, receiveShadow: true,
    note: 'The narrative object and the closest thing in frame, so it is what sets the scale for everything behind it. The one asset in its group carrying a baked map.',
  },
  {
    id: 'carriers_cart', file: 'carriers_cart.glb', source: 'clutter', group: 'Outfield clutter',
    at: [
      { pos: [64.6, 0, 36.4], rotY: 108 * D, rot: [0, 0, -0.22], seat: true, tag: 'tipped, by the bridge' },
      { pos: [12.6, 0, 34.4], rotY: -35 * D, seat: true, tag: 'on the berm outside the gate' },
    ],
    castShadow: true, receiveShadow: true,
  },
  {
    id: 'woodstack', file: 'woodstack.glb', source: 'clutter', group: 'Outfield clutter',
    at: [
      { pos: [2.2, 0, 33.6], rotY: 12 * D, seat: true, tag: 'outside the gate' },
      { pos: [21.0, 0.2, 15.0], rotY: 96 * D, tag: 'by the bake-house' },
      { pos: [33.2, 0, 33.0], rotY: -52 * D, seat: true, tag: 'on the berm' },
    ],
    castShadow: true, receiveShadow: true,
  },
  {
    id: 'tether_post', file: 'tether_post.glb', source: 'clutter', group: 'Outfield clutter',
    at: [
      { pos: [63.8, 0, 30.2], rotY: 20 * D, seat: true, tag: 'by the bridge' },
      { pos: [65.1, 0, 31.6], rotY: 145 * D, seat: true, tag: 'by the bridge' },
      { pos: [69.44, 0, 32.23], rotY: 70 * D, seat: true, tag: 'by the bridge' },
      { pos: [10.8, 0, 32.6], rotY: -20 * D, seat: true, tag: 'by the gate' },
      { pos: [2.6, 0, 31.4], rotY: 100 * D, seat: true, tag: 'by the gate' },
      { pos: [13.4, 0, 30.1], rotY: 200 * D, seat: true, tag: 'by the gate' },
    ],
    castShadow: true, receiveShadow: false,
  },
  {
    id: 'hay_heap', file: 'hay_heap.glb', source: 'clutter', group: 'Outfield clutter',
    at: [
      { pos: [41.72, 0, 37.85], rotY: 25 * D, seat: true },
      { pos: [73.87, 0, 29.16], rotY: 140 * D, seat: true },
      { pos: [54.39, 0, 4.26], rotY: -60 * D, seat: true },
    ],
    castShadow: true, receiveShadow: false,
  },
  {
    id: 'field_gate', file: 'field_gate.glb', source: 'track', group: 'Track and field edges',
    // In the gaps the wall runs leave where the road goes through. The origin
    // is the hinge, so the yaw swings the gate about its hanging post.
    at: [
      { pos: [78.6, 0, 39.6], rotY: 117 * D, seat: true, tag: 'shut' },
      { pos: [71.4, 0, 44.4], rotY: 44 * D, seat: true, tag: 'hanging open' },
    ],
    castShadow: true, receiveShadow: false,
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

  { id: 'rock_outcrop_a', file: 'rock_outcrop_a.glb', source: 'rocks', group: 'Rock and outcrop kit',
    count: 9, place: 'outcrop_a', castShadow: true, receiveShadow: true,
    note: 'Bedded limestone: stacked slabs with flat tops and sharp arrises, not warped spheres. Breaking through the turf on the platform batter.' },
  { id: 'rock_outcrop_b', file: 'rock_outcrop_b.glb', source: 'rocks', group: 'Rock and outcrop kit',
    count: 14, place: 'outcrop_b', castShadow: true, receiveShadow: true },
  { id: 'boulder_a', file: 'boulder_a.glb', source: 'rocks', group: 'Rock and outcrop kit',
    count: 18, place: 'boulder_a', castShadow: true, receiveShadow: true },
  { id: 'boulder_b', file: 'boulder_b.glb', source: 'rocks', group: 'Rock and outcrop kit',
    count: 16, place: 'boulder_b', castShadow: true, receiveShadow: true },
  { id: 'scree_run', file: 'scree_run.glb', source: 'rocks', group: 'Rock and outcrop kit',
    count: 5, place: 'scree', castShadow: true, receiveShadow: true },

  // These four are placed by RUNS in place.js rather than by a count: they
  // follow a boundary at a fixed pitch, and how many fit is a property of the
  // boundary, not a number to be forced.
  { id: 'wall_mod_a', file: 'wall_mod_a.glb', source: 'track', group: 'Track and field edges',
    run: true, castShadow: true, receiveShadow: true,
    note: '2.00 m pitch on a 2.04 m module with 4 cm of deliberate overlap, origin on the pitch centre, alternate modules flipped 180 degrees. All the variety is placement; a distinctive module drawn 44 times reads as a repeat.' },
  { id: 'wall_mod_b', file: 'wall_mod_b.glb', source: 'track', group: 'Track and field edges',
    run: true, castShadow: true, receiveShadow: true,
    note: 'The gapped module, used in threes as a fallen run.' },
  { id: 'hurdle', file: 'hurdle.glb', source: 'track', group: 'Track and field edges',
    run: true, castShadow: true, receiveShadow: false,
    note: 'Hazel, driven 0.14 m into the ground — the mesh extends below its origin on purpose.' },
];

// ------------------------------------------------- what is not built yet
// Named here so the page can be honest about the hole rather than quietly
// rendering a smaller world. main.js prints this list to the console and the
// notes panel shows it.

export const PENDING = [];

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
