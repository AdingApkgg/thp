// Native metadata walk 21dc0 and query wrapper 21fb0. Calls are scanned
// structurally, not executed: difficulty applies, instruction times do not.
export function scanEclLife(program,index,{difficulty=0,depth=0,startOffset=null,visited=new Uint8Array(1024),metadata={containsSpell:false,nextThreshold:-1,nextSubroutine:-1}}={}){
 const walk=(subIndex,level,start)=>{
  if(subIndex<0||subIndex>=program.subroutines.length||subIndex>=1024||level>8||visited[subIndex])return false;
  const sub=program.subroutines[subIndex];visited[subIndex]=1;
  if(start!==null&&(start<sub.offset||start>=sub.end))return false;
  let cursor=0;if(start!==null){cursor=sub.instructions.findIndex(instruction=>instruction.offset===start);if(cursor<0){if(start===sub.end-12)return false;throw Error('TH06nc ECL life query: unaligned instruction pointer');}}
  for(;cursor<sub.instructions.length;cursor++){
   const instruction=sub.instructions[cursor];if(!(instruction.difficultyMask&(1<<difficulty)))continue;
   const opcode=instruction.opcode,arg=()=>new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength).getInt32(0,true);
   if(opcode===93)metadata.containsSpell=true;
   else if(opcode===111)return true;
   else if(opcode===113)metadata.nextThreshold=arg();
   else if(opcode===114)metadata.nextSubroutine=arg();
   else if(opcode===35||opcode>=37&&opcode<=42){if(walk(arg(),level+1,null))return true;}
  }
  return false;
 };
 return {foundLife:walk(index|0,depth|0,startOffset),metadata,visited};
}
export function queryEclLife(program,index,{difficulty=0,startOffset=null,excludeSubroutine=-1}={}){
 const visited=new Uint8Array(1024);if(excludeSubroutine>=0&&excludeSubroutine<1024)visited[excludeSubroutine]=1;
 return scanEclLife(program,index,{difficulty,startOffset,visited}).metadata;
}
