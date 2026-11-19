const F=Math.fround,U=n=>BigInt.asUintN(64,BigInt(n??0));
// Numeric requests and refresh-counter retirement, 413c0..415b2.
export function drawHudNumbers(drawNumber,{displayScore=0n,highScore=0n,totalGraze=0,pointStageCount=0,inputFlags=0,force=false}={}){
 const score=(value,y)=>{value=U(value);let width=F(0),threshold=1000000000n;while(threshold<=value){threshold=U(threshold*10n);width=F(width+F(12));if(threshold===0n)throw Error('TH06nc HUD: score alignment overflow');}drawNumber({format:'%.9llu',value:String(value),text:String(value).padStart(9,'0'),position:[F(F(723)-width),y,0]});};
 score(displayScore,78);score(highScore,53);
 if((inputFlags&0xc0)||force){const value=totalGraze|0;drawNumber({format:'%d',value:String(value),text:String(value),position:[723,207,0]});}
 if((inputFlags&0x300)||force){const value=pointStageCount&65535;drawNumber({format:'%d',value:String(value),text:String(value),position:[723,232,0]});}
 for(const shift of [0,4,2,6,8]){const count=(inputFlags>>>shift)&3;if(count)inputFlags=(inputFlags&~(3<<shift))|((count-1)<<shift);}
 return inputFlags>>>0;
}
