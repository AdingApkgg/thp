// One substitution site, one question: does the address it binds name the machine it is binding?
//
// machine.mjs's replace(address,name,handler) writes a five-byte jump at `address` and does NOT
// translate it (section 76). The fixtures are th11-shaped - they name the addresses of the title
// the port started from - and fixture-addresses.mjs exists for exactly that, so a `m.replace` site
// is correct only when its literal is the address the table maps it to, i.e. `touch(address) ===
// address` for a target-namespace literal, or the site passes `touch(0x...)` itself.
//
// m.call(0x...) is the same question with a stronger consequence: a raw literal that the table maps
// elsewhere calls whatever function happens to live there in the target image. Section 298 measured
// it - anm-resource died at pc=0x454190 with EAX=0 reading [0x0] at native call 7, and 0x454190 is a
// row whose target is 0x45fc90.
//
// Usage: node replace-site-audit.mjs [--all]
//   default: only the sites whose literal the table maps elsewhere (the misplaced ones)
//   --all:   every site, with the verdict for each
//
// Section 300's rule, learned by breaking anm-load-all with it: a `*.test.mjs` suite is th11-shaped
// and its literals must be translated, while a support file (helpers.mjs, world-oracle.mjs,
// engine-block-standin.mjs, the shared fixtures) is target-namespace BY CONSTRUCTION - its CRT
// bootstrap and OS substitutes were transcribed from th12's own entry point. The two are reported
// separately, because "misplaced" means different things in each: in a suite it is a defect, in a
// support file it is the design, and a translator that cannot tell them apart redraws the harness.
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {touch} from './fixture-addresses.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const files=readdirSync(here).filter(name=>name.endsWith('.mjs'));
const kinds={replace:/m\.replace\(([^,]+),/g,call:/m\.call\(([^,)]+)[,)]/g};
const rows=[];
for(const file of files){
  const text=readFileSync(resolve(here,file),'utf8').split('\n');
  text.forEach((line,index)=>{
    for(const [kind,pattern] of Object.entries(kinds)){
      for(const match of line.matchAll(pattern)){
        const argument=match[1].trim();
        const literal=/^0x([0-9a-fA-F]+)$/.exec(argument);
        if(!literal)continue;                      // touch(0x...) and computed addresses are fine
        const address=parseInt(literal[1],16);
        const translated=touch(address)>>>0;
        if(translated===address)continue;          // target namespace, or no row claims it
        rows.push({file,line:index+1,kind,address,translated,ok:false,
                   suite:file.endsWith('.test.mjs'),text:line.trim().slice(0,72)});
      }
    }
  });
}
const suites=rows.filter(row=>row.suite), support=rows.filter(row=>!row.suite);
for(const kind of Object.keys(kinds)){
  console.log(`  ${suites.filter(row=>row.kind===kind).length} ${kind} sites in suites name an address the table maps elsewhere`);
  console.log(`  ${support.filter(row=>row.kind===kind).length} ${kind} support-file sites name such an address (target-namespace by construction, left raw on purpose)`);
}
const all=process.argv.includes('--all');
for(const row of rows){
  console.log(`    ${row.suite?'suite':'support'}  ${row.file}:${row.line}  ${row.kind}  0x${row.address.toString(16)} -> 0x${row.translated.toString(16)}`);
  if(all)console.log(`        ${row.text}`);
}
