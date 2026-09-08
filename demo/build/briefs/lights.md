# Brief — asset groups 3 and 4: everything that glows

Written before `build_lights.py`. Committed verbatim: this is the text the
model was built from.

Both groups are emissive and therefore never go through `skin_*.py`. Every
material is a flat `lib.material(..., emissive=1.0)`; the real
`emissiveIntensity` is set by name in `docs/js/materials.js` per ART-DIRECTION
§3.6.

---

## Group 3 — fire, lamp and plume kit

A household fire kit for a half-ruined Welsh march castle at ten at night in
late October, seen from ninety metres out on a low, almost level camera against
a sky the colour of `#080D18` — these seven pieces are the only bright things in
a picture that is otherwise one black mass, so they carry the whole image and
must read at twenty to forty pixels tall. Build a `brazier` 0.62 m across and
1.10 m to the tip of its flames — a splayed three-legged wrought-iron stand, a
shallow openwork fire-basket of six vertical bars between a foot ring and a
heavy rim hoop, a low glowing bed of coals inside it in `fire-core #FFD08A` with
three darker `ember #B23A16` lumps sitting in it, and five overlapping tapered
four-sided flame shards in `fire-flame #FF9A3C` standing up out of the bed at
different heights and leans; a `bonfire` 2.6 m across and 1.40 m tall — a ring
of nine set limestone blocks, six criss-crossed burning logs, a wide low
`fire-core` bed with embers, and six larger flame shards; a `lantern` 0.22 ×
0.22 × 0.34 m — an iron horn lantern, meaning a chunky square frame of four
corner uprights on a base plate with a pyramidal vented cap and a carrying bail
on top, and four cloudy horn panes in `tallow #FFBE6A` set inside the frame, not
a glass box and nothing modern; a `cresset` 0.34 m across and 0.50 m tall — a
wall bracket of a back plate, an arm and a diagonal stay carrying an open
lathe-turned iron bowl of burning pitch, `fire-flame` shards above a `fire-core`
bed; a `lamp_post` 0.16 × 0.16 × 2.4 m — a chamfered squared oak post on a
packing stone, with an iron strap band and a short hook arm at the head for a
lantern to hang from, and no emissive part at all; and two smoke plumes,
`plume_tall` 2.5 m across and 13 m high for the keep chimney and `plume_low`
1.8 m across and 8 m high for the hall ridge and the oven flue, each a
faceted eight-sided section swept up a path that rises nearly vertically for the
first two thirds, then bends about 30° from vertical and drifts north-east on
the south-west wind, its section widening from a chimney-sized 0.5 m to the full
width and flattening into an ellipse at the top as the cold air caps it, in
`mist-pale #5E7488` at alpha 0.13 with no emission whatsoever. Everything that
is not fire is near-black — `timber-night #100D0A` ironwork and timber,
`stone-dark #151D29` set stones — because it will be lit by the point light
beside it and by nothing else. The whole kit is about 4 100 triangles. It must
not be a torch on every wall, the flames must not be modelled flame *shapes*,
the fire must read as two distinct brightnesses (bed hotter than shards) rather
than one flat orange sticker, and the plumes must not come out opaque.

## Group 4 — lit-opening plates and shutters

Small emissive plates that sit 25 mm proud of the castle's existing near-black
opening slabs so that six of about forty openings become rooms with people in
them, plus the timber shutter that is the whole trick. Every plate is a flat
box, thin in local Y, emitting toward local −Y, centred on local X, sitting on
z = 0, so placing one is a position and a yaw: `pane_window` 1.40 wide × 2.10
tall for the two lit keep top-storey windows, `pane_hall` 1.05 × 1.40 for two of
the hall's five east windows, `pane_loop` 0.28 × 1.45 for the single lit arrow
loop on the east gate drum, `pane_lancet` 1.20 × 2.40 for the chapel west
window, `pane_passage` 1.90 × 2.60 set four metres back inside the gate passage
so the gateway reads as a way through rather than a black slot, and
`oven_mouth`, a small round-headed 0.55 × 0.70 arch in `ember #B23A16` for the
bake-house oven front — all of them `tallow #FFBE6A` except the oven. Every one
matches the face dimensions of the castle slab it covers, taken from
`build_castle.py` and not guessed. The `shutter` is 0.72 wide × 2.10 tall × 0.05
thick oak: four vertical boards with a visible gap between them, two horizontal
ledges across the back, and two iron strap hinges running out from the hinge
edge, authored flat in the wall plane with its origin on the hinge line so the
scene can swing each of the two of them to a different angle across a keep pane.
About 250 triangles for the lot. It must not be a grid — no two lit openings on
one elevation at one height — and a bare lit rectangle with no shutter across it
reads as a decal, which is the failure this group exists to avoid.
