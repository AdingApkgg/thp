// Can this engine run a function where it lives? A cross-title fixture needs to know, and the answer
// is per title and per address, and per process.
//
//   node trace-oracle-call.mjs 0x454190 0x40 in-place
//   node trace-oracle-call.mjs 0x454190 0x40 relocated
//
// One wasm-side trap leaves the engine such that every later call in the same process fails the same
// way: measured on a fresh machine with seven ordered calls, a first memset succeeded, th12's own
// template initialiser then trapped, and after that the same memset trapped too, and not even
// resetThreadFPU healed it. A second machine built later in the same process is poisoned as well, so
// one measurement per process is the rule this tool follows.
import {oracle} from './helpers.mjs';
const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const address=Number(process.argv[2]??0x454190),length=Number(process.argv[3]??0x40);
const mode=process.argv[4]??'in-place';
const m=await oracle(),U=m.uc,object=m.allocate(0x800);
let entry=address;
if(mode!=='in-place'){
  entry=m.allocate(length+16);
  const body=Buffer.from(m.bytes(address,length));
  for(let index=0;index+5<=body.length;index++)
    if(body[index]===0xe8||body[index]===0xe9){
      const target=address+index+5+body.readInt32LE(index+1);
      body.writeInt32LE((target-(entry+index+5))|0,index+1);
    }
  m.write(entry,body);
}
const trace=[];
const hook=m.cpu.hook_add(U.HOOK_CODE,(cpu,at)=>{if(trace.length<64)trace.push(Number(at)>>>0);},
                          null,entry,entry+length+16);
let verdict;
try{m.reg('ESI',object);m.call(entry);verdict='ok';}
catch(error){verdict=String(error.message??error).split('\n')[0].slice(0,58);}
try{m.cpu.hook_del(hook);}catch{/* a trapped engine cannot even delete a hook */}
console.log('  '+mode.padEnd(9)+' '+hex(address)+' -> '+hex(entry)+'): '+verdict);
console.log('    bytes: '+Buffer.from(m.bytes(address,length>12?12:length)).toString('hex'));
console.log('    first='+trace.slice(0,3).map(hex).join(',')+' last='+trace.slice(-3).map(hex).join(',')+
  '  ('+trace.length+' seen)');
