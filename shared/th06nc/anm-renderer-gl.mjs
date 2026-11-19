import {anmQuad} from './anm-quad.mjs';
import {anmWorldQuad,projectFlatWorldQuad} from './anm-world-quad.mjs';
import {textureUvScale} from './texture-gl.mjs';
import {anmVertexAlphas} from './anm-vertex-alpha.mjs';
export class AnmRendererGl {
 constructor(gl){
  this.gl=gl;
  const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  this.program=gl.createProgram();
  gl.attachShader(this.program,shader(gl.VERTEX_SHADER,`#version 300 es
  layout(location=0)in vec2 position;layout(location=1)in vec2 texcoord;uniform vec2 size;uniform vec2 uvScale;uniform vec2 edgeAlpha;out vec2 uv;out float vertexAlpha;void main(){uv=texcoord*uvScale;vertexAlpha=gl_VertexID<2?edgeAlpha.x:edgeAlpha.y;gl_Position=vec4(position.x/size.x*2.-1.,1.-position.y/size.y*2.,0.,1.);}`));
  gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,`#version 300 es
  precision highp float;in vec2 uv;in float vertexAlpha;uniform sampler2D atlas;uniform vec4 tint;uniform vec3 addColor;out vec4 color;void main(){color=texture(atlas,uv)*vec4(tint.rgb,vertexAlpha);color.rgb=clamp(color.rgb+addColor,0.,1.);}`));
  gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));
  this.vao=gl.createVertexArray();this.buffer=gl.createBuffer();gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
  for(let i=0;i<2;i++){gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,2,gl.FLOAT,false,16,i*8);}
  this.size=gl.getUniformLocation(this.program,'size');this.tint=gl.getUniformLocation(this.program,'tint');
  this.addColor=gl.getUniformLocation(this.program,'addColor');
  this.uvScale=gl.getUniformLocation(this.program,'uvScale');
  this.edgeAlpha=gl.getUniformLocation(this.program,'edgeAlpha');
 }
 draw(vm,texture,{addColor=[0,0,0],snap=false,space='screen',topAlpha=255,bottomAlpha=255}={}){
  if(space!=='screen'&&space!=='world')throw Error('TH06nc: unknown ANM drawing space '+space);
  const gl=this.gl,quad=space==='world'?projectFlatWorldQuad(anmWorldQuad(vm),gl.canvas.height):anmQuad(vm,gl.canvas.height,{snap});if(!quad)return false;
  return this.drawQuad(quad,texture,vm.v.getUint32(0xec,true),{addColor,additive:Boolean(vm.v.getUint32(0xc4,true)&4),topAlpha,bottomAlpha});
 }
 drawQuad(quad,texture,color=0xffffffff,{addColor=[0,0,0],additive=false,topAlpha=255,bottomAlpha=255}={}){
  const gl=this.gl;
  gl.useProgram(this.program);gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.bufferData(gl.ARRAY_BUFFER,quad,gl.STREAM_DRAW);
  gl.uniform2f(this.size,gl.canvas.width,gl.canvas.height);const c=color;
  gl.uniform4f(this.tint,((c>>>16)&255)/255,((c>>>8)&255)/255,(c&255)/255,(c>>>24)/255);
  const alpha=anmVertexAlphas(c,topAlpha,bottomAlpha);gl.uniform2f(this.edgeAlpha,alpha[0]/255,alpha[1]/255);
  gl.uniform3f(this.addColor,addColor[0]/255,addColor[1]/255,addColor[2]/255);
  gl.uniform2f(this.uvScale,...textureUvScale(texture));
  gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.enable(gl.BLEND);
  gl.blendEquation(gl.FUNC_ADD);gl.blendFunc(gl.SRC_ALPHA,additive?gl.ONE:gl.ONE_MINUS_SRC_ALPHA);
  gl.drawArrays(gl.TRIANGLE_STRIP,0,4);return true;
 }
 dispose(){const gl=this.gl;gl.deleteBuffer(this.buffer);gl.deleteVertexArray(this.vao);gl.deleteProgram(this.program);}
}
