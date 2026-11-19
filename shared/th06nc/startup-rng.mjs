// Native boot7a7fe..7a812 samples the platform clock once, keeps low16 bits
// and clears the uint32 call counter. Browser/Windows clock epochs differ.
export function seedStartupRng(rng,milliseconds){
 rng.seed=(Math.trunc(milliseconds)>>>0)&65535;
 rng.count=0;
 return rng;
}
