import {anmWorldQuad} from './anm-world-quad.mjs';
import {textureUvScale} from './texture-gl.mjs';
// Perspective backend for original world ANM geometry. Fog interpolation and
// GPU sampling are not yet pixel-compared against the native renderer.
export class StdRendererGl {
 constructor(gl){
  this.gl=gl;const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};this.program=gl.createProgram();
  gl.attachShader(this.program,shader(gl.VERTEX_SHADER,`#version 300 es
  layout(location=0)in vec3 position;layout(location=1)in vec2 texcoord;uniform mat4 view;uniform mat4 projection;uniform vec2 uvScale;out vec2 uv;out float eyeDepth;void main(){vec4 eye=view*vec4(position,1.);vec4 clip=projection*eye;gl_Position=vec4(clip.xy,2.*clip.z-clip.w,clip.w);uv=texcoord*uvScale;eyeDepth=eye.z;}`));
  gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,`#version 300 es
  precision highp float;in vec2 uv;in float eyeDepth;uniform sampler2D atlas;uniform vec4 tint;uniform vec3 fogColor;uniform vec2 fogRange;out vec4 color;void main(){color=texture(atlas,uv)*tint;if(color.a==0.)discard;float fog=clamp((fogRange.y-eyeDepth)/(fogRange.y-fogRange.x),0.,1.);color.rgb=mix(fogColor,color.rgb,fog);}`));
  gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));this.uniform=Object.fromEntries(['view','projection','uvScale','tint','fogColor','fogRange'].map(n=>[n,gl.getUniformLocation(this.program,n)]));this.vao=gl.createVertexArray();this.buffer=gl.createBuffer();gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,20,0);gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,2,gl.FLOAT,false,20,12);
 }
 draw(vm,texture,{view,projection,fogColor=[0,0,0],fogRange=[200,500]}={}){
  const quad=anmWorldQuad(vm);if(!quad)return false;if(!texture)throw Error('TH06nc STD: texture missing');const gl=this.gl,c=vm.v.getUint32(0xec,true);gl.useProgram(this.program);gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.bufferData(gl.ARRAY_BUFFER,quad,gl.STREAM_DRAW);gl.uniformMatrix4fv(this.uniform.view,false,view);gl.uniformMatrix4fv(this.uniform.projection,false,projection);gl.uniform2f(this.uniform.uvScale,...textureUvScale(texture));gl.uniform4f(this.uniform.tint,((c>>>16)&255)/255,((c>>>8)&255)/255,(c&255)/255,(c>>>24)/255);gl.uniform3f(this.uniform.fogColor,...fogColor.map(x=>x/255));gl.uniform2f(this.uniform.fogRange,...fogRange);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.depthMask(true);gl.disable(gl.CULL_FACE);gl.enable(gl.BLEND);gl.blendEquation(gl.FUNC_ADD);gl.blendFunc(gl.SRC_ALPHA,vm.v.getUint32(0xc4,true)&4?gl.ONE:gl.ONE_MINUS_SRC_ALPHA);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);return true;
 }
 dispose(){const gl=this.gl;gl.deleteBuffer(this.buffer);gl.deleteVertexArray(this.vao);gl.deleteProgram(this.program);}
}
