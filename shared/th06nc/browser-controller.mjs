// Web-standard gamepad to the native controller packet consumed by127d0.
// Hardware/driver normalization is a platform boundary, separate from the
// native packet-to-input mask and button-configuration controller.
export function readBrowserController(pad){
 const connected=Boolean(pad?.connected&&pad.mapping==='standard'),packet=new Uint8Array(26),buttons=new Uint8Array(18);
 if(connected){
  for(const [index,code]of [[0,12],[1,13],[2,14],[3,15],[4,8],[5,9],[8,5],[9,4],[10,6],[11,7],[12,0],[13,1],[14,2],[15,3]])packet[code]=Number(Boolean(pad.buttons[index]?.pressed));
  for(const [index,code]of [[6,16],[7,17]])packet[code]=Math.round(Math.max(0,Math.min(1,pad.buttons[index]?.value??0))*255);
  const v=new DataView(packet.buffer),axis=index=>Math.max(-1,Math.min(1,Number.isFinite(pad.axes[index])?pad.axes[index]:0)),encode=value=>Math.round(value*(value<0?32768:32767));for(let i=0;i<4;i++)v.setInt16(18+i*2,encode(axis(i)*(i%2?-1:1)),true);
  buttons.set(packet.subarray(0,16));buttons[16]=Number(packet[16]>=30);buttons[17]=Number(packet[17]>=30);
 }
 return {connected,packet,buttons};
}
