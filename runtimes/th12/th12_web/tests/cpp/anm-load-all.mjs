// Every shipped animation file through the original's own loader, and the suite's helper for one.
//
// The ANM loader chain (sections 71 and 72) is the gate in front of most of the fixture suite, so
// the cheapest regression is a load of every reference asset, counting verdicts. One call per file
// in a single process is sound as long as none of them traps: a wasm-side trap poisons later calls
// in the process (section 67), which this file reports separately rather than hiding in a count.
//
//   node anm-load-all.mjs                 # every reference/assets/*.anm
//   node anm-load-all.mjs text.anm        # the named ones only, verdict per file
import {readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {oracle,root} from './helpers.mjs';
import {animationOracle} from './anm-oracle.mjs';
const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const assets=readdirSync(resolve(root,'reference/assets')).filter(name=>name.endsWith('.anm'));
const names=process.argv.length>2?process.argv.slice(2):assets;
const m=await oracle(),o=animationOracle(m);
const results=[];
for(const name of names){
  try{
    const loaded=o.load(name);
    results.push({name,verdict:'ok',original:hex(loaded.original),heap:hex(loaded.heap)});
  }catch(error){
    const text=String(error.message??error);
    const wasm=text.includes('memory access out of bounds');
    results.push({name,verdict:wasm?'wasm-trap':'failed',message:text.split('\n')[0],
      fault:text.split('\n').slice(1).join(' ').slice(0,160)});
    if(wasm)break;                       // a poisoned process may not be measured again
  }
}
const tally=results.reduce((counts,row)=>(counts[row.verdict]=(counts[row.verdict]??0)+1,counts),{});
console.log(JSON.stringify({assets:assets.length,requested:names.length,tally,results}));
