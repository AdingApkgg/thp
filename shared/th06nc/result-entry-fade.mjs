// Result task initialization 73d75..73dcf. Practice Result17 has its own
// entry path. This block retains the existing color and current alpha.
export function initializeResultEntryFade(fade,{state=9,standalone=false}={}){
 if(state===17||state!==9&&!standalone||fade?.mode!==2)return;
 const v=fade.v;v.setInt32(0,standalone?10:30,true);v.setInt32(0x2c,255,true);v.setInt32(8,0,true);v.setInt32(4,-999,true);v.setInt32(0x34,3,true);
}
