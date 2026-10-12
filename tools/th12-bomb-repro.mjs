// Reproduce the browser's "a bomb ends the stage" in the node core, where the economy and the battle error are
// readable per frame. The soak tops lives back up to 8 on every frame before it runs its policy, so its six-stage
// progression is not evidence that a real playthrough survives; this runs the same policy with and without that
// top-up, and with the bomb held for one frame (what the soak sends) against seven (what a 120 ms key hold sends).
//
//   TH12_DATA=<path to th12.dat> node tools/th12-bomb-repro.mjs
//
// Run it from `runtimes/th12/th12_web` so the test helpers resolve the built core, or point TH11_CORE_TEST_FILE
// at `artifacts/cpp/game-core-test.wasm` yourself. The game data is not distributed, which is why this is a
// diagnostic and not a gate.
import {readFileSync} from 'node:fs';
import {core,memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const c = await core();
const raw = readFileSync(path);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const source = c.resources_create();
if (c.resources_open(source, data, raw.length) !== 1) throw Error('resources_open failed: ' + path);

const error = s => {
  const b = memory(c, c.game_session_error(s), 512);
  return new TextDecoder().decode(b.subarray(0, b.indexOf(0)));
};

function run({label, topUp, bombEvery, bombHold, frames}) {
  const s = c.game_session_create(), render = c.comp_create();
  if (c.game_session_begin(s, source, 1, 0, 0, 1, 0) !== 1) throw Error('begin: ' + error(s));
  let bombTicks = 0;
  for (let f = 0; f < frames; ++f) {
    // Any of these calls can grow wasm memory, which detaches a DataView created before it, so the economy is
    // read through a view made immediately before each use rather than one kept across the frame.
    const held = 1 | (bombEvery && f % bombEvery < bombHold ? 2 : 0);
    if (bombEvery && f % bombEvery < bombHold) ++bombTicks;
    if (topUp) {
      const economy = c.battle_data(s, 0);
      new DataView(c.memory.buffer).setInt32(economy + 16, Math.max(new DataView(c.memory.buffer).getInt32(economy + 16, true), 8), true);
    }
    if (c.game_session_update(s, held, 0, 0, 0, 0, 0) !== 1) { console.log(`  ${label}: update failed at ${f}: ${error(s)}`); return; }
    if (c.game_session_render(s, render) !== 1) { console.log(`  ${label}: render failed at ${f}`); return; }
    const view = new DataView(c.memory.buffer), economy = c.battle_data(s, 0);
    const phase = c.game_session_value(s, 0);
    if (phase !== 1) { console.log(`  ${label}: LEFT THE STAGE at frame ${f}, phase ${phase}`); return; }
    if (f % 600 === 0) {
      console.log(`   ${label} f=${String(f).padStart(5)} phase=${phase} lives=${view.getInt32(economy + 16, true)} power=${view.getInt32(economy + 4, true)} bombPresses=${bombTicks}`);
    }
  }
  console.log(`  ${label}: still in the stage after ${frames} frames`);
}

console.log('=== A: soak policy, lives topped to 8 every frame ===');
run({label: 'soak', topUp: true, bombEvery: 180, bombHold: 1, frames: 3000});
console.log('=== B: same policy, no top-up ===');
run({label: 'no-topup', topUp: false, bombEvery: 180, bombHold: 1, frames: 3000});
console.log('=== C: no top-up, bomb held 7 frames every 180 ===');
run({label: 'hold7', topUp: false, bombEvery: 180, bombHold: 7, frames: 3000});
console.log('=== D: no top-up, no bombs ===');
run({label: 'nobomb', topUp: false, bombEvery: 0, bombHold: 0, frames: 3000});
