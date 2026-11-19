// Result dispatcher states 15/16, 726c6..72743. Common ANM/time updates
// remain with advanceResultCommon; state 10 belongs to replay selection.
export function advanceResultSummary({v},{held=0,previous=0}={}){
 const state=v.getInt32(0x9e94,true),clock=v.getInt32(0x4450,true);
 if(state===15){
  if(clock<=30)v.setInt16(0x2ada,16,true);
  else if(clock>=90&&(held&256)!==(previous&256)&&(held&256)){
   v.setInt16(0x2ada,2,true);v.setInt32(0x9e94,16,true);v.setInt32(0x4450,0,true);
  }
 }else if(state===16){
  if(clock>=30){v.setInt32(0x4450,59,true);v.setInt32(0x9e94,10,true);}
 }else throw Error('TH06nc result: summary state required');
}
