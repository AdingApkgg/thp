// Experimental preferred-HW path; clipped edge arithmetic executes in this draw.
import{buildHardwareClipGeometry}from'./BuildHardwareClipGeometryV1.mjs';
import{hardwareClipVertexSource}from'./HardwareClipVertexShaderV1.mjs';
// Experimental HW viewport: scale clip XY before the shader reciprocal multiply.
// Experimental HW shader RCP viewport with ordinary perspective attributes.
// Experimental original HW-VP homogeneous path; SW fallback remains selectable.
import{clipTrianglesToWindow}from'./ClipTrianglesToWindowV4.mjs';
import{multiplyNearestSource}from'./FloatMultiplyNearestV2.mjs';
import{multiplyTowardZeroSource}from'./FloatMultiplyTowardZeroV2.mjs';
// Same rendering math; valid command streams check WebGL errors at declared batch boundaries.
// Unaccepted candidate: both software-transformed XYZ and XYZRHW use the native 1/256 raster grid.
// Homogeneous fallback remains for nonpositive W.
// Unaccepted window-space XYZ depth plane; own RHW-weighted attributes. Clipping unvalidated.
// Unaccepted software-viewport XYZ projection before hardware RHW rasterization. Clipping not yet validated.
// Unaccepted EXT_clip_control ZERO_TO_ONE pipeline avoids XYZ Z clip remapping.
// Unaccepted XYZ shader variant omits fragment-depth output, uses hardware depth plane.
// Diagnostic 1/256 pixel coverage grid fork; interpolation still under investigation.
// Full-session renderer fork. Transformed FVF without SPECULAR supplies zero vertex fog.
const identity=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const color=v=>[(v>>>16&255)/255,(v>>>8&255)/255,(v&255)/255,(v>>>24)/255];
const asFloat=v=>new Float32Array(new Uint32Array([v]).buffer)[0];
const f=Math.fround;
// D3D9 fog color uses f32 reciprocal then f32 multiply; vertex/factor bytes
// retain their separately verified nearest division conversion.
const fogColor=v=>{const scale=f(1/255);return[f((v>>>16&255)*scale),f((v>>>8&255)*scale),f((v&255)*scale),(v>>>24)/255];};
// D3D9 raster grid uses nearest-even at exact half-subpixel coordinates.
function rasterCoordinate(v){const scaled=v*256,lower=Math.floor(scaled);return (scaled-lower===.5?(lower%2===0?lower:lower+1):Math.round(scaled))/256;}
function dot(a,b){let v=f(a[0]*b[0]);for(let i=1;i<4;i++)v=f(v+f(a[i]*b[i]));return v;}
function multiply(a,b){const out=new Float32Array(16);for(let row=0;row<4;row++)for(let column=0;column<4;column++)out[row*4+column]=dot(a.subarray(row*4,row*4+4),[b[column],b[column+4],b[column+8],b[column+12]]);return out;}
const transform=(m,p)=>[0,1,2,3].map(i=>dot(p,[m[i],m[i+4],m[i+8],m[i+12]]));
function viewportPosition(clip,viewport){
 const rhw=clip[3]===0?2097152:f(1/clip[3]),[x,y,width,height,min,max]=viewport;
 return [f(f(f(f(f(clip[0]+clip[3])*.5)*rhw)*width)+f(x+f(1e-6))),f(f(f(f(f(clip[1]+clip[3])*.5)*rhw)*-height)+f(f(y+height)+f(1e-6))),f(f(f(clip[2]*f(max-min))*rhw)+min),rhw];
}
function vertexFog(z,start,end){const inverse=f(1/f(end-start));return f(f(end*inverse)-f(Math.abs(z)*inverse));}
function hardwareVertexFog(z,start,end){const inverse=f(1/f(end-start));return f(f(end*inverse)-Math.abs(z)*inverse);}
// The reference adapter compares alpha after its render-target UNORM8
// conversion. Measure that conversion on this WebGL adapter, using generated
// float inputs only. No native game pixels or comparison fixtures are read.
function measureAlphaThresholds(gl,shader){
 const vertex=shader(gl.VERTEX_SHADER,`#version 300 es
 void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.0-1.0,0,1);}`),fragment=shader(gl.FRAGMENT_SHADER,`#version 300 es
 precision highp float;uniform highp sampler2D values;out vec4 result;
 void main(){float v=texelFetch(values,ivec2(int(gl_FragCoord.x),0),0).r;result=vec4(v,v,v,1);}`),program=gl.createProgram();gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 const output=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,output);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,256,1,0,gl.RGBA,gl.UNSIGNED_BYTE,null);const framebuffer=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,framebuffer);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,output,0);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Alpha calibration framebuffer unavailable');
 const input=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,input);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texImage2D(gl.TEXTURE_2D,0,gl.R32F,256,1,0,gl.RED,gl.FLOAT,null);const vao=gl.createVertexArray();gl.bindVertexArray(vao);gl.useProgram(program);gl.uniform1i(gl.getUniformLocation(program,'values'),0);gl.viewport(0,0,256,1);gl.disable(gl.BLEND);gl.disable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.disable(gl.SCISSOR_TEST);
 const lower=new Uint32Array(256),upper=new Uint32Array(256).fill(0x3f800000),middle=new Uint32Array(256),floats=new Float32Array(middle.buffer),pixels=new Uint8Array(1024);
 for(let step=0;step<30;step++){for(let i=1;i<256;i++)middle[i]=lower[i]+((upper[i]-lower[i])>>>1);gl.texSubImage2D(gl.TEXTURE_2D,0,0,0,256,1,gl.RED,gl.FLOAT,floats);gl.drawArrays(gl.TRIANGLES,0,3);gl.readPixels(0,0,256,1,gl.RGBA,gl.UNSIGNED_BYTE,pixels);for(let i=1;i<256;i++)if(upper[i]-lower[i]>1){if(pixels[i*4]>=i)upper[i]=middle[i];else lower[i]=middle[i];}}
 const thresholds=new Float32Array(257);thresholds.set(new Float32Array(upper.buffer));thresholds[0]=0;thresholds[256]=2;for(let i=1;i<256;i++)if(upper[i]-lower[i]!==1||thresholds[i]<thresholds[i-1])throw Error('Alpha calibration is not monotone');
 gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.bindVertexArray(null);gl.deleteVertexArray(vao);gl.deleteFramebuffer(framebuffer);gl.deleteTexture(input);gl.deleteTexture(output);gl.deleteProgram(program);gl.deleteShader(vertex);gl.deleteShader(fragment);return thresholds;
}
// Fixed-function D3D9 requests from StageRuntime. This first browser backend
// is a diagnostic renderer; raster output has not yet passed native pixel QA.
// Finite RHW depth-disabled probes do not generalize to XYZ near-plane crossings.
// XYZ software clipping is explicitly modeled when all original W are positive.
// Preserve original depth separately for fragment output; only GL clip Z is neutral.
export class SessionRenderer {
 constructor(canvas,{vertexProcessing="hardware"}={}){
  this.vertexProcessing=vertexProcessing;
  this.errorBatchDepth=0;this.errorBatchCommands=0;this.errorChecks=0;this.batchedCommands=0;this.batchCompletions=0;this.canvas=canvas;const gl=this.gl=canvas.getContext('webgl2',{alpha:false,antialias:false,depth:true,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL 2 is unavailable');const clip=this.clipControl=gl.getExtension('EXT_clip_control');if(!clip)throw Error('Exact zero-to-one depth extension unavailable');clip.clipControlEXT(clip.LOWER_LEFT_EXT,clip.ZERO_TO_ONE_EXT);
  const vs=`#version 300 es
  precision highp float;
  layout(location=0) in vec4 position;layout(location=1) in vec4 color;layout(location=2) in vec2 uv;layout(location=3) in float fogFactor;layout(location=4) in float depthFactor;
  uniform vec4 viewport;uniform bool nativeTarget;uniform bool directClip;
  out vec4 diffuse;out vec2 texcoord;out float fog;out float nativeDepth;
  void main(){float w=1.0/position.w;
   vec4 p=vec4(((position.xy-viewport.xy+vec2(.5))/viewport.zw*2.0-1.0)*vec2(1,nativeTarget?1:-1),position.z,1)*w;
   if(directClip){p=position;p.xy+=vec2(1.0/viewport.z,-1.0/viewport.w)*p.w;p.y*=nativeTarget?-1.0:1.0;}
   gl_Position=p;diffuse=color;texcoord=uv;fog=fogFactor;nativeDepth=depthFactor*p.w;
  }`;
  const fs=`#version 300 es
  precision highp float;precision highp int;${multiplyNearestSource}
  in vec4 diffuse;in vec2 texcoord;in float fog;in float nativeDepth;
  uniform sampler2D image;uniform vec4 factor,fogColor;uniform ivec4 stages;uniform bool alphaTest,fogEnabled;uniform vec2 alphaBounds;uniform int alphaFunc;out vec4 result;
  bool alphaPass(float a){return alphaFunc==1?false:alphaFunc==2?a<alphaBounds.x:alphaFunc==3?a>=alphaBounds.x&&a<alphaBounds.y:alphaFunc==4?a<alphaBounds.y:alphaFunc==5?a>=alphaBounds.y:alphaFunc==6?a<alphaBounds.x||a>=alphaBounds.y:alphaFunc==7?a>=alphaBounds.x:true;}
  void main(){vec4 t=texture(image,texcoord);vec4 c=stages.z==3?factor:diffuse;vec4 a=stages.w==3?factor:diffuse;vec4 v=vec4(stages.x==3?c.rgb:t.rgb*c.rgb,stages.y==3?a.a:t.a*a.a);if(alphaTest&&!alphaPass(v.a))discard;float fogWeight=clamp(fog,0.0,1.0);if(fogEnabled&&fogWeight!=1.0)v.rgb=v.rgb*fogWeight+vec3(multiplyNearest(fogColor.r,1.0-fogWeight),multiplyNearest(fogColor.g,1.0-fogWeight),multiplyNearest(fogColor.b,1.0-fogWeight));result=v;gl_FragDepth=nativeDepth*gl_FragCoord.w;}`;
  const shader=(kind,source)=>{const s=gl.createShader(kind);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  this.alphaThresholds=measureAlphaThresholds(gl,shader);
  const p=this.program=gl.createProgram();gl.attachShader(p,shader(gl.VERTEX_SHADER,vs));gl.attachShader(p,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));gl.useProgram(p);
  this.uniforms=Object.fromEntries(['viewport','image','nativeTarget','directClip','factor','fogColor','stages','alphaTest','alphaBounds','alphaFunc','fogEnabled'].map(n=>[n,gl.getUniformLocation(p,n)]));
  const depthVs=vs.replace('out float nativeDepth;','out float nativeDepth;out float perspectiveRhw;').replace('float w=1.0/position.w;','float w=1.0;').replace('diffuse=color;texcoord=uv;fog=fogFactor;','diffuse=color*position.w;texcoord=uv*position.w;fog=fogFactor*position.w;perspectiveRhw=position.w;');const depthFs=fs.replace('precision highp float;','precision highp float;precision highp int;'+multiplyTowardZeroSource).replace('in float nativeDepth;','in float nativeDepth;in float perspectiveRhw;').replace('void main(){','void main(){float inverseRhw=1.0/perspectiveRhw;').replace('texture(image,texcoord)','texture(image,vec2(multiplyTowardZero(texcoord.x,inverseRhw),multiplyTowardZero(texcoord.y,inverseRhw)))').replaceAll('factor:diffuse','factor:vec4(multiplyTowardZero(diffuse.r,inverseRhw),multiplyTowardZero(diffuse.g,inverseRhw),multiplyTowardZero(diffuse.b,inverseRhw),multiplyTowardZero(diffuse.a,inverseRhw))').replace('clamp(fog,0.0,1.0)','clamp(multiplyTowardZero(fog,inverseRhw),0.0,1.0)').replace('gl_FragDepth=nativeDepth*gl_FragCoord.w;','');
  const hardware=this.hardwareProgram=gl.createProgram();gl.attachShader(hardware,shader(gl.VERTEX_SHADER,depthVs));gl.attachShader(hardware,shader(gl.FRAGMENT_SHADER,depthFs));gl.linkProgram(hardware);if(!gl.getProgramParameter(hardware,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(hardware));
  this.hardwareUniforms=Object.fromEntries(Object.keys(this.uniforms).map(n=>[n,gl.getUniformLocation(hardware,n)]));
  const clipProgram=this.clipProgram=gl.createProgram();gl.attachShader(clipProgram,shader(gl.VERTEX_SHADER,vs));gl.attachShader(clipProgram,shader(gl.FRAGMENT_SHADER,fs.replace('gl_FragDepth=nativeDepth*gl_FragCoord.w;','')));gl.linkProgram(clipProgram);if(!gl.getProgramParameter(clipProgram,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(clipProgram));this.clipUniforms=Object.fromEntries(Object.keys(this.uniforms).map(n=>[n,gl.getUniformLocation(clipProgram,n)]));
  if(!gl.getExtension('NV_shader_noperspective_interpolation'))throw Error('Hardware interpolation extension unavailable');
  const homogeneousVs=`#version 300 es
  #extension GL_NV_shader_noperspective_interpolation : require
  precision highp float;precision highp int;${multiplyNearestSource}
  layout(location=0) in vec4 position;layout(location=1) in vec4 color;layout(location=2) in vec2 uv;layout(location=3) in float fogFactor;
  uniform vec4 viewport;uniform bool nativeTarget;uniform bool projectHardwareViewport;uniform mat4 worldViewProjection;uniform vec2 viewportCenter;uniform bool pretransformedClip;
  out vec4 diffuse;out vec2 texcoord;out float fog;out float nativeDepth;
  void main(){vec4 p=pretransformedClip?position:worldViewProjection*position;if(projectHardwareViewport){float q=1.0/p.w;vec2 screen=vec2(multiplyNearest(multiplyNearest(p.x,viewport.z*.5),q),multiplyNearest(multiplyNearest(-p.y,viewport.w*.5),q))+viewportCenter;screen=roundEven(screen*256.)/256.;p.xy=((screen-viewport.xy+vec2(.5))/viewport.zw*2.-1.)*vec2(1,nativeTarget?1:-1)*p.w;}else{p.xy+=vec2(1.0/viewport.z,-1.0/viewport.w)*p.w;p.y*=nativeTarget?-1.0:1.0;}gl_Position=p;diffuse=color;texcoord=uv;fog=fogFactor;nativeDepth=0.;}`;
  const homogeneousFs=fs.replace('gl_FragDepth=nativeDepth*gl_FragCoord.w;','');
  const homogeneous=this.homogeneousProgram=gl.createProgram();gl.attachShader(homogeneous,shader(gl.VERTEX_SHADER,homogeneousVs));gl.attachShader(homogeneous,shader(gl.FRAGMENT_SHADER,homogeneousFs));gl.linkProgram(homogeneous);if(!gl.getProgramParameter(homogeneous,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(homogeneous));this.homogeneousUniforms=Object.fromEntries([...Object.keys(this.uniforms),'projectHardwareViewport','worldViewProjection','viewportCenter','pretransformedClip'].map(n=>[n,gl.getUniformLocation(homogeneous,n)]));
  const hardwareClip=this.hardwareClipProgram=gl.createProgram();gl.attachShader(hardwareClip,shader(gl.VERTEX_SHADER,hardwareClipVertexSource));gl.attachShader(hardwareClip,shader(gl.FRAGMENT_SHADER,homogeneousFs));gl.linkProgram(hardwareClip);if(!gl.getProgramParameter(hardwareClip,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(hardwareClip));this.hardwareClipUniforms=Object.fromEntries(Object.keys(this.homogeneousUniforms).map(n=>[n,gl.getUniformLocation(hardwareClip,n)]));
  this.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);for(const[location,n,offset]of[[0,4,0],[1,4,16],[2,2,32],[3,1,40],[4,1,44]]){gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,n,gl.FLOAT,false,48,offset);}
  this.textures=new Map();this.textureInfo=new Map();this.framebuffers=new Map();this.backbufferToken=0;this.backbufferReferences=0;this.sharedDepth=null;this.currentTarget=0;this.white=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.white);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));
  this.vertexLayout=48;this.reset();
 }
 reset(){
  this.matrices=new Map([2,3,16,256].map(n=>[n,identity()]));this.viewport=[0,0,this.canvas.width,this.canvas.height,0,1];this.fvf=0x144;this.texture=0;this.draws=0;this.currentTarget=0;this.bindTarget(0);
  // Actual 46ff60 setup, followed by the relevant D3D9 device defaults.
  this.states=new Map([[7,1],[14,1],[15,1],[19,5],[20,6],[22,1],[23,8],[24,1],[25,7],[27,1],[28,1],[34,0xffa0a0a0],[35,0],[36,0x447a0000],[37,0x459c4000],[38,0x3f800000],[60,0xffffffff],[140,3],[171,1]]);
  this.stages=new Map([[1,4],[2,2],[3,3],[4,4],[5,2],[6,3],[24,2]]);this.samplers=new Map([[1,1],[2,1],[5,2],[6,2]]);
 }
 beginErrorBatch(){++this.errorBatchDepth;}
 endErrorBatch(){if(!this.errorBatchDepth)throw Error('Unmatched graphics error batch');if(--this.errorBatchDepth)return;++this.errorChecks;++this.batchCompletions;const count=this.errorBatchCommands;this.errorBatchCommands=0;const error=this.gl.getError();if(error)throw Error('WebGL error 0x'+error.toString(16)+' after '+count+' operations, last opcode '+this.lastBatchedOpcode);}
 dispatch(op,args,bytes){
  const gl=this.gl;
  if(op===0){if(bytes.byteLength!==64)throw Error('Invalid transform');this.matrices.set(args[0],new Float32Array(bytes.slice().buffer));}
  else if(op===1){const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);this.viewport=[v.getUint32(0,true),v.getUint32(4,true),v.getUint32(8,true),v.getUint32(12,true),v.getFloat32(16,true),v.getFloat32(20,true)];}
  else if(op===2)this.states.set(args[0],args[1]);
  else if(op===3){if(args[0])throw Error('Unsupported texture stage');this.stages.set(args[1],args[2]);}
  else if(op===4)this.fvf=args[0];
  else if(op===5)this.draw(args,bytes);
  else if(op===6){if(args[0])throw Error('Unsupported texture unit');this.texture=args[1];}
  else if(op===7){if(args[0])throw Error('Unsupported sampler');this.samplers.set(args[1],args[2]);}
  else if(op===14)this.clear(args,bytes);
  else if(op===15){if(args[0])throw Error('Unsupported render-target slot');this.bindTarget(args[1],true);}
  else if(op===16)this.uploadTexture(args,bytes);
  else if(op===17){const token=args[0],target=this.framebuffers.get(token);if(target){if(this.currentTarget===token)this.bindTarget(0);gl.deleteFramebuffer(target.framebuffer);this.framebuffers.delete(token);}gl.deleteTexture(this.textures.get(token));this.textures.delete(token);this.textureInfo.delete(token);}
  else if(op===20)this.acquireBackbuffer(args[0]);
  else if(op===21){if(args[0]!==this.backbufferToken||!this.backbufferReferences)throw Error('Unknown backbuffer reference');--this.backbufferReferences;}
  else throw Error('Unknown device operation '+op);
  if(this.errorBatchDepth){++this.errorBatchCommands;++this.batchedCommands;this.lastBatchedOpcode=op;}else{++this.errorChecks;const error=gl.getError();if(error)throw Error('WebGL error 0x'+error.toString(16)+' in operation '+op);}return 1;
 }
 // All D3D9 targets keep the device's automatic D24S8 surface. A separate
 // backbuffer FBO lets WebGL share that depth/stencil storage with both textures.
 // Every FBO stores native row zero at GL row zero, like uploaded images.
 // The vertex viewport/scissor use that same orientation for color and depth;
 // only the final canvas blit reverses rows. Flipping sampled UVs introduces
 // rounding at point-sample boundaries and changes linear interpolation.
 acquireBackbuffer(token){
  const gl=this.gl;if(!token)throw Error('Invalid backbuffer token');
  if(this.backbufferToken){if(token!==this.backbufferToken)throw Error('Backbuffer token changed');++this.backbufferReferences;return;}
  this.backbufferToken=token;this.backbufferReferences=1;
  this.sharedDepth=gl.createRenderbuffer();gl.bindRenderbuffer(gl.RENDERBUFFER,this.sharedDepth);gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH24_STENCIL8,this.canvas.width,this.canvas.height);
  const texture=gl.createTexture(),pixels=new Uint8Array(this.canvas.width*this.canvas.height*4);for(let i=3;i<pixels.length;i+=4)pixels[i]=255;gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,this.canvas.width,this.canvas.height,0,gl.RGBA,gl.UNSIGNED_BYTE,pixels);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
  this.makeTarget(0,texture,{format:22,width:this.canvas.width,height:this.canvas.height});this.bindTarget(0);
 }
 makeTarget(token,texture,info){
  const gl=this.gl;
  const framebuffer=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,framebuffer);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,texture,0);gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_STENCIL_ATTACHMENT,gl.RENDERBUFFER,this.sharedDepth);
  if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Incomplete target '+token.toString(16));const target={framebuffer,texture,format:info.format,width:info.width,height:info.height};this.framebuffers.set(token,target);return target;
 }
 bindTarget(surface,resetViewport=false){
  const gl=this.gl,token=surface===this.backbufferToken?0:surface;let target=this.framebuffers.get(token);
  if(!target&&token){const texture=this.textures.get(token),info=this.textureInfo.get(token);if(!texture||!info||!this.sharedDepth)throw Error('Unknown render target '+token.toString(16));target=this.makeTarget(token,texture,info);}
  this.currentTarget=token;gl.bindFramebuffer(gl.FRAMEBUFFER,target?.framebuffer||null);const alpha=target?![20,22,23].includes(target.format):true;gl.colorMask(true,true,true,alpha);
  // IDirect3DDevice9::SetRenderTarget resets the viewport even when the
  // requested surface is already current. Internal framebuffer binds do not.
  if(resetViewport)this.viewport=[0,0,target?.width||this.canvas.width,target?.height||this.canvas.height,0,1];
 }
 targetHeight(){return this.framebuffers.get(this.currentTarget)?.height||this.canvas.height;}
 dispose(){
  const gl=this.gl;gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.bindRenderbuffer(gl.RENDERBUFFER,null);gl.colorMask(true,true,true,true);
  for(const target of this.framebuffers.values())gl.deleteFramebuffer(target.framebuffer);
  for(const texture of this.textures.values())gl.deleteTexture(texture);
  const back=this.framebuffers.get(0);if(back)gl.deleteTexture(back.texture);
  if(this.sharedDepth)gl.deleteRenderbuffer(this.sharedDepth);gl.deleteTexture(this.white);gl.deleteBuffer(this.buffer);
  for(const shader of gl.getAttachedShaders(this.program)||[])gl.deleteShader(shader);gl.deleteProgram(this.program);for(const shader of gl.getAttachedShaders(this.hardwareProgram)||[])gl.deleteShader(shader);gl.deleteProgram(this.hardwareProgram);for(const shader of gl.getAttachedShaders(this.clipProgram)||[])gl.deleteShader(shader);gl.deleteProgram(this.clipProgram);
  for(const shader of gl.getAttachedShaders(this.homogeneousProgram)||[])gl.deleteShader(shader);gl.deleteProgram(this.homogeneousProgram);
  for(const shader of gl.getAttachedShaders(this.hardwareClipProgram)||[])gl.deleteShader(shader);gl.deleteProgram(this.hardwareClipProgram);
  this.framebuffers.clear();this.textures.clear();this.textureInfo.clear();
 }
 present(){
  if(!this.backbufferToken)return;const gl=this.gl,back=this.framebuffers.get(0);gl.disable(gl.SCISSOR_TEST);gl.bindFramebuffer(gl.READ_FRAMEBUFFER,back.framebuffer);gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER,null);gl.blitFramebuffer(0,0,back.width,back.height,0,this.canvas.height,this.canvas.width,0,gl.COLOR_BUFFER_BIT,gl.NEAREST);this.bindTarget(this.currentTarget);gl.bindFramebuffer(gl.READ_FRAMEBUFFER,null);
  const error=gl.getError();if(error)throw Error('WebGL present error '+error);
 }
 uploadTexture(args,bytes){
  const gl=this.gl,[token,format,w,h]=args;this.textureInfo.set(token,{format,width:w,height:h});const target=this.framebuffers.get(token);if(target){target.width=w;target.height=h;target.format=format;}let texture=this.textures.get(token);if(!texture){texture=gl.createTexture();this.textures.set(token,texture);}gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);
  if([23,25,26].includes(format)){const packed=new Uint16Array(w*h),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);for(let i=0;i<packed.length;i++){const n=v.getUint16(i*2,true);packed[i]=format===23?n:format===25?(n&0x7fff)<<1|n>>>15:(n&0xfff)<<4|n>>>12;}gl.texImage2D(gl.TEXTURE_2D,0,format===23?gl.RGB565:format===25?gl.RGB5_A1:gl.RGBA4,w,h,0,format===23?gl.RGB:gl.RGBA,format===23?gl.UNSIGNED_SHORT_5_6_5:format===25?gl.UNSIGNED_SHORT_5_5_5_1:gl.UNSIGNED_SHORT_4_4_4_4,packed);return;}
  if(![20,21,22].includes(format))throw Error('Unsupported physical texture format '+format);
  const rgba=new Uint8Array(w*h*4),stride=format===20?3:4;if(bytes.length!==w*h*stride)throw Error('Invalid texture size');for(let i=0,p=0;i<rgba.length;i+=4,p+=stride){rgba[i]=bytes[p+2];rgba[i+1]=bytes[p+1];rgba[i+2]=bytes[p];rgba[i+3]=format===21?bytes[p+3]:255;}gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,rgba);
 }
 clear(args,bytes){
  const gl=this.gl,[count,flags,packed,depth,stencil]=args,[vx,vy,vw,vh]=this.viewport;
  gl.clearColor(...color(packed));gl.clearDepth(asFloat(depth));gl.clearStencil(stencil);gl.depthMask(true);
  const mask=(flags&1?gl.COLOR_BUFFER_BIT:0)|(flags&2?gl.DEPTH_BUFFER_BIT:0)|(flags&4?gl.STENCIL_BUFFER_BIT:0);
  // D3D9 clears the viewport for Count=0 and clips each explicit rectangle
  // against it. GL clear itself ignores the viewport, so use a scissor.
  const rectangle=(l,t,r,b)=>{l=Math.max(l,vx);t=Math.max(t,vy);r=Math.min(r,vx+vw);b=Math.min(b,vy+vh);if(r<=l||b<=t)return;gl.scissor(l,this.backbufferToken?t:this.targetHeight()-b,r-l,b-t);gl.clear(mask);};
  gl.enable(gl.SCISSOR_TEST);
  if(!count)rectangle(vx,vy,vx+vw,vy+vh);
  else{const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);for(let i=0;i<count;i++)rectangle(...[0,4,8,12].map(offset=>view.getInt32(i*16+offset,true)));}
  gl.disable(gl.SCISSOR_TEST);
 }
 draw(args,bytes){
  const gl=this.gl;let[type,count,stride]=args;if(![0x44,0x144,0x102,0x142].includes(this.fvf))throw Error('Unsupported FVF '+this.fvf.toString(16));if(bytes.length%stride)throw Error('Partial vertex');
  const transformed=!!(this.fvf&4),hasColor=!!(this.fvf&0x40),hasUv=!!(this.fvf&0x100),data=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);let n=bytes.length/stride,vertices=new Float32Array(n*12);
  const worldView=multiply(this.matrices.get(256),this.matrices.get(2)),worldViewProjection=multiply(worldView,this.matrices.get(3)),textureMatrix=this.matrices.get(16),start=asFloat(this.states.get(36)),end=asFloat(this.states.get(37));
  const hardwareVertexProcessing=!transformed&&this.vertexProcessing==="hardware";
  const clipVertices=[];let clipRequired=false;if(!transformed)for(let i=0;i<n;i++){const at=i*stride,c=transform(worldViewProjection,[data.getFloat32(at,true),data.getFloat32(at+4,true),data.getFloat32(at+8,true),1]);clipVertices.push(c);if(!(c[3]>0)||!c.every(Number.isFinite))clipRequired=true;}
  for(let i=0;i<n;i++){const p=i*stride,q=i*12,position=[data.getFloat32(p,true),data.getFloat32(p+4,true),data.getFloat32(p+8,true),transformed?data.getFloat32(p+12,true):1],clip=transformed?position:clipVertices[i];vertices.set(transformed||hardwareVertexProcessing?position:clipRequired?clip:viewportPosition(clip,this.viewport),q);if(transformed||(!hardwareVertexProcessing&&!clipRequired)){vertices[q]=rasterCoordinate(vertices[q]);vertices[q+1]=rasterCoordinate(vertices[q+1]);}if(transformed&&!this.states.get(7))vertices[q+2]=0;vertices[q+11]=transformed?position[2]:viewportPosition(clip,this.viewport)[2];let at=p+(transformed?16:12);vertices.set(hasColor?color(data.getUint32(at,true)):[1,1,1,1],q+4);if(hasColor)at+=4;if(hasUv){const uv=[data.getFloat32(at,true),data.getFloat32(at+4,true)];vertices.set(transformed?uv:transform(textureMatrix,[...uv,1,0]).slice(0,2),q+8);}const eyeZ=transformed?0:transform(worldView,position)[2];vertices[q+10]=this.states.get(28)?(transformed?0:(hardwareVertexProcessing?hardwareVertexFog:vertexFog)(eyeZ,start,end)):1;}
  let hardwareClipped=false;if(hardwareVertexProcessing&&!clipRequired&&this.states.get(136)!==0&&(clipVertices.some(c=>c[2]<0)!==clipVertices.some(c=>c[2]>c[3]))){const records=clipVertices.map((clip,i)=>({clip,attributes:Array.from(vertices.subarray(i*12+4,i*12+11))})),clipped=buildHardwareClipGeometry(records,type,clipVertices.some(c=>c[2]>c[3]));if(clipped){hardwareClipped=true;vertices=clipped;n=vertices.length/24;type=4;count=n/3;}}
  let cpuClipped=false;
  if(!transformed&&!hardwareVertexProcessing&&!clipRequired&&this.states.get(136)!==0&&clipVertices.some(c=>c[2]<0||c[2]>c[3])){const records=clipVertices.map((clip,i)=>({clip,attributes:Array.from(vertices.subarray(i*12+4,i*12+11)),packet:Array.from(vertices.subarray(i*12,i*12+12)),window:viewportPosition(clip,this.viewport)})),clipped=clipTrianglesToWindow(records,type,this.viewport,rasterCoordinate);if(clipped){cpuClipped=true;vertices=clipped;n=vertices.length/12;type=4;count=n/3;}}
  const s=k=>this.states.get(k),u=transformed?this.uniforms:hardwareVertexProcessing?(hardwareClipped?this.hardwareClipUniforms:this.homogeneousUniforms):clipRequired?this.clipUniforms:this.hardwareUniforms;gl.useProgram(transformed?this.program:hardwareVertexProcessing?(hardwareClipped?this.hardwareClipProgram:this.homogeneousProgram):clipRequired?this.clipProgram:this.hardwareProgram);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.bufferData(gl.ARRAY_BUFFER,vertices,gl.STREAM_DRAW);
  const vertexLayout=hardwareClipped?96:48;if(this.vertexLayout!==vertexLayout){const layout=hardwareClipped?[[0,4,0],[1,4,16],[2,4,32],[3,4,48],[4,3,64],[5,3,76],[6,2,88]]:[[0,4,0],[1,4,16],[2,2,32],[3,1,40],[4,1,44]];for(const[location,size,offset]of layout){gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,size,gl.FLOAT,false,vertexLayout,offset);}if(!hardwareClipped){gl.disableVertexAttribArray(5);gl.disableVertexAttribArray(6);}this.vertexLayout=vertexLayout;}
  if(hardwareVertexProcessing){gl.uniform1i(u.pretransformedClip,hardwareClipped);gl.uniformMatrix4fv(u.worldViewProjection,false,worldViewProjection);gl.uniform2f(u.viewportCenter,f(this.viewport[0]+this.viewport[2]*.5),f(this.viewport[1]+this.viewport[3]*.5));gl.uniform1i(u.projectHardwareViewport,clipVertices.every(c=>c[3]>0&&c.every(Number.isFinite))&&!(clipVertices.some(c=>c[2]<0)&&clipVertices.some(c=>c[2]>c[3])));}
  const[x,y,w,h,min,max]=this.viewport;gl.viewport(x,this.backbufferToken?y:this.targetHeight()-y-h,w,h);gl.depthRange(min,max);gl.uniform4f(u.viewport,x,y,w,h);gl.uniform4fv(u.fogColor,fogColor(s(34)));gl.uniform4fv(u.factor,color(s(60)));gl.uniform4i(u.stages,this.stages.get(1),this.stages.get(4),this.stages.get(3),this.stages.get(6));gl.uniform1i(u.alphaTest,!!s(15));gl.uniform1i(u.fogEnabled,!!s(28));gl.uniform2f(u.alphaBounds,this.alphaThresholds[s(24)],this.alphaThresholds[s(24)+1]);gl.uniform1i(u.alphaFunc,s(25));gl.uniform1i(u.image,0);gl.uniform1i(u.nativeTarget,!!this.backbufferToken);gl.uniform1i(u.directClip,clipRequired);
  gl.activeTexture(gl.TEXTURE0);const texture=this.texture?this.textures.get(this.texture):this.white;if(!texture)throw Error('Unknown texture '+this.texture.toString(16));gl.bindTexture(gl.TEXTURE_2D,texture);const wrap={1:gl.REPEAT,2:gl.MIRRORED_REPEAT,3:gl.CLAMP_TO_EDGE};gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,wrap[this.samplers.get(1)]);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,wrap[this.samplers.get(2)]);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,this.samplers.get(6)===1?gl.NEAREST:gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,this.samplers.get(5)===1?gl.NEAREST:gl.LINEAR);
  s(7)?gl.enable(gl.DEPTH_TEST):gl.disable(gl.DEPTH_TEST);gl.depthMask(!!s(14));gl.depthFunc([0,gl.NEVER,gl.LESS,gl.EQUAL,gl.LEQUAL,gl.GREATER,gl.NOTEQUAL,gl.GEQUAL,gl.ALWAYS][s(23)]);
  gl.disable(gl.CULL_FACE);s(27)?gl.enable(gl.BLEND):gl.disable(gl.BLEND);const blend=[0,gl.ZERO,gl.ONE,gl.SRC_COLOR,gl.ONE_MINUS_SRC_COLOR,gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.DST_ALPHA,gl.ONE_MINUS_DST_ALPHA,gl.DST_COLOR,gl.ONE_MINUS_DST_COLOR,gl.SRC_ALPHA_SATURATE];gl.blendFunc(blend[s(19)],blend[s(20)]);gl.blendEquation([0,gl.FUNC_ADD,gl.FUNC_SUBTRACT,gl.FUNC_REVERSE_SUBTRACT,gl.MIN,gl.MAX][s(171)]);
  const modes=[0,gl.POINTS,gl.LINES,gl.LINE_STRIP,gl.TRIANGLES,gl.TRIANGLE_STRIP,gl.TRIANGLE_FAN];const expected=type===1?count:type===2?count*2:type===3?count+1:type===4?count*3:count+2;if(n!==expected||!modes[type]&&type!==1)throw Error('Invalid primitive payload');let depthClamp;if(cpuClipped){depthClamp=this.depthClamp||(this.depthClamp=gl.getExtension('EXT_depth_clamp'));if(!depthClamp)throw Error('Depth clamp unavailable for software-clipped geometry');gl.enable(depthClamp.DEPTH_CLAMP_EXT);}gl.drawArrays(modes[type],0,n);if(depthClamp)gl.disable(depthClamp.DEPTH_CLAMP_EXT);++this.draws;
 }
}
export {multiply,transform,viewportPosition,vertexFog};
