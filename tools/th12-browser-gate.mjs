// Checks the committed browser-run record. The run itself needs a browser and a static server, so the record it
// writes is what a plain checkout can verify. Every failure mode this session produced was a run with no errors in
// it, so the conditions below are about the run having played, not about it having stayed quiet.
//
//   node tools/th12-browser-gate.mjs --check     compares the record against the conditions below
//   node tools/th12-browser-gate.mjs             prints the record
//
// The record is produced by:
//   node tools/browser-proof.mjs --url http://127.0.0.1:8113/ --out <dir> --shots 2 --wait 60000 \
//     --sample 500 --all-samples --click "#start" --expect-start --expect-stage 1 --expect-progress \
//     --record docs/porting/browser-run.json --repeat "KeyZ:300:3000" --repeat "ArrowLeft:400:2600" \
//     --repeat "ArrowRight:400:3700" --repeat "ShiftLeft:900:2200"
// and the run fails on the same conditions, so the record cannot disagree with the run that wrote it.
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const CHECK = process.argv.includes('--check');
// The single-stage record is what every checkout can verify. The campaign record is the same run driven long enough
// to clear every stage, and it is checked by its own switch because it needs a browser for half an hour to produce.
const CAMPAIGN = process.argv.includes('--campaign');
const RECORD = resolve(root, CAMPAIGN ? 'docs/porting/browser-campaign-full.json' : 'docs/porting/browser-run.json');

// Measured on a real run (round 236): the entry path is the server root, the harness reaches its running state
// only from the start element, and a first stage is reached within the budget with keys injected.
const REQUIRED = {
  url: 'http://127.0.0.1:8113/',
  started: true,
  clicked: true,
  pageErrors: 0,
  consoleErrors: 0,
  stageMaxAtLeast: 1,
  playedSamplesAtLeast: 1,   // a run on the title reports the same stage and frame readings as a run in a stage
  playedFrameMaxAtLeast: 200,
  framesServedAtLeast: 300000, // a blank or error page produced 12885
  secondsAtLeast: 60,
};

// The campaign's screenshots are taken at a slower sampling interval and its canvas region is smaller, so the frame
// size floor is the campaign's own: the record is still required to hold a rendered frame, not a blank one.
const REQUIRED_CAMPAIGN = { ...REQUIRED, framesServedAtLeast: 100000 };
const needed = CAMPAIGN ? REQUIRED_CAMPAIGN : REQUIRED;
// One switch for the whole gate, because a checkout checking only the short run would miss the campaign's ending and
// the order its stages were reached in. It re-runs this file once per record so each keeps its own expectations.
if (process.argv.includes('--all')) {
  const { execFileSync } = await import('node:child_process');
  let failed = 0;
  for (const flags of [['--check'], ['--campaign', '--check']]) {
    try {
      process.stdout.write(execFileSync(process.execPath, [fileURLToPath(import.meta.url), ...flags], { encoding: 'utf8' }));
    } catch (error) {
      process.stdout.write(error.stdout ?? '');
      failed = 1;
    }
  }
  process.exit(failed);
}
const record = JSON.parse(readFileSync(RECORD, 'utf8'));
const failures = [];
if (record.kind !== 'th12-browser-run') failures.push(`kind is ${JSON.stringify(record.kind)}`);
if (record.url !== REQUIRED.url) failures.push(`url is ${JSON.stringify(record.url)}, not ${REQUIRED.url}`);
for (const key of ['started', 'clicked']) {
  if (record[key] !== REQUIRED[key]) failures.push(`${key} is ${JSON.stringify(record[key])}, not ${REQUIRED[key]}`);
}
for (const key of ['pageErrors', 'consoleErrors']) {
  if (!(record[key] <= REQUIRED[key])) failures.push(`${key} is ${record[key]}, not at most ${REQUIRED[key]}`);
}
// A start element that was never clicked, a health line that never appeared, and a stretch of time with nothing
// but a title on screen all pass every condition above, which is why the ones below exist.
if (!(record.stageMax >= REQUIRED.stageMaxAtLeast)) {
  failures.push(`stageMax is ${bucket(record.stageMax)}, not at least ${REQUIRED.stageMaxAtLeast}`);
}
if (!(record.framesServed >= needed.framesServedAtLeast)) {
  failures.push(`the largest frame was ${record.framesServed} bytes, not at least ${needed.framesServedAtLeast}`);
}
if (!(record.seconds >= REQUIRED.secondsAtLeast)) {
  failures.push(`the run lasted ${record.seconds}s, not at least ${REQUIRED.secondsAtLeast}s`);
}
if (!(record.stageTransitions >= 1)) {
  failures.push(`the run saw ${record.stageTransitions} stage transitions, so it never left the first stage`);
}
// The title increments the same frame counter as a stage, so a run that never left the title used to satisfy every
// condition above. Only the session phase separates the two, and this record is the only place it survives.
if (!(record.playedSamples >= REQUIRED.playedSamplesAtLeast)) {
  failures.push(`the run reported phase 1 in ${bucket(record.playedSamples)} samples, not at least ` +
    `${REQUIRED.playedSamplesAtLeast}: nothing proves the stage readings are not a title screen`);
}
// A campaign is stages in order and an ending, not a maximum: five in a row say the clear path runs, and the phase
// reaching the ending says the last clear led where it should.
if (CAMPAIGN) {
  // The title is stage 0 and the run passes through it, so the sequence is filtered to the stages themselves: what
  // is required is that the six arrived in order, not that nothing else was ever on screen.
  const sequence = (record.stageSequence ?? []).filter(s => s > 0);
  const expected = [1, 2, 3, 4, 5, 6];
  if (sequence.length !== expected.length || sequence.some((s, i) => s !== expected[i])) {
    failures.push(`the stages reached were ${JSON.stringify(sequence)}, not ${JSON.stringify(expected)}`);
  }
  if (!((record.phaseMax ?? -1) >= 5)) {
    failures.push(`the highest phase was ${bucket(record.phaseMax)}, so the campaign never reached the ending`);
  }
}
if (!(record.playedFrameMax >= REQUIRED.playedFrameMaxAtLeast)) {
  failures.push(`the stage frame reached ${bucket(record.playedFrameMax)} while phase 1, not at least ` +
    `${REQUIRED.playedFrameMaxAtLeast}`);
}
function bucket(v) { return v === null || v === undefined ? 'absent' : v; }

if (CHECK) {
  if (failures.length) {
    for (const f of failures) console.log(`  FAIL ${f}`);
  } else {
    console.log(`  PASS  ${CAMPAIGN ? 'the campaign record' : 'the record'} shows a started, clicked run: ` +
      `stage ${record.stageMax}, ${record.stageTransitions} transition(s), phase 1 for ${record.playedSamples} ` +
      `samples up to frame ${record.playedFrameMax}, ${record.seconds}s, largest frame ${record.framesServed} bytes, ` +
      `${record.pageErrors} page and ${record.consoleErrors} console errors` +
      (CAMPAIGN ? `, stages ${(record.stageSequence ?? []).filter(s => s > 0).join('>')} and phase ${record.phaseMax}` : ''));
  }
} else {
  console.log(JSON.stringify({ record, required: needed }, null, 2));
}
process.exit(failures.length && CHECK ? 1 : 0);
