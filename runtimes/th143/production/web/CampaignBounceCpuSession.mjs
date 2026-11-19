import {CampaignCpuSession} from './CampaignCpuSession.mjs';
export class CampaignBounceCpuSession extends CampaignCpuSession {
 async cpuSnapshot(frame){const s=await super.cpuSnapshot(frame),c=this.runtime;s.variableTweenStates=[];
  const hex=b=>Array.from(b,v=>v.toString(16).padStart(2,'0')).join('');
  for(let i=0;i<c.title_root_start_actor_count();++i)for(let k=0;k<c.title_root_start_context_count(i);++k){const p=c.title_context_scalar_data(i,k);if(!p)throw Error('Missing VM scalar state');const origins=[];for(let j=0;j<8;++j){const q=c.title_context_scalar_origin(i,k,j);origins.push(q?hex(this.bytes(q,new DataView(c.memory.buffer).getUint16(q+6,true))):null);}s.variableTweenStates.push({actor:i,context:k,scalars:hex(this.bytes(p,384)),origins});}return s;
 }
}
