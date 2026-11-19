import{InteractivePersistentCpuSessionV114}from'./InteractivePersistentCpuSessionV114.mjs';
export class InteractivePersistentCpuSessionV115 extends InteractivePersistentCpuSessionV114{
 async step(){const result=await super.step();if(this.phase==='game'){const c=this.runtime,p=c.boot_region(0x4e47d0,0xa34),v=new DataView(c.memory.buffer),state=c.natural_return_diagnostic(6);if(p&&v.getUint32(p+0x6e8,true)===4&&v.getUint32(p+0x6ec,true)===4&&c.natural_return_diagnostic(16)===0&&(state===1||state===11))this.phase='title';}return result;}
}
