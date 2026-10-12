// TH12 extended-opcode coverage gate.
//
// docs/th12/ecl-extended-opcodes.json classifies every opcode id >= 256 that
// TH12 can emit. The engine must not run a TH11 handler for an id TH12 gave a
// different instruction to, so EnemyScript.cpp carries an explicit refusal list
// for the collisions. This test ties the two together: if the map gains a
// collision the engine has not acknowledged, or the engine refuses an id the map
// does not call a collision, the suite fails.
//
// It also asserts that every opcode th12.dat actually executes is classified -
// so "unimplemented" is always an enumerated, reviewable state rather than an
// opcode discovered by crashing.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { root } from './th12-oracle.mjs';

const MAP = resolve(root, '../../../docs/th12/ecl-extended-opcodes.json');
const SOURCE = resolve(root, 'cpp/game/EnemyScript.cpp');
const USAGE = resolve(root, 'artifacts/cpp/verification/th12-ecl-opcodes.json');

test('TH12 extended-opcode map is current and the engine refuses every collision', () => {
  const map = JSON.parse(readFileSync(MAP, 'utf8'));
  const source = readFileSync(SOURCE, 'utf8');

  const declared = source.match(/kTh12CollidingOpcodes\[\]\s*=\s*\{([^}]*)\}/);
  assert.ok(declared, 'EnemyScript.cpp no longer declares kTh12CollidingOpcodes');
  const engine = declared[1].split(',').map(s => s.trim()).filter(Boolean).map(Number).sort((a, b) => a - b);

  const collisions = map.entries.filter(e => e.verdict === 'collision' && e.usedInTh12Dat > 0)
    .map(e => e.id).sort((a, b) => a - b);

  assert.deepEqual(engine, collisions,
    'the engine refusal list and the collision verdicts in docs/th12/ecl-extended-opcodes.json disagree');

  // Every opcode TH12's own data executes must be classified.
  const used = map.entries.filter(e => e.usedInTh12Dat > 0);
  const unclassified = used.filter(e => !e.verdict || e.verdict === 'unused');
  assert.deepEqual(unclassified.map(e => e.id), [], 'opcodes used by th12.dat but not classified');

  // A signature that differs from TH11's is the mechanical collision test; an
  // id TH12 alone defines could still collide semantically, which is why the
  // verdict is a conservative subset and not a completeness proof.
  for (const e of used) {
    if (e.verdict === 'collision') {
      assert.notEqual(e.th11, 'same', `opcode ${e.id} marked collision but its signature matches TH11`);
      assert.notEqual(e.th11, 'new', `opcode ${e.id} marked collision but TH11 has no such opcode`);
    }
  }

  if (existsSync(USAGE)) {
    const usage = JSON.parse(readFileSync(USAGE, 'utf8'));
    const extendedUsed = usage.usedOpcodes.filter(e => e.id >= 256).length;
    assert.equal(used.length, extendedUsed, 'map and usage artifact disagree on the extended opcode set');
  }

  const refusedInstructions = collisions.reduce((n, id) => n + (map.entries.find(e => e.id === id)?.usedInTh12Dat ?? 0), 0);
  const todo = used.filter(e => e.verdict === 'todo');
  console.log(`TH12 extended opcodes: ${used.length} used, ` +
    `${collisions.length} collisions refused (${refusedInstructions} instructions), ` +
    `${todo.length} still to transcribe (${todo.reduce((n, e) => n + e.usedInTh12Dat, 0)} instructions)`);
});
