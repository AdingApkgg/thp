// Probe every th12 stage against the portable engine and report, for each, how
// far it gets before the engine refuses an opcode. This turns "which opcode is
// missing" from a guess into a measurement, and it is the input the transcription
// order should follow rather than raw instruction counts.
//
// Each stage gets its own wasm instance: the engine holds global state, so
// reusing one instance across stages measures the previous stage's leftovers as
// much as the current one.
//
//   node tools/th12-stage-probe.mjs [frames] [--stages 1,2,3]
import { WASI } from 'node:wasi';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const web = resolve(root, 'runtimes/th12/th12_web');
const args = process.argv.slice(2);
const frames = Number(args.find(a => /^\d+$/.test(a)) ?? 3000);
// Held input word for every frame. Bit 0 is the shot button; firing is what lets enemy waves be cleared.
const heldArg = args.indexOf('--held');
const HOLD_SHOOT = heldArg >= 0 && args[heldArg + 1] ? Number(args[heldArg + 1]) : 1;
const stageArg = args.indexOf('--stages');
const stages = stageArg >= 0 && args[stageArg + 1]
  ? args[stageArg + 1].split(',').map(Number)
  : [1, 2, 3, 4, 5, 6, 7];

const target = JSON.parse(readFileSync(resolve(web, 'target.json'), 'utf8'));
const archive = readFileSync(target.dataArchives['th12.dat'].path);
const coreBytes = readFileSync(resolve(web, 'artifacts/cpp/game-core-test.wasm'));

async function engine() {
  const wasi = new WASI({ version: 'preview1', args: [], env: {}, preopens: {} });
  const { instance } = await WebAssembly.instantiate(coreBytes, { wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(instance);
  const c = instance.exports;
  const readCString = ptr => {
    if (typeof ptr !== 'number' || ptr === 0) return '';
    const view = new Uint8Array(c.memory.buffer, ptr >>> 0, 4096);
    const end = view.indexOf(0);
    return new TextDecoder().decode(view.subarray(0, end < 0 ? 4096 : end));
  };
  const p = c.allocate(archive.length);
  new Uint8Array(c.memory.buffer, p, archive.length).set(archive);
  const resources = c.resources_create();
  if (c.resources_open(resources, p, archive.length) !== 1) {
    throw new Error(`th12.dat rejected: ${readCString(c.resources_error(resources))}`);
  }
  return { c, resources, readCString };
}

console.log(`probing ${stages.length} stage(s), ${frames} frames each`);
{
  // resources_count takes the handle, not zero: called with 0 it returns 0 whatever the archive holds, which
  // is where the misleading "0 entries" came from.
  const probe = await engine();
  console.log(`archive: ${probe.c.resources_count(probe.resources)} entries`);
}

const rows = [];
for (const stage of stages) {
  const { c, resources, readCString } = await engine();
  const game = c.game_session_create();
  // How far the stage actually got comes from the session's own accessors rather than from the frame count:
  // 0 is the phase, 1 the frame, 2 the stage number, 7 the enemy count and 8 the active bullet count, while
  // transition 10 is the completion exit code. Reaching the end of a stage is therefore a signal the probe can
  // assert on, and a non-zero enemy or bullet high water mark shows the stage ran content rather than idling.
  const value = k => (c.game_session_value ? c.game_session_value(game, k) : -999);
  const transition = k => (c.game_session_transition_value ? c.game_session_transition_value(game, k) : -999);
  // A stage cannot be measured to its end with a player that dies: without input it dies around frame 4000 and
  // the session then freezes. The first attempt computed PlayerFrameState's invincibility timer offset from the
  // struct layout and wrote it each frame. The samples came back empty, which showed battle_data is not exported
  // to this wasm build at all, so the write was aimed at address zero and did nothing whatsoever - a stage that
  // looked immune was merely a stage that had not been touched. What replaces it is a named export,
  // game_session_invincibility, which sets the timer through the same set call the game itself uses. Whether it
  // is present is reported, so a build that lacks it cannot pass for a stage that survived.
  const keepAlive = typeof c.game_session_invincibility === 'function'
    ? () => c.game_session_invincibility(game, 9999)
    : null;
  const keepAliveAvailable = keepAlive !== null;
  let refused = null, survived = 0, started = false, crashed = null, crashFrames = [], clamps = 0, clampFirst = 0, clampOpcode = -1, clampArgument = -1;
  let startPhase = -999, endPhase = -999, endStage = -999, leftPhaseAt = 0, exitCode = 0, maxEnemies = 0, maxBullets = 0;
  // Running the full budget used to mean one thing only, but round 105 showed it means two: stages 1 and 2 came
  // back with exactly the content peaks they had while blocked, so they were no longer refusing, they had died
  // in place with the frame counter still climbing. battle frame is the signal that separates them, since it
  // advances every frame the battle updates and stops when the world does. A run of 600 frames without it
  // moving is recorded with the counts at that moment, so "ran the full budget" now splits into still moving
  // and stopped moving.
  let lastBattleFrame = -1, sameBattleFrameRun = 0, stalledAt = 0, stalledEnemies = 0, stalledBullets = 0, stalledPhase = -999;
  // Whether the stage is still the active one is a different question from whether the battle is updating.
  // Stages 1 and 2 run 20000 frames with a live battle and still no completion exit, which is five and a half
  // minutes against a stage length of two to three, so the next thing to establish is whether the stage has in
  // fact already ended and the completion or dialogue sequence is sitting waiting for input, which the probe
  // never supplies. transition 2 is stage_active and 0 is transitioning, 1 transition_started, 3 outgoing_stage,
  // 5 the result timer and 7 the transition timer, so the samples record all of them.
  let stageInactiveAt = 0, firstInactiveSample = null;
  // Instrumentation for the four hop stage end chain: whether the dialogue object exists, becomes active, and
  // which command and instruction it holds.
  let dialogueSeen = 0, dialogueFirstSeenAt = 0, dialogueActiveAt = 0, lastDialogue = null;
  // The cursors of the first four enemies: what the remaining ones are executing while nothing progresses.
  // Walk the stage script from offset 700 through the 708..756 cycle body and past it, chaining by each
  // instruction's length, so the loop can be read as a whole instead of one sampled offset at a time.
  let stageWalk = null, stageLayout = null;
  const enemyScripts = []; let firstEnemyScripts = null, lastEnemyScripts = null;
  // Opcode -> first frame it was executed by any live enemy. 0x152 is the dialogue starter.
  const opcodesSeen = new Map();
  // The stage script's cursor. A cursor that keeps advancing means the stage script is running; one that parks
  // names the instruction the stage is waiting on.
  const stageScripts = []; let lastScriptOffset = -1, scriptOffsetChanges = 0, scriptLastChangeAt = 0, scriptSameRun = 0, scriptLongestStill = 0;
  const samples = [];
  try {
    if (c.game_session_begin(game, resources, stage, 0, 0, 1, 0) === 1) {
      started = true;
      startPhase = value(0);
      // What the STD parser kept. If the instruction count is small, the region parsed is a camera script and
      // the enemy spawning script is elsewhere in the file, which would make the closing spin loop the end of
      // the wrong script. The last instruction's offset and opcode cross check the decode, which put it at 772.
      if (c.game_session_stage_layout) {
        stageLayout = {
          instructions: c.game_session_stage_layout(game, 0),
          objects: c.game_session_stage_layout(game, 1),
          instances: c.game_session_stage_layout(game, 2),
          lastOffset: c.game_session_stage_layout(game, 3),
          lastOpcode: c.game_session_stage_layout(game, 4),
        };
        console.log(`    stage ${stage}: layout ${JSON.stringify(stageLayout)}`);
      }
      if (c.game_session_stage_decode) {
        stageWalk = [];
        for (const start of [708, 756]) {
          let o = start;
          for (let n = 0; n < 24; ++n) {
            const op = c.game_session_stage_decode(game, o, 0);
            if (op === 0xfffffffe || op === 0xffffffff) { stageWalk.push({ start, offset: o, opcode: op }); break; }
            const len = c.game_session_stage_decode(game, o, 2), argc = c.game_session_stage_decode(game, o, 4);
            const args = []; for (let a = 0; a < Math.min(argc, 4); ++a) args.push(c.game_session_stage_decode(game, o, 5 + a));
            stageWalk.push({ start, offset: o, opcode: op, time: c.game_session_stage_decode(game, o, 1), length: len, args });
            if (!(len > 0)) break; o += len;
          }
        }
      }
      for (let frame = 0; frame < frames; frame++) {
        if (keepAlive) keepAlive();
        // The probe used to pass every input word as zero, which means the player never fires. Enemies then
        // never die, and a stage whose script waits for a wave to be cleared waits forever: stage 1 ran 20000
        // frames, five and a half minutes against a two to three minute stage, with the battle updating
        // throughout, the enemy count high and never reaching zero, and no transition ever starting. Holding the
        // shot button is what turns "the stage is running" into "the stage can finish".
        // Dialogue command 21 is what ends a stage: Dialogue.cpp case 21 calls dialogue_stage_complete, which is
        // GameBattle::completion.complete(), whose first gate is the stage result animation. A dialogue advances
        // on confirmation, and the confirm word was still zero after shooting and movement were supplied, so the
        // stage could never reach its end no matter how thoroughly its waves were cleared. The held word carries
        // shots and movement; confirm is the seventh argument.
        if (c.game_session_dialogue_probe && frame % 300 === 0) {
          const dExists = c.game_session_dialogue_probe(game, 0), dActive = c.game_session_dialogue_probe(game, 1), dOp = c.game_session_dialogue_probe(game, 2), dIns = c.game_session_dialogue_probe(game, 3), dWait = c.game_session_dialogue_probe(game, 5);
          if (dExists === 1 || dActive === 1 || dialogueSeen === 0) { dialogueSeen = 1; lastDialogue = { frame: survived + 1, exists: dExists, active: dActive, opcode: dOp, instruction: dIns, waiting: dWait }; }
          if (dExists === 1 && !dialogueFirstSeenAt) dialogueFirstSeenAt = survived + 1;
          if (dActive === 1 && !dialogueActiveAt) dialogueActiveAt = survived + 1;
        }
        if (c.game_session_stage_script_probe) {
          const off = c.game_session_stage_script_probe(game, 0);
          if (off !== lastScriptOffset) { lastScriptOffset = off; scriptOffsetChanges++; scriptLastChangeAt = survived + 1; }
          else ++scriptSameRun;
          if (scriptSameRun > scriptLongestStill) scriptLongestStill = scriptSameRun;
          if (frame % 600 === 0) stageScripts.push({ decodeOpcode: c.game_session_stage_decode ? c.game_session_stage_decode(game, off, 0) : -1, decodeTime: c.game_session_stage_decode ? c.game_session_stage_decode(game, off, 1) : -1, decodeArgCount: c.game_session_stage_decode ? c.game_session_stage_decode(game, off, 4) : -1, decodeArg0: c.game_session_stage_decode ? c.game_session_stage_decode(game, off, 5) : -1, decodeArg1: c.game_session_stage_decode ? c.game_session_stage_decode(game, off, 6) : -1, frame: survived + 1, offset: off, begin: c.game_session_stage_script_probe(game, 1), frameCount: c.game_session_stage_script_probe(game, 2), scriptTimer: c.game_session_stage_script_probe(game, 3), scriptRate: c.game_session_stage_script_probe(game, 11), effectRate: c.game_session_stage_script_probe(game, 12), state: c.game_session_stage_script_probe(game, 5), instances: c.game_session_stage_script_probe(game, 9) });
        }
        if (c.game_session_enemy_script_probe) {
          // Every frame, collect the opcodes the surviving enemies are executing. Sampling every 600 frames can
          // miss a brief instruction, and the question is whether opcode 0x152, the one that starts a dialogue,
          // is ever executed at all.
          for (let i = 0; i < 8; ++i) { const op = c.game_session_enemy_script_probe(game, i, 2); if (op < 0 || op > 0xffff) break; if (!opcodesSeen.has(op)) opcodesSeen.set(op, survived + 1); }
        }
        if (c.game_session_enemy_manager_probe && frame % 3000 === 0 && frame < 10000) {
          const ids = [], ops = [], times = [];
          for (let i = 0; i < 8; ++i) {
            ids.push(c.game_session_enemy_script_probe ? c.game_session_enemy_script_probe(game, i, 0) : -9);
            ops.push(c.game_session_enemy_script_probe ? c.game_session_enemy_script_probe(game, i, 2) : -9);
            times.push(c.game_session_enemy_script_probe ? c.game_session_enemy_script_probe(game, i, 1) : -9);
          }
          console.log(`    f${survived + 1} boss=${c.game_session_boss_probe ? c.game_session_boss_probe(game, 0) : -9} phases=${c.game_session_boss_probe ? c.game_session_boss_probe(game, 1) : -9} bossPtr=${c.game_session_boss_probe ? c.game_session_boss_probe(game, 3) : -9} count=${c.game_session_enemy_manager_probe(game, 0)} total_created=${c.game_session_enemy_manager_probe(game, 1)} last_error=${c.game_session_enemy_manager_probe(game, 2)} ids=[${ids}] ops=[${ops}] times=[${times}]`);
        }        if (c.game_session_enemy_script_probe && frame % 600 === 0) {
          enemyScripts.length = 0;
          for (let i = 0; i < 4; ++i) enemyScripts.push({ id: c.game_session_enemy_script_probe(game, i, 0), time: c.game_session_enemy_script_probe(game, i, 1), opcode: c.game_session_enemy_script_probe(game, i, 2), insTime: c.game_session_enemy_script_probe(game, i, 4) });
          if (frame === 0) firstEnemyScripts = JSON.parse(JSON.stringify(enemyScripts));
          lastEnemyScripts = JSON.parse(JSON.stringify(enemyScripts));
        }
        const sweep = frame % 180 < 90 ? 0x40 : 0x80;
        const climb = frame % 600 < 300 ? 0x10 : 0;
        if (c.game_session_update(game, HOLD_SHOOT | sweep | climb, 0, 0, 0, 1, 0) === 0) { refused = readCString(c.game_session_error(game)); break; }
        survived = frame + 1;
        const phase = value(0), enemies = value(7), bullets = value(8), exit = transition(10);
        if (enemies > maxEnemies) maxEnemies = enemies;
        if (bullets > maxBullets) maxBullets = bullets;
        if (phase !== startPhase && leftPhaseAt === 0) leftPhaseAt = survived;
        // The completion exit code is the stage-end signal. A phase change is only recorded, not used to stop:
        // the intro and battle phases differ too, so leaving the phase is not the same as finishing the stage.
        if (exit !== 0) { exitCode = exit; break; }
        const battleFrame = transition(4);
        if (battleFrame === lastBattleFrame) {
          ++sameBattleFrameRun;
          if (sameBattleFrameRun === 600 && stalledAt === 0) {
            stalledAt = survived; stalledEnemies = enemies; stalledBullets = bullets; stalledPhase = phase;
          }
        } else { sameBattleFrameRun = 0; lastBattleFrame = battleFrame; }
        const stageActive = transition(2);
        if (stageActive === 0 && stageInactiveAt === 0) stageInactiveAt = survived;
        if (frame % 600 === 0) {
          const sample = { frame: survived, phase, enemies, bullets, stage: value(2), exit, battleFrame,
            transitioning: transition(0), transitionStarted: transition(1), stageActive,
            outgoing: transition(3), resultTimer: transition(5), hudFlags: transition(6), transitionTimer: transition(7) };
          if (sample.stageActive === 0 && !firstInactiveSample) firstInactiveSample = sample;
          samples.push(sample);
        }
      }
      endPhase = value(0); endStage = value(2);
    } else {
      refused = readCString(c.game_session_error(game));
    }
  } catch (error) {
    // A wasm trap is a per-stage outcome, not a reason to lose the other stages:
    // an abort used to end the whole run and hide every stage after it.
    const stack = String(error?.stack ?? error?.message ?? error);
    crashed = stack.split('\n')[0];
    crashFrames = [...stack.matchAll(/wasm-function\[(\d+)\]:?(0x[0-9a-f]+)?/g)].map((m) => `${m[1]}:${m[2] ?? ""}`);
  } finally {
    try {
      clamps = c.ecl_stack_clamps ? c.ecl_stack_clamps() : 0;
      clampFirst = c.ecl_stack_clamp_first_offset ? c.ecl_stack_clamp_first_offset() : 0;
      clampOpcode = c.ecl_clamp_opcode ? c.ecl_clamp_opcode() : -1;
      clampArgument = c.ecl_clamp_argument ? c.ecl_clamp_argument() : -1;
      c.game_session_delete(game);
    } catch { /* the instance is already unusable */ }
  }
  const opcode = refused?.match(/ECL opcode (\d+)/)?.[1] ?? null;
  rows.push({ stage, started, framesSurvived: survived, startPhase, endPhase, leftPhaseAt, endStage, exitCode, reachedStageEnd: exitCode !== 0, maxEnemies, maxBullets, keepAliveAvailable, stalledAt, stalledEnemies, stalledBullets, stalledPhase, stageInactiveAt, firstInactiveSample, dialogueFirstSeenAt, dialogueActiveAt, lastDialogue, firstEnemyScripts, lastEnemyScripts, opcodesSeen: Object.fromEntries(opcodesSeen), sawDialogueOpcode: opcodesSeen.has(0x152), scriptOffsetChanges, scriptLastChangeAt, scriptLongestStill, stageWalk, stageScripts, dialogueOpcodeAt: opcodesSeen.get(0x152) ?? 0, opcode: opcode ? Number(opcode) : null, error: refused, crashed, crashFrames, clamps, clampFirst, clampOpcode, clampArgument, samples });
  console.log(`  stage ${stage}: ${started ? 'started' : 'REFUSED AT BOOT'}, survived ${survived} frames, enemies<=${maxEnemies}, bullets<=${maxBullets}, phase ${startPhase}->${endPhase}${keepAliveAvailable ? ', kept alive' : ', NO keep-alive export'}` +
    (stageInactiveAt ? `, stage became INACTIVE at frame ${stageInactiveAt}` : ', stage stayed active') +
    (stalledAt ? `, STALLED from frame ${stalledAt} (phase ${stalledPhase}, enemies ${stalledEnemies}, bullets ${stalledBullets})` : '') +
    (exitCode ? `, STAGE END exit=${exitCode}` : '') +
    (opcode ? `, then ECL opcode ${opcode}` : refused ? `, then: ${refused}` : crashed ? `, then CRASHED: ${crashed}` : ', ran the full budget without a stage end') + (clamps ? ` [${clamps} clamped stack access(es), max position ${clampFirst}, opcode 0x${clampOpcode.toString(16)}, argument ${clampArgument}]` : ''));
}

const outDir = resolve(root, 'artifacts/th12');
mkdirSync(outDir, { recursive: true });
writeFileSync(resolve(outDir, 'stage-probe.json'), `${JSON.stringify({
  target: { game: target.game, version: target.version, sha256: target.sha256 },
  framesPerStage: frames, stages: rows,
}, null, 2)}\n`);
console.log(`wrote ${resolve(outDir, 'stage-probe.json')}`);
