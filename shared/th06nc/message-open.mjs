// Message owner open 3ece0, preserving HUD fields outside the native reset spans.
// Pointers 3668/38f8/3b58 use file offsets or stable resource/table handles.
export function openMessage(state,id,{environment={},cancelProjectiles,loadAnm=null}={}){
 const {bytes,v,program}=state;if(!Number.isInteger(id)||id<0)throw Error('TH06nc message: invalid script ID');if(id>=program.count)return false;
 if(!cancelProjectiles)throw Error('TH06nc message: projectile cancellation service missing');cancelProjectiles();
 bytes.fill(0,0x3420,0x36b0);bytes.fill(0,0x36b4,0x38f8);bytes.fill(0,0x3900,0x3b58);
 v.setInt32(0x36b0,id,true);v.setBigUint64(0x3668,BigInt(program.offsets[id]),true);v.setBigUint64(0x3680,0n,true);v.setUint16(0x36f0,65535,true);v.setUint16(0x3810,65535,true);
 for(const [p,value]of [[0x3424,15],[0x3670,0xffffff],[0x3674,0xfff0f0],[0x3690,0x10101],[0x3694,0x10101],[0x36a0,0x50505],[0x36a4,0x50505]])v.setUint32(p,value,true);
 v.setUint8(0x3900,1);const stage=environment.stageIndex??0,load=(file,slot,base)=>{if(!loadAnm)throw Error('TH06nc message: stage ANM service missing');loadAnm({archive:'th06ST.dat',file,slot,base});};
 if(stage===6&&(id===0||id===10))load('eff06.anm',11,0x2d3);
 else if(stage===7&&id!==2&&id!==12){load('eff07.anm',11,0x2d3);load('face12c.anm',18,0x4c6);}
 v.setUint8(0x3ec0,0);environment.messageField36b0=id;environment.messageField3b50=0;return true;
}
