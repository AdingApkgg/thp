// Play one of the original's own replays through the port, in the node core, and watch the stage instead of the
// frame counter. A policy cannot clear a stage without dodging, but the original shipped recordings of its own
// stages, and replaying one drives the original stage scripts with the original inputs. If the port follows the
// replay from stage 1 into stage 2, that is a whole-stage result rather than a claim that it runs.
//
//   TH12_DATA=<path to th12.dat> node tools/th12-replay-campaign.mjs [demo3.rpy] [frames]
//
// Run it from `runtimes/th12/th12_web` so the helpers resolve the built core. The game data is not distributed,
// which is why this is a diagnostic and not a gate.
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {core,memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const wantName = process.argv[2] ?? 'demo3.rpy';
const frames = Number(process.argv[3] ?? 9000);
// A nonzero fourth argument holds the player invincible: the stage machinery and the player's survival are two
// different questions, and only the first one is about whether the original's stage scripts play through.
const invincible = Number(process.argv[4] ?? 0);
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
// The archive's own table, with its own count: game_resources_entry_name keeps returning a pointer past the end,
// so a listing built on it never terminates.
const archive = c.archive_create();
if (c.archive_open(archive, data, raw.length, 12) !== 1) throw Error('archive_open failed (pbg version 12)');
const count = c.archive_count(archive);
const names = [];
for (let i = 0; i < count; ++i) names.push(text(c.archive_name(archive, i)));
const index = names.indexOf(wantName);
const replays = names.filter(n => /\.rpy$/i.test(n));
console.log(`  archive entries: ${count}, replays: ${replays.join(' ') || '(none)'}`);
if (index < 0) throw Error(`no ${wantName} in the archive; saw ${replays.join(' ') || 'none'}`);

const cap = 1 << 22;
const buf = c.allocate(cap);
const size = c.archive_read(archive, index, buf, cap);
if (size < 0) throw Error('archive_read failed for ' + wantName);
console.log(`  ${wantName}: ${size} bytes sha256=`);

// The decoded stage table first: a demo that holds several stages ends each one where that stage ended, which is
// what tells "the recording stopped early" apart from "the port did not clear the stage".
const rp = c.replay_create();
if (c.replay_open(rp, buf, size) !== 1) throw Error('replay_open: ' + text(c.replay_error(rp)));
for (let n = 1; n <= 7; ++n) {
  const sp = c.replay_stage(rp, n);
  if (!sp) continue;
  const v = new DataView(c.memory.buffer);
  const w = [0, 4, 8, 12].map(k => v.getUint32(sp + k, true));
  console.log(`  stage ${n}: ptr=${sp} words=${w.join(',')}`);
}

// The decoded stage header, word by word. ReplayStageState::read takes the seed from +2, the score from +12 and the
// position from +32/+36; if those offsets are wrong the player is put somewhere the recording never put it, which is
// what an immediate collision looks like.
{
  const base = c.replay_data(rp), total = c.replay_size(rp);
  const v = new DataView(c.memory.buffer);
  const st = 1; // the stage the recording will select
  let off = 0;
  for (let n = 1; n <= 7; ++n) { const sp = c.replay_stage(rp, n); if (sp && n === st || (sp && !off)) { off = v.getUint32(sp + 4, true); break; } }
  const word = (o) => v.getUint32(base + o, true);
  const fh = [];
  for (let k = 0; k < 0x70; k += 4) fh.push(word(k));
  console.log(`  file header: ${fh.map(x => x.toString(16).padStart(8, '0')).join(' ')}`);
  console.log(`  decoded ${total} bytes, stage ${st} header at ${off}:`);
  for (let k = 0; k < 0xB0; k += 16) {
    const row = [];
    for (let j = 0; j < 16; j += 4) row.push(v.getUint32(base + off + k + j, true));
    console.log(`   +${String(k).padStart(3)}: ${row.map(x => x.toString().padStart(10)).join(' ')}`);
  }
}
const s = c.game_session_create(), render = c.comp_create();
// demo=1 is the attract path the title takes for the same file; stage 0 lets the replay choose its own stage.
if (c.game_session_replay(s, source, buf, size, 0, 1) !== 1) throw Error('replay begin: ' + text(c.game_session_error(s)));
let lastStage = c.game_session_value(s, 2), died = false;
// The recording's own bits next to the player's own position: a player that does not move where its bits ask is a
// different fault from one that moves and is still hit, and a death shows which of the two it was.
const history = [];
for (let f = 0; f < frames; ++f) {
  if (c.game_session_update(s, 0, 0, 0, 0, 0, 0) !== 1) {
    console.log(`  update failed at ${f}: ${text(c.game_session_error(s))}`);
    process.exit(1);
  }
  if (invincible && c.game_session_invincibility(s, invincible) < 0) { console.log('  invincibility refused'); process.exit(1); }
  if (c.game_session_render(s, render) !== 1) { console.log(`  render failed at ${f}`); process.exit(1); }
  const view = new DataView(c.memory.buffer);
  const phase = c.game_session_value(s, 0), stage = c.game_session_value(s, 2);
  const economy = c.battle_data(s, 0);
  const lives = view.getInt32(economy + 16, true);
  const motion = c.battle_data(s, 2);
  history.push({ f, held: c.game_session_replay_input(s), x: motion ? Math.round(view.getFloat32(motion, true)) : 0,
    y: motion ? Math.round(view.getFloat32(motion + 4, true)) : 0, lives });
  if (history.length > 40) history.shift();
  if (history.length > 1 && lives < history[history.length - 2].lives) {
    console.log(`   DEATH at f=${f} (lives ${history[history.length - 2].lives} -> ${lives}), frames before it:`);
    for (const e of history.slice(-21, -1)) {
      if (e.f % 2 === 0) console.log(`     f=${String(e.f).padStart(4)} held=${e.held.toString(16).padStart(4, '0')} x=${String(e.x).padStart(5)} y=${String(e.y).padStart(5)}`);
    }
  }
  if (f < 400 && f % 20 === 0) {
    const l = history[history.length - 1];
    console.log(`   f=${String(f).padStart(4)} held=${l.held.toString(16).padStart(4, '0')} x=${String(l.x).padStart(5)} y=${String(l.y).padStart(5)} lives=${l.lives}`);
  }
  if (f % 600 === 0 || stage !== lastStage) {
    console.log(`   f=${String(f).padStart(5)} phase=${phase} stage=${stage} frame=${c.game_session_value(s, 1)} ` +
      `enemies=${c.game_session_value(s, 7)} bullets=${c.game_session_value(s, 8)} ` +
      `lives=${lives} power=${view.getInt32(economy + 4, true)} ` +
      `replayFrame=${c.game_session_replay_frame(s)} battle=${c.game_session_value(s, 5)} player=${c.game_session_value(s, 6)} ` +
      `damage=${c.game_session_damage_total(s)} bossHp=${c.game_session_boss_health(s, 0)}/${c.game_session_boss_health(s, 1)}`);
  }
  if (stage !== lastStage) { console.log(`  STAGE CHANGED ${lastStage} -> ${stage} at frame ${f}`); lastStage = stage; }
  if (phase !== 1) {
    console.log(`  left the stage at frame ${f}, phase ${phase} (0 title, 2 paused, 3 game over, 4 finished, 5 ending)`);
    died = true;
    break;
  }
}
console.log(died ? '  ended' : `  still in phase 1 after ${frames} frames, stage ${lastStage}`);
