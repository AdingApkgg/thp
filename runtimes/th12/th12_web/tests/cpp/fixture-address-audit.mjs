// Which raw addresses in a fixture file are source addresses - and what they map to.
//
// The fixtures are th11-shaped: the shipped tables map a source address to the target image's
// address, and `touch()` is the mapping. A fixture that writes the NATIVE side (the oracle's
// machine, `m.*`) must write the mapped address, while the same literal written through the
// CORE side's accessors belongs to the port's own (source) naming. A literal written raw into
// the native machine is the one class of mistake that fails quietly: the game reads the mapped
// address, finds zero, and dies somewhere unrelated - which is what section 73 records for
// enemy-animations.test.mjs and dialogue.test.mjs.
//
//   node fixture-address-audit.mjs enemy-animations.test.mjs [--all]
import {readFileSync} from 'node:fs';
import {touch} from './fixture-addresses.mjs';
const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const files=process.argv.slice(2).filter(a=>!a.startsWith('--'));
const showAll=process.argv.includes('--all');
let mapped=0;
for(const file of files){
  const text=readFileSync(file,'utf8');
  const literals=[...new Set([...text.matchAll(/0x4[0-9a-fA-F]{5}/g)].map(m=>m[0].toLowerCase()))];
  const rows=literals.map(literal=>{
    const value=Number(literal),target=touch(value);
    return {literal,address:hex(value),target:hex(target),mapped:target!==value,
      uses:(text.match(new RegExp(literal.slice(2),'gi'))??[]).length};
  }).filter(row=>showAll||row.mapped).sort((a,b)=>a.address.localeCompare(b.address));
  console.log(`${file}: ${rows.filter(r=>r.mapped).length} mapped literal(s) of ${literals.length}`);
  for(const row of rows){
    if(row.mapped)++mapped;
    console.log('  %s x%d%s',row.literal,row.uses,row.mapped?` -> ${row.target}`:'  (source == target)');
  }
}
console.log(`total mapped: ${mapped}`);
