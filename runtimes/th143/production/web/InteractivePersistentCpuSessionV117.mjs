import{InteractivePersistentCpuSessionV116}from'./InteractivePersistentCpuSessionV116.mjs';
export class InteractivePersistentCpuSessionV117 extends InteractivePersistentCpuSessionV116{
 async loadFirstRoot(){if(this.returnedTitleRuntime){this.phase='game';return;}return super.loadFirstRoot();}
 async step(){const before=this.phase,result=await super.step();if(before==='game'&&this.phase==='title')this.returnedTitleRuntime=true;return result;}
}
