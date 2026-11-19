import{InteractivePersistentCpuSessionV109}from'./InteractivePersistentCpuSessionV109.mjs';
import{SessionDevice}from'./SessionDeviceWindowDepthV114.mjs';
export class InteractivePersistentCpuSessionV114 extends InteractivePersistentCpuSessionV109{
 constructor(...args){super(...args);this.device.dispose();this.device=new SessionDevice(args[0]);const dispatch=this.device.dispatch.bind(this.device);this.device.dispatch=(op,args,bytes)=>op===16&&!args.length?1:dispatch(op,args,bytes);}
}
