import {readFileSync,writeFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmVm} from '../shared/th06nc/anm-vm.mjs';
const manifest=JSON.parse(readFileSync('artifacts/th06nc/scripts.json'));
const cases=[];
for(const ref of manifest.filter(f=>/^title\d+\.anm$/.test(f.name))){
 const resource=readAnm(readFileSync(ref.path));
 for(const script of resource.scripts){
  const labels=script.instructions.filter(i=>i.opcode===22).map(i=>new DataView(i.args.buffer,i.args.byteOffset,i.args.byteLength).getInt32(0,true)).filter(x=>x!==-1);
  for(const variant of ['ordinary','interrupts']){
  const vm=new AnmVm(resource,script.id),initial=Buffer.from(vm.state).toString('hex'),frames=[];
  for(let tick=0;tick<360;tick++){
   let interrupt=0;
   if(variant==='interrupts'&&tick===45)interrupt=labels[0]||32760;
   if(variant==='interrupts'&&tick===120)interrupt=32760;
   if(variant==='interrupts'&&tick===180)interrupt=labels.at(-1)||32760;
   if(interrupt)vm.interrupt(interrupt);
   const result=vm.tick();frames.push({interrupt,result,state:Buffer.from(vm.state).toString('hex')});
   if(result)break;
  }
  cases.push({name:ref.name,path:ref.path,sha256:ref.sha256,id:script.id,variant,initial,frames});
  }
 }
}
writeFileSync('artifacts/th06nc/anm-vm-cases.json',JSON.stringify(cases));
console.log(`${cases.length} title script cases generated`);
