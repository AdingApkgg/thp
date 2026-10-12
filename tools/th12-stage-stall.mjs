// Read a stage that has parked: name the instruction the stage script's cursor is on, and say whether the script
// interpreter is even being reached.
//
//   node tools/th12-stage-stall.mjs [stage] [frames] [every]
//
// Run it from `runtimes/th12/th12_web`. The port's policy cannot dodge, so it holds the shot button and refreshes
// invincibility to keep the run alive; what is being looked at is the stage script, not the player. The cursor, the
// instruction under it, the draw flags that can skip the interpreter entirely, and the stage-interrupt counters are
// printed together, because "the script is waiting" and "the script is not being run" look identical from a frame
// counter alone.
import {readFileSync} from 'node:fs';
import {core,memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const stage = Number(process.argv[2] ?? 1);
const frames = Number(process.argv[3] ?? 9200);
const every = Number(process.argv[4] ?? 200);
// Passing a fifth argument makes the run tap the shot button instead of holding it: the dialogue's confirmation is a
// press edge, so holding a button can never produce one, and a run that only holds cannot show that.
const tap = process.argv[5] !== undefined;
const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const c = await core();
const raw = readFileSync(path);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const source = c.resources_create();
if (c.resources_open(source, data, raw.length) !== 1) throw Error('resources_open failed');
const s = c.game_session_create(), render = c.comp_create();
if (c.game_session_begin(s, source, stage, 0, 0, 2, 0) !== 1) throw Error('begin: ' + c.game_session_error(s));

const instructions = Number(c.game_session_stage_instruction_probe(s, 0, 0));
const nameCursor = () => {
  const cursor = c.game_session_stage_script_probe(s, 0);
  for (let i = 0; i < instructions; ++i) {
    if (c.game_session_stage_instruction_probe(s, 4, i) !== cursor) continue;
    const opcode = c.game_session_stage_instruction_probe(s, 2, i);
    const time = c.game_session_stage_instruction_probe(s, 1, i) | 0;
    const length = c.game_session_stage_instruction_probe(s, 3, i);
    const args = [];
    for (let k = 0; k < Math.min(4, Math.floor((length - 8) / 4)); ++k) args.push(c.game_session_stage_instruction_probe(s, 5 + k, i) | 0);
    return `index=${i} opcode=${opcode} time=${time} len=${length} args=[${args.join(',')}]`;
  }
  return 'cursor names no instruction';
};

let lastCursor = -1, frozen = 0;
for (let f = 0; f < frames; ++f) {
  if (c.game_session_update(s, 1, 0, 0, 0, 0, 0) !== 1) { console.log(`  update failed at ${f}: ${c.game_session_error(s)}`); process.exit(1); }
  if (c.game_session_invincibility(s, 600) < 0) { console.log('  invincibility refused'); process.exit(1); }
  if (c.game_session_render(s, render) !== 1) { console.log(`  render failed at ${f}`); process.exit(1); }
  const cursor = c.game_session_stage_script_probe(s, 0);
  if (cursor === lastCursor) ++frozen; else frozen = 0;
  lastCursor = cursor;
  if (f % every === 0 || c.game_session_value(s, 2) !== stage) {
    console.log(`   f=${String(f).padStart(5)} stage=${c.game_session_value(s, 2)} cursor=${cursor} frozen=${frozen} ` +
      `draw=${c.game_session_stage_script_probe(s, 13).toString(16)} fade=${c.game_session_stage_script_probe(s, 14)} ` +
      `objects=${c.game_session_stage_script_probe(s, 15)} ` +
      `interrupts=${c.game_session_stage_script_probe(s, 16)}/${c.game_session_stage_script_probe(s, 17)} ` +
      `dialogue=${c.game_session_dialogue_probe(s, 0)}/${c.game_session_dialogue_probe(s, 1)} ` +
      `dialogueOp=${c.game_session_dialogue_probe(s, 2)} dialogueNext=${c.game_session_dialogue_probe(s, 7)} ` +
      `release=${c.game_session_dialogue_probe(s, 6)} waiting=${c.game_session_dialogue_probe(s, 5)} ` +
      `dialogueTime=${c.game_session_dialogue_probe(s, 8) | 0} dialogueWait=${c.game_session_dialogue_probe(s, 9) | 0} ` +
      `enemies=${c.game_session_enemy_probe(s, 0, 0)} damage=${c.game_session_damage_total(s)}`);
    console.log(`         ${nameCursor()}`);
    // Every live enemy's own script, because the stage is waiting for one of them to interrupt it: an enemy parked
    // on a wait and an enemy that is gone look the same in a live count.
    const live = c.game_session_enemy_probe(s, 0, 0);
    for (let i = 0; i < Math.min(live, 4); ++i) {
      console.log(`         enemy[${i}] instance=${c.game_session_enemy_script_probe(s, i, 0)} ` +
        `opcode=${c.game_session_enemy_script_probe(s, i, 2)} ` +
        `instructionTime=${c.game_session_enemy_script_probe(s, i, 4) | 0} ` +
        `contextTime=${c.game_session_enemy_script_probe(s, i, 1) | 0} ` +
        `scriptState=${c.game_session_enemy_script_probe(s, i, 5)} ` +
        `flags=${c.game_session_enemy_probe(s, i, 1).toString(16)} hp=${c.game_session_enemy_probe(s, i, 2)}`);
    }
  }
  if (c.game_session_value(s, 2) !== stage) { console.log(`  STAGE CHANGED at frame ${f}`); break; }
}
process.exit(0);
