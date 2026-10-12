// How much damage the player's shots deal per frame at a known power, so the port's kill rate is a number
// rather than an impression.
//
//   node tools/th12-damage-probe.mjs [stage] [frames] [power]
//
// Run it from `runtimes/th12/th12_web`. It holds the shot button every frame with the player invincible so the
// measurement is not disturbed by deaths, and prints the damage the port has accumulated at intervals. The stage's
// enemies come from the original's ECL data, so their maximum health is original data: dividing the damage a stage
// needs by the damage a frame produces says whether a clear can happen in the frames a recording of that stage has.
import {readFileSync} from 'node:fs';
import {core,memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const stage = Number(process.argv[2] ?? 1);
const frames = Number(process.argv[3] ?? 3000);
const power = Number(process.argv[4] ?? 0);
const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const c = await core();
const raw = readFileSync(path);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const source = c.resources_create();
if (c.resources_open(source, data, raw.length) !== 1) throw Error('resources_open failed');
const s = c.game_session_create(), render = c.comp_create();
if (c.game_session_begin(s, source, stage, 0, 0, 2, 0) !== 1) throw Error('begin: ' + c.game_session_error(s));
if (power) {
  const economy = c.battle_data(s, 0);
  new DataView(c.memory.buffer).setInt32(economy + 4, power, true);
}
let last = 0, markFrame = 0, markDamage = 0;
for (let f = 0; f < frames; ++f) {
  // Shoot, and stay alive so the number is about damage and not about surviving.
  if (c.game_session_update(s, 1, 0, 0, 0, 0, 0) !== 1) { console.log(`  update failed at ${f}: ${c.game_session_error(s)}`); process.exit(1); }
  if (c.game_session_invincibility(s, 600) < 0) { console.log('  invincibility refused'); process.exit(1); }
  if (c.game_session_render(s, render) !== 1) { console.log(`  render failed at ${f}`); process.exit(1); }
  if (f < 4) {
    const m = c.battle_data(s, 2);
    const v = new DataView(c.memory.buffer);
    console.log(`   start f=${f} x=${v.getFloat32(m, true).toFixed(1)} y=${v.getFloat32(m + 4, true).toFixed(1)}`);
  }
  const damage = c.game_session_damage_total(s);
  if (f % 300 === 0 || f === frames - 1) {
    const span = f - markFrame;
    const rate = span ? ((damage - markDamage) / span) : 0;
    console.log(`   f=${String(f).padStart(5)} stage=${c.game_session_value(s, 2)} power=${new DataView(c.memory.buffer).getInt32(c.battle_data(s, 0) + 4, true)} ` +
      `damage=${damage} rate=${rate.toFixed(2)}/frame bossHp=${c.game_session_boss_health(s, 0)}/${c.game_session_boss_health(s, 1)}`);
    markFrame = f; markDamage = damage;
  }
  if (c.game_session_value(s, 0) !== 1) { console.log(`  left the stage at frame ${f}`); break; }
  last = damage;
}
console.log(`  total damage after ${frames} frames of continuous shooting: ${last}`);
process.exit(0);
