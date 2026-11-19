import{InteractivePersistentCpuSessionV98}from'./InteractivePersistentCpuSessionV98.mjs';
export class InteractivePersistentCpuSessionV99 extends InteractivePersistentCpuSessionV98 {
 disposeForExit(){if(this.phase==='closed'&&!this.deviceDisposedForExit){this.device.dispose();this.deviceDisposedForExit=true;}}
 async step(){const result=await super.step();this.disposeForExit();return result;}
 closeForPage(){try{return super.closeForPage();}finally{this.disposeForExit();}}
}
