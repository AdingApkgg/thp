// Application previous-state2/request7 branch, 79e63..79f2f + 7a243.
// Fade ticking is a separate task. Gameplay remains registered until mode2.
export function prepareGameplayResult(fade,{practice=false}={},services={}){
 if(!fade)return 1;
 if(fade.mode===2){services.detachGameplay();const result=services.registerResult({state:practice?17:9,dirty:1,updatePriority:13,drawPriority:16});return result===0?1:4;}
 if(fade.mode===0)fade.requestOut(0,30);
 return 1;
}
