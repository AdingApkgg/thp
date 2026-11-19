const F=Math.fround;
// FPS aggregation 3c66e..3c6da. FPS measurement is a platform clock input;
// the stored numerator/denominator remain native float32 accumulators.
export function accumulateRuntimeSpeed(state,fps,{active=true}={}){
 if(!active)return;
 state.denominator=F(F(state.denominator)+F(60));
 const weight=fps>54?60:fps>42?48:fps>30?36:30;
 state.numerator=F(F(state.numerator)+F(weight));
}
export class RuntimeSpeed {
 constructor(){this.numerator=0;this.denominator=0;this.frames=0;this.previousTime=null;}
 reset(){this.numerator=0;this.denominator=0;}
 sample(microseconds,active){
  if(this.previousTime===null)this.previousTime=microseconds;
  this.frames=(this.frames+1)|0;const elapsed=microseconds-this.previousTime;
  if(elapsed<500000)return;
  const fps=this.frames*1000000/elapsed;this.previousTime=microseconds;this.frames=0;accumulateRuntimeSpeed(this,fps,{active});
 }
}
