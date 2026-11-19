import{multiplyNearestSource}from'./FloatMultiplyNearestV2.mjs';
// The same independently observed shader reciprocal and two-weight edge
// interpolation execute in this draw, without a second context or readback.
export const hardwareClipVertexSource=`#version 300 es
precision highp float;precision highp int;
${multiplyNearestSource}
layout(location=0)in vec4 positionA;layout(location=1)in vec4 positionB;
layout(location=2)in vec4 colorA;layout(location=3)in vec4 colorB;
layout(location=4)in vec3 uvFogA;layout(location=5)in vec3 uvFogB;
layout(location=6)in vec2 edgeMode;
uniform vec4 viewport;uniform vec2 viewportCenter;uniform bool nativeTarget;
out vec4 diffuse;out vec2 texcoord;out float fog;out float nativeDepth;
float blendNative(float a,float b,float wa,float wb){return multiplyNearest(a,wa)+multiplyNearest(b,wb);}
void main(){
 vec4 p=positionA,c=colorA;vec3 t=uvFogA;
 if(edgeMode.x>.5){
  bool far=edgeMode.y>.5;float da=far?positionA.w-positionA.z:positionA.z,db=far?positionB.w-positionB.z:positionB.z;
  float r=1./(da-db),wa=multiplyNearest(-db,r),wb=multiplyNearest(da,r);
  p=vec4(blendNative(positionA.x,positionB.x,wa,wb),blendNative(positionA.y,positionB.y,wa,wb),blendNative(positionA.z,positionB.z,wa,wb),blendNative(positionA.w,positionB.w,wa,wb));p.z=far?p.w:0.;
  c=vec4(blendNative(colorA.r,colorB.r,wa,wb),blendNative(colorA.g,colorB.g,wa,wb),blendNative(colorA.b,colorB.b,wa,wb),blendNative(colorA.a,colorB.a,wa,wb));
  t=vec3(blendNative(uvFogA.x,uvFogB.x,wa,wb),blendNative(uvFogA.y,uvFogB.y,wa,wb),blendNative(uvFogA.z,uvFogB.z,wa,wb));
 }
 float q=1./p.w;
 vec2 screen=vec2(multiplyNearest(multiplyNearest(p.x,viewport.z*.5),q),multiplyNearest(multiplyNearest(-p.y,viewport.w*.5),q))+viewportCenter;
 screen=roundEven(screen*256.)/256.;p.xy=((screen-viewport.xy+vec2(.5))/viewport.zw*2.-1.)*vec2(1,nativeTarget?1:-1)*p.w;
 gl_Position=p;diffuse=c;texcoord=t.xy;fog=t.z;nativeDepth=0.;
}`;
