// The census: every suite run with node --test, its pass/fail counts and the wall it stopped at.
//
// This is the instrument the port's verdict is read from - "did that change help" and "where does each suite
// stop now" - and until round 330 it lived in tools/tmp, which is gitignored, so no committed state could
// reproduce the numbers a round reported. It is promoted here with the --leaks switch of section 109, which
// asks the machine for its per-process sentinel line (section 106) and aggregates what the runner captures.
// Section 84 is the repair that made the census worth running; section 306 is where this loop was written.
//
// Round 306: the census the section 84 repair makes worth running.
//
// Ninety-one suites were rewritten, so "did that help" is a question with a measurable answer, and so
// is "where does each suite stop now". Every suite is run with node --test, its pass/fail counts are
// parsed, and the trap artifact its wrapper leaves behind is read for the address and kind of the
// first wall. The whole table goes to JSON and the summary groups the walls, so the next target is
// chosen by frequency rather than by whichever suite was looked at last.
import {spawnSync} from 'node:child_process';
import {readdirSync,readFileSync,writeFileSync,rmSync,existsSync,statSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';

const cpp=fileURLToPath(new URL('../runtimes/th12/th12_web/tests/cpp/',import.meta.url));
const artifacts=fileURLToPath(new URL('../runtimes/th12/th12_web/artifacts/cpp/verification/',import.meta.url));
const node=process.execPath;
const limit=process.argv.includes('--limit')?Number(process.argv[process.argv.indexOf('--limit')+1]):0;
const pattern=process.argv.includes('--filter')?process.argv[process.argv.indexOf('--filter')+1]:null;

// Round 330: the machine can report its sentinel leaks per process (section 106), but this runner captures
// each suite's stdout and only parsed the pass/fail counts, so the report was discarded rather than absent.
// A `--leaks` run asks the machine for the line and reads it out of the same captured output, so the
// corpus-wide fidelity figure comes from the census rather than from a handful of suites run by hand.
const wantLeaks=process.argv.includes('--leaks');
const clear=()=>{if(existsSync(artifacts))for(const name of readdirSync(artifacts))
  if(name.startsWith('trap-'))rmSync(join(artifacts,name),{force:true});};
const newestTrap=()=>{
  if(!existsSync(artifacts))return null;
  const files=readdirSync(artifacts).filter(n=>n.startsWith('trap-'));
  if(!files.length)return null;
  files.sort((a,b)=>statSync(join(artifacts,b)).mtimeMs-statSync(join(artifacts,a)).mtimeMs);
  try{return JSON.parse(readFileSync(join(artifacts,files[0]),'utf8'));}catch{return null;}
};

let suites=readdirSync(cpp).filter(n=>n.endsWith('.test.mjs')).sort();
if(pattern)suites=suites.filter(n=>n.includes(pattern));
if(limit)suites=suites.slice(0,limit);

const rows=[];
for(const suite of suites){
  clear();
  const started=Date.now();
  const run=spawnSync(node,['--test',suite],{cwd:cpp,encoding:'utf8',maxBuffer:64*1024*1024,
    ...(wantLeaks?{env:{...process.env,TH_SENTINEL_REPORT:'1'}}:{})});
  const out=(run.stdout||'')+(run.stderr||'');
  const leakMatch=[...out.matchAll(/sentinel-leaks (\d+)\s+scrubbed (\d+)\s+interior-applied (\d+)\s+framed (\d+)/g)];
  const leaks=leakMatch.length?{leaks:leakMatch.reduce((n,m)=>n+Number(m[1]),0),
    scrubbed:leakMatch.reduce((n,m)=>n+Number(m[2]),0),processes:leakMatch.length}:null;
  const count=kind=>{const m=[...out.matchAll(new RegExp('ℹ '+kind+' (\\d+)','g'))];return m.length?Number(m[m.length-1][1]):null;};
  const trap=newestTrap();
  const recent=trap&&Array.isArray(trap.recent)&&trap.recent.length?trap.recent[trap.recent.length-1]:null;
  const message=(out.match(/(?:AssertionError|Error|ReferenceError|TypeError)[^\n]*/)||[''])[0].trim();
  // Section 112: the call context comes from the payload the wrapper prints, not from `target`, which is the
  // title metadata. Both groups are optional: a suite that never reaches a call prints neither, and that is
  // recorded as null rather than as zero.
  const entryMatch=out.match(/"entry": *"(0x[0-9a-f]+)"/);
  const callsMatch=out.match(/"calls": *(\d+)/);
  // Section 133: a trap artifact can be STALE. th12-aim-angle passed with a wall attributed to it, so a row
  // records the process exit code, and only a non-zero exit can own a wall; a wall seen in a row that did not
  // fail is counted separately rather than folded into the headline.
  const wall=recent?{at:recent.at,address:recent.address,pc:recent.pc,size:recent.size}:null;
  const wallCounted=!!(wall&&run.status!==0);
  rows.push({suite,pass:count('pass'),fail:count('fail'),code:run.status,ms:Date.now()-started,
    wall,wallCounted,
    entry:entryMatch?entryMatch[1]:null,
    calls:callsMatch?Number(callsMatch[1]):null,
    message:message.slice(0,200),leaks:leaks});
  const r=rows[rows.length-1];
  console.log(`  ${(r.fail===0&&r.pass>0?'PASS':'fail')}  ${suite.padEnd(34)} pass ${r.pass} fail ${r.fail}  ${r.wall?`${r.wall.at}@${r.wall.address} pc=${r.wall.pc}`:(r.message||'').slice(0,80)}`);
}

const walls={};
for(const row of rows)if(row.wallCounted){const key=`${row.wall.pc} (${row.wall.at} ${row.wall.address})`;walls[key]=(walls[key]||0)+1;}
const summary={ran:rows.length,
  passing:rows.filter(r=>r.fail===0&&r.pass>0&&r.code===0).length,
  trapping:rows.filter(r=>r.wallCounted).length,
  wallsInPassingRows:rows.filter(r=>r.wall&&!r.wallCounted).length,
  diedBeforeTests:rows.filter(r=>r.code!==0&&!r.pass&&!r.fail).length,
  totals:{pass:rows.reduce((n,r)=>n+(r.pass||0),0),fail:rows.reduce((n,r)=>n+(r.fail||0),0)},
  leaks:{reported:rows.filter(r=>r.leaks).length,total:rows.reduce((n,r)=>n+(r.leaks?.leaks||0),0),scrubbed:rows.reduce((n,r)=>n+(r.leaks?.scrubbed||0),0)},
  topWalls:Object.entries(walls).sort((a,b)=>b[1]-a[1]).slice(0,14)};
// The verdict file: a full run owns the corpus table, and a filtered run cannot take it over.
const outArg=process.argv.includes('--out')?process.argv[process.argv.indexOf('--out')+1]:null;
const outFile=outArg||(pattern||limit?'docs/porting/census-th12-filtered.json':'docs/porting/census-th12.json');
writeFileSync(resolve(fileURLToPath(new URL('../',import.meta.url)),outFile),JSON.stringify({summary,rows},null,1).replace(/\n/g,'\r\n'));
console.log(`  == ${summary.passing}/${summary.ran} passing, ${summary.trapping} trapping (walls in non-failing rows ${summary.wallsInPassingRows}), died before any test ${summary.diedBeforeTests}, ${summary.totals.pass} pass / ${summary.totals.fail} fail assertions`);
for(const [key,n] of summary.topWalls)console.log(`  wall x${n}  ${key}`);
