// The palette from ART-DIRECTION.md §2, as data.
//
// Two families and a hard rule: `fire-core` is the only thing in the scene
// allowed to be bright, and everything cool is capped at the value of
// `stone-lit` (0x6A = 0.42). The debug clamp in debug.js checks that.

export const COOL = {
  skyZenith:  0x080D18,
  skyHorizon: 0x1C2C42,
  fog:        0x16243A,
  moonCold:   0xAFC8EC,
  stoneLit:   0x6A7787,
  stoneDark:  0x151D29,
  turfNight:  0x1A2419,
  earthWet:   0x20211C,
  timberNight:0x100D0A,
  mistPale:   0x5E7488,
  waterBlack: 0x0A121A,
};

export const WARM = {
  fireCore:  0xFFD08A,
  fireFlame: 0xFF9A3C,
  fireSpill: 0xFF7A2E,
  tallow:    0xFFBE6A,
  ember:     0xB23A16,
};

// Hemisphere fill, §3.2.
export const AMBIENT = { sky: 0x2A3E58, ground: 0x0D1319 };

// The value ceiling for anything that is not a fire, §2 "The rule".
export const COOL_LUMA_CEILING = 0.45;
