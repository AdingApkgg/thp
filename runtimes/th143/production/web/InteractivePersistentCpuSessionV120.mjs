import{InteractivePersistentCpuSessionV119}from'./InteractivePersistentCpuSessionV119.mjs';
export class InteractivePersistentCpuSessionV120 extends InteractivePersistentCpuSessionV119{
 refreshHostClock(){
  const now=performance.now();
  this.hostClockMilliseconds??=10000;
  if(this.hostClockLast!==undefined&&!this.hostClockPaused)this.hostClockMilliseconds+=Math.max(0,now-this.hostClockLast);
  this.hostClockLast=now;
  this.runtime?.campaign_host_clock_set?.(Math.floor(this.hostClockMilliseconds)>>>0);
 }
 setHostClockPaused(paused){this.refreshHostClock();this.hostClockPaused=!!paused;}
 consumeCalls(){this.refreshHostClock();return super.consumeCalls();}
 async loadFirstRoot(){this.refreshHostClock();return super.loadFirstRoot();}
 async loadReplayRoot(){this.refreshHostClock();return super.loadReplayRoot();}
 async step(){this.refreshHostClock();return super.step();}
 closeForPage(){this.refreshHostClock();return super.closeForPage();}
}
