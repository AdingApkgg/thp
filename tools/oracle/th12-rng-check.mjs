// Check the port's engine RNG against the original's own machine code running under Unicorn.
//
//   py -3 tools/oracle/th12-oracle.py --rng-steps 64 --seed 0xEAE0 --out tools/tmp/oracle-rng.json
//   py -3 tools/oracle/th12-oracle.py --rng32-steps 32 --seed 0xEAE0 --out tools/tmp/oracle-rng32.json
//   node tools/oracle/th12-rng-check.mjs tools/tmp/oracle-rng.json [tools/tmp/oracle-rng32.json ...]
//
// Run it from the repository root. This is the shape the objective asks for: the original's routine is the
// reference, the port's transcription is the thing under test, and the answer is a comparison rather than an
// assertion. A diagnostic and not a gate, because it needs th12.exe, which is not distributed.
import {readFileSync} from 'node:fs';
import {core,memory} from '../../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const paths = process.argv.slice(2);
if (!paths.length) {
  console.log('  usage: node tools/oracle/th12-rng-check.mjs <oracle-json>...');
  process.exit(2);
}
const c = await core();
let total = 0;
let failures = 0;
for (const path of paths) {
  const oracle = JSON.parse(readFileSync(path, 'utf8'));
  const twoDraw = /next32/.test(oracle.function ?? '');
  let seed = oracle.seed >>> 0;
  let calls = 0;
  const bad = [];
  let compared = 0;
  for (const step of oracle.steps) {
    // Both exports pack the new state as (seed << 16) | call count; the two-draw variant also hands back the
    // u32 the game would use, and that value is compared separately so the check is not only about the state.
    const packed = Number(twoDraw ? c.th12_rng32_step(seed, calls) : c.th12_rng_step(seed, calls)) >>> 0;
    const value = twoDraw ? Number(c.th12_rng32_value(seed, calls)) >>> 0 : null;
    const portSeed = (packed >>> 16) & 0xffff;
    const portCalls = packed & 0xffff;
    seed = portSeed;
    calls = portCalls;
    compared += 1;
    const expectedValue = twoDraw ? step.value >>> 0 : step.ax;
    if (portSeed !== step.seed || portCalls !== (step.calls & 0xffff) || (twoDraw ? value !== expectedValue : portSeed !== step.ax)) {
      if (bad.length < 6) {
        bad.push(`step ${compared - 1}: original seed=0x${step.seed.toString(16)} calls=${step.calls} value=${expectedValue} ` +
          `vs port seed=0x${portSeed.toString(16)} calls=${portCalls}${twoDraw ? ` value=${value}` : ''}`);
      }
    }
  }
  total += compared;
  if (bad.length) {
    failures += 1;
    console.log(`  FAIL ${path} (${oracle.function}): ${bad.length} of ${compared} steps disagree`);
    for (const line of bad) console.log(`    ${line}`);
  } else {
    console.log(`  PASS ${path} (${oracle.function}): the port agrees with th12.exe's own routine on all ${compared} steps`);
  }
}
console.log(`  compared ${total} steps across ${paths.length} routine(s), ${failures} failing`);
process.exit(failures ? 1 : 0);
