// Can stage one be finished at all? A replay desyncs, and a policy cannot dodge, so this takes the third route:
// hold the shot down, keep the player invincible, and watch the stage's own progress. It answers whether the boss
// can be defeated and the stage-completion chain runs - which is a different question from whether a recording
// reproduces - by reporting the stage, the live enemy count and every stage transition.
//
//   TH12_DATA=<path to th12.dat> node tools/th12-stage-clear.mjs [stage] [frames]
//
// Run it from `runtimes/th12/th12_web` so the helpers resolve the built core.
import {readFileSync} from 'node:fs';
import {core,memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const stage = Number(process.argv[2] ?? 1);
const frames = Number(process.argv[3] ?? 24000);
const c = await core();
const raw = readFileSync(path);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const source = c.resources_create();
if (c.resources_open(source, data, raw.length) !== 1) throw Error('resources_open failed: ' + path);
const text = p => {
  const b = memory(c, p, 512), end = b.indexOf(0);
  return new TextDecoder().decode(b.subarray(0, end < 0 ? 512 : end));
};

const s = c.game_session_create(), render = c.comp_create();
if (c.game_session_begin(s, source, stage, 0, 0, 1, 0) !== 1) throw Error('begin: ' + text(c.game_session_error(s)));
let lastStage = stage;
for (let f = 0; f < frames; ++f) {
  c.game_session_invincibility(s, 600);
  // Shoot always, and nudge left and right so the shot is not parked under one column. The point is not to dodge
  // but to keep hitting whatever is on screen.
  const held = 1 | (f % 900 < 450 ? 64 : 128);
  if (c.game_session_update(s, held, 0, 0, 0, 0, 0) !== 1) {
    console.log(`  update failed at ${f}: ${text(c.game_session_error(s))}`);
    process.exit(1);
  }
  if (c.game_session_render(s, render) !== 1) { console.log(`  render failed at ${f}`); process.exit(1); }
  const view = new DataView(c.memory.buffer), economy = c.battle_data(s, 0);
  const phase = c.game_session_value(s, 0), st = c.game_session_value(s, 2);
  if (f % 600 === 0 || st !== lastStage) {
    console.log(`   f=${String(f).padStart(5)} phase=${phase} stage=${st} frame=${c.game_session_value(s, 1)} ` +
      `enemies=${c.game_session_value(s, 7)} bullets=${c.game_session_value(s, 8)} ` +
      `lives=${view.getInt32(economy + 16, true)} power=${view.getInt32(economy + 4, true)} ` +
      `damage=${c.game_session_damage_total(s)} bossHp=${c.game_session_boss_health(s, 0)}/${c.game_session_boss_health(s, 1)} ` +
      `script=${c.game_session_stage_script_probe(s, 0)} scriptFrame=${c.game_session_stage_script_probe(s, 2)} ` +
      `instances=${c.game_session_stage_script_probe(s, 9)} objects=${c.game_session_stage_script_probe(s, 10)} ` +
      `e0flags=${c.game_session_enemy_probe(s, 0, 1).toString(16)} e0inst=${c.game_session_enemy_probe(s, 0, 5)} ` +
      `e1flags=${c.game_session_enemy_probe(s, 1, 1).toString(16)} ` +
      `battle=${c.game_session_value(s, 5)} player=${c.game_session_value(s, 6)}`);
  }
  if (st !== lastStage) { console.log(`  STAGE CHANGED ${lastStage} -> ${st} at frame ${f}`); lastStage = st; }
  if (phase !== 1) { console.log(`  left the stage at frame ${f}, phase ${phase}`); break; }
}
console.log(`  final stage ${lastStage}`);
