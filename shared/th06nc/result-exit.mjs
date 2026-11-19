// Result closing state 2, 6f9c5..6faaf. A finished task skips the common
// ANM/time tail; the supervisor's ordinary destination is game state 1.
export function advanceResultExit({v},fade){
 if(v.getInt32(0x9e94,true)!==2)throw Error('TH06nc result: closing state required');
 const standalone=Boolean(v.getUint8(0x9e9a));
 if(!v.getUint8(0x9e98)){v.setUint8(0x9e98,1);fade?.requestOut(standalone?0:0xffffff,standalone?10:30);}
 if(!fade||fade.mode!==2)return null;
 if(!standalone&&v.getUint32(0x4450,true)<30)return null;
 return {kind:standalone?'closeResult':'returnTitle'};
}
