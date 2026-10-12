// TH12 engine boot test: the real portable engine, not a parser, loading th12.dat.
//
// The resource readers were already proven equivalent to thtk one file at a time.
// This test asks the next question: does the *engine's own* resource layer accept
// a complete TH12 installation - core ANMs, all six shot definitions, the default
// ECL and all seven stage sets (background/logo/enemy ANM, timeline ECL, six
// dialogue files)? Starting an actual battle on top of them is a separate test
// because it depends on TH12's opcode semantics, which are still incomplete.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

let coreSnapshot;
async function core() {
  const file = process.env.TH12_CORE_TEST_FILE
    ? resolve(process.env.TH12_CORE_TEST_FILE)
    : resolve(root, 'artifacts/cpp/game-core-test.wasm');
  const bytes = coreSnapshot ??= readFileSync(file);
  const wasi = new WASI({ version: 'preview1', args: [], env: {}, preopens: {} });
  const { instance } = await WebAssembly.instantiate(bytes, { wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(instance);
  return instance.exports;
}

function readCString(c, ptr) {
  if (!ptr) return '';
  const view = new Uint8Array(c.memory.buffer, ptr >>> 0, 512);
  const end = view.indexOf(0);
  return new TextDecoder().decode(view.subarray(0, end < 0 ? 512 : end));
}

async function withEngine(fn) {
  const archive = readFileSync(target.dataArchives['th12.dat'].path);
  const c = await core();
  const p = c.allocate(archive.length);
  new Uint8Array(c.memory.buffer, p, archive.length).set(archive);
  const resources = c.resources_create();
  const session = c.session_resources_create();
  try {
    assert.equal(c.resources_open(resources, p, archive.length), 1, 'th12.dat rejected by the engine archive layer');
    assert.equal(c.resources_count(resources), 180, 'archive entry count');
    return await fn(c, resources, session);
  } finally {
    c.session_resources_delete(session);
    c.resources_delete(resources);
    c.release(p);
  }
}

test('TH12 engine loads core resources and every stage set from th12.dat', async () => {
  const stages = await withEngine(async (c, resources, session) => {
    assert.equal(c.session_resources_core(session, resources), 1,
      `core resource set (ANM/SHT/default ECL) did not load: ${readCString(c, c.session_resources_error(session))}`);

    const rows = [];
    for (let stage = 1; stage <= 7; stage++) {
      const set = c.stage_resources_create();
      try {
        assert.equal(c.resources_stage(resources, stage, set), 1,
          `stage ${stage}: stage resources did not load: ${readCString(c, c.resources_error(resources))}`);
        const row = {
          stage,
          background: c.stage_value(set, 0), logo: c.stage_value(set, 1), enemies: c.stage_value(set, 2),
          timeline: c.stage_value(set, 3), messages: c.stage_value(set, 5),
          messageBytes: Array.from({ length: 6 }, (_, i) => c.stage_message_size(set, i)),
        };
        assert.ok(row.background > 0 && row.logo > 0 && row.enemies > 0, `stage ${stage}: empty ANM`);
        assert.ok(row.timeline > 0, `stage ${stage}: empty timeline ECL`);
        assert.equal(row.messages, 6, `stage ${stage}: dialogue count`);
        assert.ok(row.messageBytes.every(n => n > 0), `stage ${stage}: empty dialogue`);
        assert.equal(c.session_resources_stage(session, resources, stage), 1,
          `stage ${stage}: session resources did not load: ${readCString(c, c.session_resources_error(session))}`);
        rows.push(row);
      } finally {
        c.stage_resources_delete(set);
      }
    }
    return rows;
  });

  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-engine-boot.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    coreSha256: sha(coreSnapshot),
    passed: true,
    archiveEntries: 180,
    stages,
  }, null, 2) + '\n');
});

// Booting a battle stops at the first ECL opcode TH12 renumbered away from TH11.
// That must be a clean, named failure - not a wasm trap. Before the collision
// gate in EnemyScript.cpp this died with `RuntimeError: unreachable` on a divide
// guard, because TH11's 402 handler ran TH12's 402 instruction. The exact opcode
// frontier moves as opcodes get transcribed, so this asserts the shape of the
// refusal and records which opcode it is.
test('TH12 session either starts the battle or refuses an untranscribed opcode by name', async () => {
  const outcome = await withEngine((c, resources) => {
    const game = c.game_session_create();
    try {
      const result = c.game_session_begin(game, resources, 1, 0, 0, 1, 0);
      const message = readCString(c, c.game_session_error(game));
      if (result === 1) return { started: true, message };
      assert.equal(result, 0, `expected success or a refusal, got ${result} (${message})`);
      const match = message.match(/ECL opcode (\d+)/);
      assert.ok(match, `refusal must name the opcode, got: ${message}`);
      const opcode = Number(match[1]);
      assert.ok(opcode >= 256, `frontier opcode should be in TH12's extended range, got ${opcode}`);
      return { started: false, message, opcode };
    } finally {
      c.game_session_delete(game);
    }
  });

  const map = JSON.parse(readFileSync(resolve(root, '../../../docs/th12/ecl-extended-opcodes.json'), 'utf8'));
  let frontier = null;
  if (!outcome.started) {
    const entry = map.entries.find(e => e.id === outcome.opcode);
    assert.ok(entry, `frontier opcode ${outcome.opcode} is absent from the extended opcode map`);
    assert.ok(entry.usedInTh12Dat > 0, `frontier opcode ${outcome.opcode} is not one th12.dat executes`);
    assert.ok(entry.verdict === 'collision' || entry.verdict === 'todo',
      `frontier opcode ${outcome.opcode} has verdict ${entry.verdict}`);
    frontier = {
      // `implemented-collision` means the engine transcribes the instruction but
      // still refuses this particular input, which is a named refusal too.
      ...outcome,
      verdict: entry.verdict,
      th12Signature: entry.signature,
      th11Signature: entry.th11,
    };
  }

  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-engine-refusal.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    coreSha256: sha(coreSnapshot),
    passed: true,
    battleStarts: outcome.started,
    frontier,
  }, null, 2) + '\n');
});

// The stage now boots and runs: 402/403 and the 280 relative spawn (0x118, the
// shared 0x100 body) are transcribed, which was every opcode stage 1's main
// prologue needed. The browser proof drives the same stage for ~90 s of attract
// demo, so 120 frames here is a floor, not the observed limit.
test('TH12 engine starts a stage battle and survives 120 frames', async () => {
  await withEngine((c, resources) => {
    const game = c.game_session_create();
    try {
      assert.equal(c.game_session_begin(game, resources, 1, 0, 0, 1, 0), 1,
        `GameSession::begin failed: ${readCString(c, c.game_session_error(game))}`);
      for (let frame = 0; frame < 120; frame++) {
        assert.notEqual(c.game_session_update(game, 0, 0, 0, 0, 0, 0), 0,
          `frame ${frame} failed: ${readCString(c, c.game_session_error(game))}`);
      }
    } finally {
      c.game_session_delete(game);
    }
  });
});
