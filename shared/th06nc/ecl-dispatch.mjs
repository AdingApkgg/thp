import {applyEclCommand,supportedEclCommands,serviceEclCommands} from './ecl-command.mjs';
const commands=new Set([...supportedEclCommands,...serviceEclCommands]);
const compare=(op,x,y)=>[x<y,x<=y,x===y,x>y,x>=y,x!==y][op];
// Script phase only, 0x140022170..0x140028840; enemy motion runs afterwards.
export class EclDispatch {
 constructor(program,enemy,services){
  this.program=program;this.enemy=enemy;this.v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);this.services=services;
  this.instructions=new Map(program.subroutines.flatMap(s=>[...s.instructions,{offset:s.end-12,time:-1,opcode:-1,length:12,difficultyMask:0,args:new Uint8Array()}]).map(i=>[i.offset,i]));
 }
 pointer(value){if(value!==undefined)this.v.setBigUint64(0x88,BigInt(value),true);return Number(this.v.getBigUint64(0x88,true));}
 start(sub=0,{integer=0,floatBits=0}={}){
  const entry=this.program.subroutines[sub];if(!entry)throw Error('TH06nc ECL: invalid entry subroutine');
  this.v.setInt32(0x40,-999,true);this.v.setInt32(0x44,0,true);this.v.setInt16(0x80,sub,true);this.pointer(entry.offset);
  this.v.setInt32(0x48,integer,true);this.v.setUint32(0x58,floatBits,true);this.v.setInt32(0x240,0,true);this.v.setInt32(0xf70,-1,true);
 }
 call(sub,next,{integer,floatBits,interrupt=false}={}){
  sub=(sub<<16)>>16;const entry=this.program.subroutines[sub];if(!entry)throw Error('TH06nc ECL: invalid called subroutine');
  const v=this.v,depth=v.getInt32(0x240,true),noStack=Boolean(v.getUint8(0xbe)&4);this.pointer(next);
  if(!noStack){if(depth<0||depth>7)throw Error('TH06nc ECL: invalid stack depth');this.enemy.copyWithin(0xc68+depth*96,0x40,0xa0);}
  this.pointer(entry.offset);v.setInt32(0x44,0,true);v.setInt32(0x40,-999,true);v.setInt16(0x80,sub,true);
  if((!noStack||interrupt)&&depth<7)v.setInt32(0x240,depth+1,true);
  if(integer!==undefined)v.setUint32(0x48,integer,true);if(floatBits!==undefined)v.setUint32(0x58,floatBits,true);
  return entry.offset;
 }
 runDue({budget=100000,beforeInstruction=null}={}){
  const v=this.v;let pc=this.pointer(),executed=0,checkPending=true;
  for(;;){
   if(executed>=budget)throw Error('TH06nc ECL: script instruction budget exceeded');
   const pending=v.getInt32(0xf70,true);
   if(checkPending&&pending>=0){pc=this.call(v.getInt16(8+pending*4,true),pc+(this.instructions.get(pc)?.length??0),{interrupt:true});v.setInt32(0xf70,-1,true);}
   checkPending=false;
   const ins=this.instructions.get(pc);if(!ins)throw Error(`TH06nc ECL: invalid script offset ${pc}`);
   if(v.getInt32(0x44,true)!==ins.time)return {nextOffset:pc,deleted:false,executed};
   if(beforeInstruction?.(ins)===false)return {nextOffset:pc,deleted:false,executed,debugStopped:true};
   if(!(ins.difficultyMask&(1<<(this.services.operands.environment.difficulty&31)))){pc+=ins.length;continue;}
   executed++;const a=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength),i=p=>a.getInt32(p,true),u=p=>a.getUint32(p,true),op=ins.opcode;
   let jump=op===2;
   if(op===1)return {nextOffset:pc,deleted:true,executed};
   if(op===3){const value=(this.services.operands.integer(u(8))-1)|0;this.services.operands.assign(i(8),value);jump=value>0;}
   if(op>=29&&op<=34)jump=compare(op-29,v.getInt32(0x90,true),0);
   if(jump){v.setInt32(0x44,i(0),true);pc+=i(4);continue;}
   if(op===110){pc=this.call(v.getInt16(8+i(0)*4,true),pc+ins.length,{interrupt:true});v.setInt32(0xf70,-1,true);checkPending=true;continue;}
   if(op===35||(op>=37&&op<=42&&compare(op-37,this.services.operands.integer(u(12)),i(16)))){
    pc=this.call(i(0),pc+ins.length,{integer:u(4),floatBits:u(8)});checkPending=true;continue;
   }
   if(op===36){
    const depth=v.getInt32(0x240,true);if(depth<1||depth>7)throw Error('TH06nc ECL: return outside call stack');
    v.setInt32(0x240,depth-1,true);this.enemy.copyWithin(0x40,0xc08+depth*96,0xc68+depth*96);pc=this.pointer();checkPending=true;continue;
   }
   if(commands.has(op))Object.assign(this.services,applyEclCommand(this.enemy,ins,this.services));
   else if(!([2,3].includes(op)||(op>=29&&op<=34)||(op>=37&&op<=42)||(op>=136&&op<=199)||op<1||op>201))throw Error(`TH06nc ECL: opcode ${op} at ${pc} not implemented`);
   pc+=ins.length;
  }
 }
 commitAfterEnemyFrame(result){if(!result.deleted){this.pointer(result.nextOffset);this.v.setInt32(0x40,this.v.getInt32(0x44,true),true);this.v.setInt32(0x44,(this.v.getInt32(0x44,true)+1)|0,true);}}
}
