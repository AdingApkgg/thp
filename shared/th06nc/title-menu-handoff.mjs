// Title destination owners 4c198..4c21c require frame >= 50.
// Quit additionally waits for the active fade owner to reach mode 2.
export function titleMenuHandoff(state,frame,fade=null){
 if(frame<50)return null;
 if(state===5)return fade?.mode===2?{kind:'quitGame',gameState:4}:null;
 return ({12:{kind:'openScore',gameState:6},21:{kind:'openMusicRoom',gameState:9},23:{kind:'openCredits',gameState:11}})[state]??null;
}
