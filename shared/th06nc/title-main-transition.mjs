// State-3 input decision phase, native 0x14004832d..0x1400487d3.
// Destination owners consume the resulting state; this does not implement them.
export function transitionTitleMain(initial,keys,{extraAvailable=false}={}){
 const state={...initial},effects=[];
 let interrupt=null;
 if(state.frame<20)return {state,effects,interrupt};
 const edge=bit=>(keys.held&bit)!==0&&(keys.previous&bit)!==(keys.held&bit);
 const fade=()=>effects.push({kind:'fade',mode:0,frames:45});
 const sound=id=>effects.push({kind:'sound',id});
 if(edge(0x100)){
  const item=state.selection;
  if(item===1&&!extraAvailable)sound(11);
  else if(item>=0&&item<=9){
   if(item===8){state.state=4;state.frame=0;state.pulse=0;state.selection=0;interrupt=3;sound(10);}
   else {
    interrupt=4;state.frame=0;
    if(item===0||item===1||item===2){
     state.state=8;state.practice=item===2?1:0;state.spell=0;
     if(item===1)state.difficulty=4;
     else {
      if(state.difficulty>=4)state.difficulty=1;
      if(state.configuredDifficulty>=4)state.configuredDifficulty=1;
     }
    }else if(item===3){state.spell=1;state.practice=0;state.state=27;}
    else if(item===4){state.state=15;state.practice=0;}
    else state.state=({5:12,6:21,7:23,9:5})[item];
    fade();sound(item===9?11:10);
   }
  }
 }
 if(edge(0x800)){state.state=5;state.frame=0;interrupt=4;fade();sound(11);}
 if(edge(0x200)){state.selection=9;sound(11);}
 return {state,effects,interrupt};
}
