// Compare the port's ECL container walk with the independent Python walker, file by file.
//
//   node tools/th-ecl-port-check.mjs <data-dir> <title> [reference.json]
//   node tools/th-ecl-port-check.mjs --all
//
// Run it from `runtimes/th12/th12_web`, or from the repository root with --all, which takes the six data directories
// the extraction pipeline writes. The Python walker reads the container in its own implementation of the format; the
// port reads it with `EclResource::open`, the same parser the engine uses. Two implementations agreeing on the number
// of files, sub-routines, instructions and distinct opcodes is a cross-check; one implementation agreeing with a
// remembered total is not. When no reference is given the Python tool is asked for one.
import {readFileSync, readdirSync, mkdirSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {resolve, join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {core, memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const here = fileURLToPath(new URL('.', import.meta.url));
const repo = resolve(here, '..');
const titles = ['12', '13', '14', '16', '17', '18'];
const all = process.argv.includes('--all');
const selection=process.argv.indexOf('--titles');
if(selection>=0&&!/^[0-9]+(?:,[0-9]+)*$/.test(process.argv[selection+1]??''))throw Error('--titles requires a comma-separated title list');

const c = await core();
let failures = 0;
const jobs = selection>=0
  ? process.argv[selection+1].split(',').map(t=>{
      const proof=JSON.parse(readFileSync(join(repo,'artifacts/archive-differential',`th${t}.json`),'utf8'));
      if(!proof.passed||!proof.extraction)throw Error(`th${t}: run the full archive differential first`);
      return {title:`th${t}`,digits:t,directory:proof.extraction};
    })
  : all
  ? titles.map(t => ({title: `th${t}`, digits: t,
      directory: join(repo, 'runtimes', `th${t}`, `th${t}_web`, 'artifacts', 'cpp', `th${t}-data`)}))
  : [{title: process.argv[3] ?? 'th13', digits: (process.argv[3] ?? 'th13').replace(/\D/g, ''),
      directory: resolve(process.argv[2] ?? '')}];

for (const job of jobs) {
  const referencePath = join(repo, 'tools', 'tmp', `ecl-walk-${job.digits}.json`);
  // Always walk the current extraction. A cached reference can silently compare
  // a new parser against a different resource set from an earlier build.
  mkdirSync(dirname(referencePath),{recursive:true});
  execFileSync('py', ['-3', join(repo, 'tools', 'th-ecl-walk.py'), '--title', job.digits, '--dir',
    job.directory, '--json', referencePath], {stdio: 'ignore',windowsHide:true});
  const reference = JSON.parse(readFileSync(referencePath, 'utf8'))[job.digits];
  if (!reference) { console.log(`   ${job.title}: no reference in ${referencePath}`); ++failures; continue; }

  const files = readdirSync(job.directory).filter(f => f.endsWith('.ecl')).sort();
  c.ecl_opcode_scan_reset();
  let subroutines = 0, instructions = 0, invalid = 0;
  for (const file of files) {
    const bytes = readFileSync(join(job.directory, file));
    const pointer = c.allocate(bytes.length);
    try{
      memory(c, pointer, bytes.length).set(bytes);
      if (c.ecl_walk_summary(pointer, bytes.length, 0) !== 1) { ++invalid; continue; }
      subroutines += c.ecl_walk_summary(pointer, bytes.length, 1);
      instructions += c.ecl_opcode_scan(pointer, bytes.length);
    }finally{c.release(pointer);}
  }
  const opcodes = c.ecl_opcode_scan_distinct();

  const measured = {files: files.length, subs: subroutines, instructions, opcodes, invalid};
  const wrong = [];
  if(!files.length||!subroutines||!instructions)wrong.push('empty resource walk is not a passing comparison');
  if(reference.rejected||reference.clean!==reference.subs)wrong.push('Python walker did not consume every subroutine cleanly');
  if (reference.files !== measured.files) wrong.push(`files ${measured.files} vs ${reference.files}`);
  if (reference.subs !== measured.subs) wrong.push(`subs ${measured.subs} vs ${reference.subs}`);
  if (reference.instructions !== measured.instructions) wrong.push(`instructions ${measured.instructions} vs ${reference.instructions}`);
  if (reference.opcodes !== measured.opcodes) wrong.push(`opcodes ${measured.opcodes} vs ${reference.opcodes}`);
  if (measured.invalid) wrong.push(`${measured.invalid} file(s) the port's parser refused`);
  console.log(`   ${job.title}: port ${measured.files} files / ${measured.subs} subs / ${measured.instructions} ` +
    `instructions / ${measured.opcodes} opcodes   |   python ${reference.files} / ${reference.subs} / ` +
    `${reference.instructions} / ${reference.opcodes}`);
  if (wrong.length) { failures += wrong.length; for (const w of wrong) console.log(`      FAIL ${w}`); }
  else console.log(`      PASS  the port's parser and the Python walker agree on ${job.title}`);
}

// Exit through the code rather than process.exit: tearing the wasm instance down while the loop is still alive
// aborts with libuv's "UV_HANDLE_CLOSING" assertion, which would turn a passing check into a failing exit status.
process.exitCode = failures ? 1 : 0;
