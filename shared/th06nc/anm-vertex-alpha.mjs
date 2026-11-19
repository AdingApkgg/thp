// 319d..31e1: 2a80's top/bottom vertex alpha, rounded in byte space.
export function anmVertexAlphas(color,topAlpha=255,bottomAlpha=255){
 const alpha=color>>>24,apply=value=>Math.floor((Math.imul(alpha,value&255)+127)/255);
 return [apply(topAlpha),apply(bottomAlpha)];
}
