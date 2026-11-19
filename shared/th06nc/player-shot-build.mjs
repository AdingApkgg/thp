import {playerShotPrograms} from './player-shot-programs.mjs';
import {rebindAnm} from './anm-rebind.mjs';
const F=Math.fround;
const programs=playerShotPrograms.map(rows=>rows.map(row=>({powerBelow:row.powerBelow,records:row.records.map(hex=>{const b=Uint8Array.from({length:36},(_,i)=>parseInt(hex.slice(i*2,i*2+2),16));return new DataView(b.buffer);})})));
export function playerShotBand(character,shot,power){const program=programs[character*2+shot],band=program?.find(row=>(power&65535)<row.powerBelow);if(!band)throw Error('TH06nc: invalid player shot profile/power');return band;}
// Original generic constructor 6a580. The owner activates slots separately.
export function buildPlayerShot(player,slot,index,clock,{soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos}={}){
 const {bytes,v,environment={},anmBank,anms}=player,band=playerShotBand(environment.character??0,environment.shot??0,environment.playerPower??0),record=band.records[index];
 if(!record||slot<0||slot>=80)throw Error('TH06nc: invalid player shot record/slot');
 const base=0x410+slot*0x170,d=new DataView(bytes.buffer,bytes.byteOffset+base,0x170),kind=record.getUint8(0x1f),last=index>=band.records.length-1;
 const failed=()=>last?-2:-1,put=(target,source)=>d.setUint32(target,record.getUint32(source,true),true);
 if(kind===3){const channel=record.getInt16(2,true),timer=0x79e8+channel*8;if(v.getInt32(timer+4,true)!==0)return failed();v.setInt32(timer+4,record.getInt16(0,true),true);v.setInt32(timer,-999,true);d.setInt16(0x138,channel,true);d.setInt16(0x14c,record.getUint8(0x1e),true);put(0x148,4);put(0x150,8);}
 else{const period=record.getInt16(0,true);if(period===0)throw Error('TH06nc: zero player shot period');if((clock|0)%period!==record.getInt16(2,true))return failed();}
 const vmOffset=base+0x18,vm=rebindAnm(anmBank,record.getInt16(0x20,true),bytes.subarray(vmOffset,vmOffset+288),{randomU16:environment.rng?()=>environment.rng.next16():null});anms.set(vmOffset,vm);
 const origin=record.getUint8(0x1e),source=origin===0?0x7730:0x7874+origin*12;
 for(let k=0;k<3;k++)d.setUint32(0x13c+k*4,v.getUint32(source+k*4,true),true);
 d.setFloat32(0x13c,F(record.getFloat32(4,true)+d.getFloat32(0x13c,true)),true);d.setFloat32(0x140,F(record.getFloat32(8,true)+d.getFloat32(0x140,true)),true);d.setFloat32(0x144,F(0.495),true);
 for(const [to,from]of [[0x160,0xc],[0x164,0x10],[0x158,0x14],[0x154,0x18]])put(to,from);d.setFloat32(0x168,1,true);
 const angle=record.getFloat32(0x14,true),speed=record.getFloat32(0x18,true);d.setFloat32(8,F(F(cos(angle))*speed),true);d.setFloat32(0xc,F(F(sin(angle))*speed),true);d.setInt32(4,0,true);d.setInt32(0,-999,true);d.setUint16(0x12,kind,true);d.setUint16(0x15c,record.getUint16(0x1c,true),true);
 const sound=record.getInt16(0x22,true);if(sound>=0&&!soundDisabled&&!soundSlots.includes(sound)){const i=soundSlots.findIndex(x=>x<0);if(i>=0)soundSlots[i]=sound;}
 return last?1:0;
}
