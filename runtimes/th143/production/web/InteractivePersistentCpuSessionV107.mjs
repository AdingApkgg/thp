import{InteractivePersistentCpuSessionV103}from'./InteractivePersistentCpuSessionV103.mjs';
import{SessionDevice}from'./SessionDeviceWindowDepthBatchedV1.mjs';
export class InteractivePersistentCpuSessionV107 extends InteractivePersistentCpuSessionV103{
 constructor(...args){super(...args);this.device.dispose();this.device=new SessionDevice(args[0]);const dispatch=this.device.dispatch.bind(this.device);this.device.dispatch=(op,args,bytes)=>op===16&&!args.length?1:dispatch(op,args,bytes);}
 consumeCalls(){this.device.beginErrorBatch();try{const result=super.consumeCalls();this.device.endErrorBatch();return result;}catch(error){if(this.device.errorBatchDepth)try{this.device.endErrorBatch();}catch{}throw error;}}
}
