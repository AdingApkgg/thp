import{InteractivePersistentCpuSessionV120}from'./InteractivePersistentCpuSessionV120.mjs';
export class InteractivePersistentCpuSessionV121 extends InteractivePersistentCpuSessionV120{
 async step(){
  const result=await super.step();
  if(this.phase==='game'){
   const c=this.runtime,p=c.boot_region(0x4e47d0,0xa34),v=new DataView(c.memory.buffer);
   if(p&&v.getUint32(p+0x6e8,true)===4&&v.getUint32(p+0x6ec,true)===4&&c.natural_return_diagnostic(16)===0&&c.natural_return_diagnostic(6)===7){
    const dispatch=c.title_second_start_frame;
    this.runtime={...c,campaign_title_input_frame:keys=>dispatch(keys,1,0,1,0,1)};
    this.phase='title';this.returnedTitleRuntime=true;
   }
  }
  return result;
 }
}
