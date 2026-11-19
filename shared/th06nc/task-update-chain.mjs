// Update-chain runner 3be80. Nodes retain native previous/next semantics;
// task removal/destruction and sound transport are explicit caller services.
export function runUpdateChain(head,{status,remove,consumeSounds=()=>{},maxInvocations=100000}={}){
 let node=head,executed=0,invocations=0;
 while(node){
  if(node.update){
   if(++invocations>maxInvocations)throw Error('TH06nc task chain: invocation limit exceeded');
   const code=node.update(node.context)|0;
   if(code===2)continue;
   if(code===6){node=head;continue;}
   if(code===0){const old=node;node=node.next;remove(old);executed=(executed+1)|0;continue;}
   if(code===3){consumeSounds();return {value:0,executed};}
   if(code===4||code===5){consumeSounds();status.value=code===4?1:2;return {value:1,executed};}
   executed=(executed+1)|0;
  }
  node=node.next;
 }
 consumeSounds();if(executed===0||executed===-1){status.value=executed===0?1:2;return {value:1,executed};}
 return {value:0,executed};
}
