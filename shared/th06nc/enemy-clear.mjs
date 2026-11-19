// ECL 96, original 28574..285df. Clear eligible life fields first; only
// non-collidable actors jump straight to their configured death subroutine.
export function clearOrdinaryEnemies(pool){
 for(const entry of pool.entries){if(!entry)continue;const {v,dispatch}=entry,flags=v.getUint8(0xbd);if(!(v.getUint8(0xbc)&128)||(flags&8))continue;v.setInt32(0x234,0,true);if(flags&1)continue;const sub=v.getInt32(0xbe0,true);if(sub<0)continue;const id=(sub<<16)>>16,target=pool.program.subroutines[id];if(!target)throw Error('TH06nc ECL: invalid cleared enemy death subroutine');dispatch.pointer(target.offset);v.setInt32(0x44,0,true);v.setInt32(0x40,-999,true);v.setInt16(0x80,id,true);v.setInt32(0xbe0,-1,true);}
}
