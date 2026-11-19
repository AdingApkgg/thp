// Life-threshold transition 37693..37793 and timeout helper 36f50.
function selectSubroutine(entry,sub){
 const {v,dispatch}=entry,id=(sub<<16)>>16,target=dispatch.program.subroutines[id];
 if(!target)throw Error('TH06nc: invalid enemy phase subroutine');
 v.setInt16(0x80,id,true);dispatch.pointer(target.offset);v.setInt32(0x44,0,true);v.setInt32(0x40,-999,true);
}
function resetRank(entry){const {v}=entry;v.setFloat32(0xa8,-0.5,true);v.setFloat32(0xac,0.5,true);v.setUint32(0xbdc,0,true);v.setUint32(0x1080,0,true);v.setInt32(0x240,0,true);}
function resetOtherEnemies(entries){
 for(const other of entries){if(!other)continue;const {v}=other;if(!(v.getUint8(0xbc)&128)||(v.getUint8(0xbd)&8))continue;
  v.setInt32(0x234,0,true);
  if(!(v.getUint8(0xbd)&1)&&v.getInt32(0xbe0,true)>=0){selectSubroutine(other,v.getInt32(0xbe0,true));v.setInt32(0xbe0,-1,true);}
 }
}
export function advanceOrdinaryEnemyPhase(entry,{entries=entry.pool?.entries??[entry],environment={},cancelBullets=null,cancelTimeoutProjectiles=cancelBullets,bossState=null}={}){
 const {v}=entry,boss=Boolean(v.getUint8(0xbd)&8);
 const threshold=v.getInt32(0xa0,true);let changed=false;
 if(threshold>=0&&v.getInt32(0x234,true)<threshold){
  v.setInt32(0x234,threshold,true);v.setInt32(0x23c,threshold,true);selectSubroutine(entry,v.getInt16(0xa4,true));
  v.setInt32(0xc58,v.getInt32(0xbe0,true),true);v.setInt32(0xa0,-1,true);v.setInt32(0xc54,-1,true);resetRank(entry);resetOtherEnemies(entries);changed=true;
 }
 const timeout=v.getInt32(0xc54,true);
 if(timeout>=0&&boss){if(!bossState)throw Error('TH06nc: boss countdown state missing');bossState.remainingSeconds=Math.trunc(((timeout-v.getInt32(4,true))|0)/60);}
 if(timeout>=0&&v.getInt32(4,true)>=timeout){
  const limit=v.getInt32(0xa0,true);if(limit>0){v.setInt32(0x234,limit,true);v.setInt32(0xa0,-1,true);}
  v.setInt32(0x23c,v.getInt32(0x234,true),true);selectSubroutine(entry,v.getInt16(0xc58,true));
  v.setInt32(0xc58,v.getInt32(0xbe0,true),true);v.setInt32(0xc54,-1,true);v.setInt32(4,0,true);v.setInt32(0,-999,true);
  if(!(v.getUint8(0xbe)&16)){
   if(!cancelTimeoutProjectiles)throw Error('TH06nc: timeout projectile cancellation service missing');
   if(environment.spellCounter)environment.spellCounter=(environment.spellCounter+1)|0;environment.spellActive=false;cancelTimeoutProjectiles();
   if(boss&&environment.spellPractice)environment.spellFinished=true;
  }
  resetOtherEnemies(entries);resetRank(entry);changed=true;
 }
 return changed;
}
