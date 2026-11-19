const F=Math.fround;
// Shared 16-bit generator observed in the original ANM/ECL implementations.
export class NativeRng {
 constructor(seed=0,count=0){this.seed=seed&65535;this.count=count>>>0;}
 next16(){let x=((this.seed^0x9630)-0x6553)&65535;x=((x<<2)|(x>>>14))&65535;this.seed=x;this.count=(this.count+1)>>>0;return x;}
 next32(){return ((this.next16()<<16)|this.next16())>>>0;}
 float01(){return F(F(this.next32())*F(2**-32));}
 angle(){return F(F(this.float01()*F(2*Math.PI))-F(Math.PI));}
}
