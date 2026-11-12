// Standalone ANGLE D3D11 pbuffer for the threaded WASI Application host.
// Only installed, hash-bound libraries; no window, browser or audio device.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
const deps=resolve(root,'artifacts/th14/process-clock-resolution-nov06/dependencies');
const require=createRequire(resolve(deps,'package.json')),koffi=require('koffi');
const sha=b=>createHash('sha256').update(b).digest('hex');
const platformType=koffi.proto('void *th14_angle_platform_nov08(unsigned int, void *, const int *)');
const clipType=koffi.proto('void th14_angle_clip_nov08(unsigned int, unsigned int)');
export function createTh14AngleContext(directory,width=640,height=480){
 assert([[640,480],[960,720],[1280,960]].some(s=>s[0]===width&&s[1]===height));
 assert.equal(process.platform,'win32');
 const files={},expected={
  'libEGL.dll':'e1ffb51ebd7e89512efaf5052549decdd4e058193f9662b2118d0974f9c1001c',
  'libGLESv2.dll':'252a6201ec13d787d01a2a110442f4d73fc1c486e8a42cc62e0875128e762e42'};
 for(const [name,digest]of Object.entries(expected)){
  const path=resolve(directory,name),bytes=readFileSync(path);assert.equal(sha(bytes),digest);
  files[name]={path,bytes:bytes.length,sha256:digest};
 }
 const egl=koffi.load(files['libEGL.dll'].path),gles=koffi.load(files['libGLESv2.dll'].path),functions=new Map();
 const proc=egl.func('void *eglGetProcAddress(const char *)');
 const error=egl.func('unsigned int eglGetError()');
 const makeCurrent=egl.func('unsigned int eglMakeCurrent(void *,void *,void *,void *)');
 const destroyContext=egl.func('unsigned int eglDestroyContext(void *,void *)');
 const destroySurface=egl.func('unsigned int eglDestroySurface(void *,void *)');
 const terminate=egl.func('unsigned int eglTerminate(void *)');
 let display=null,surface=null,context=null,initialized=false,closed=false;
 const cleanup=[];
 const gl=(name,result,args)=>{if(!functions.has(name))functions.set(name,gles.func(name,result,args));return functions.get(name);};
 function close(){
  if(closed)return cleanup;closed=true;
  if(initialized){
   cleanup.push({operation:'make-no-context',result:makeCurrent(display,null,null,null)});
   if(context)cleanup.push({operation:'destroy-context',result:destroyContext(display,context)});
   if(surface)cleanup.push({operation:'destroy-surface',result:destroySurface(display,surface)});
   cleanup.push({operation:'terminate-display',result:terminate(display)});
  }
  process.removeListener('exit',close);return cleanup;
 }
 try{
  const platform=proc('eglGetPlatformDisplayEXT');assert(platform);
  display=koffi.call(platform,platformType,0x3202,null,new Int32Array([0x3203,0x3208,0x3209,0x320a,0x3038]));
  assert(display,'ANGLE D3D11 display');
  const major=new Int32Array(1),minor=new Int32Array(1);
  const initialize=egl.func('unsigned int eglInitialize(void *, _Out_ int *, _Out_ int *)');
  assert.equal(initialize(display,major,minor),1,'eglInitialize '+error().toString(16));initialized=true;
  process.once('exit',close);
  assert.equal(egl.func('unsigned int eglBindAPI(unsigned int)')(0x30a0),1);
  const config=[null],count=new Int32Array(1);
  const choose=egl.func('unsigned int eglChooseConfig(void *,const int *,_Out_ void **,int,_Out_ int *)');
  assert.equal(choose(display,new Int32Array([0x3033,1,0x3040,0x40,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3025,0,0x3026,0,0x3038]),config,1,count),1);
  assert.equal(count[0],1);assert(config[0]);
  surface=egl.func('void *eglCreatePbufferSurface(void *,void *,const int *)')(display,config[0],new Int32Array([0x3057,width,0x3056,height,0x3038]));
  assert(surface,'eglCreatePbufferSurface '+error().toString(16));
  context=egl.func('void *eglCreateContext(void *,void *,void *,const int *)')(display,config[0],null,new Int32Array([0x3098,3,0x3038]));
  assert(context,'eglCreateContext '+error().toString(16));assert.equal(makeCurrent(display,surface,surface,context),1);
  const getString=gl('glGetString','str',['uint']);
  const info={renderer:getString(0x1f01),version:getString(0x1f02),vendor:getString(0x1f00),glsl:getString(0x8b8c),
   offscreenWidth:width,offscreenHeight:height,egl:[major[0],minor[0]],extensions:getString(0x1f03).split(' '),libraries:files,
   koffiVersion:JSON.parse(readFileSync(resolve(deps,'node_modules/koffi/package.json'))).version,
   dependencyLockSha256:sha(readFileSync(resolve(deps,'package-lock.json')))};
  assert(info.renderer.includes('D3D11'),'No backend fallback');
  const getError=gl('glGetError','uint',[]);
  function clipControl(){
   assert(info.extensions.includes('GL_EXT_clip_control'));
   const pointer=proc('glClipControlEXT');assert(pointer);koffi.call(pointer,clipType,0x8ca1,0x935f);
   assert.equal(getError(),0);return 1;
  }
  function readBGRA(){
   const previous=new Int32Array(1);
   gl('glGetIntegerv','void',['uint','_Out_ int *'])(0x8caa,previous);
   gl('glBindFramebuffer','void',['uint','uint'])(0x8ca8,0);
   const rgba=Buffer.alloc(width*height*4);
   gl('glReadPixels','void',['int','int','int','int','uint','uint','void *'])(0,0,width,height,0x1908,0x1401,rgba);
   gl('glBindFramebuffer','void',['uint','uint'])(0x8ca8,previous[0]);assert.equal(getError(),0,'Read framebuffer error');
   const bgra=Buffer.alloc(rgba.length);
   for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const a=((height-1-y)*width+x)*4,b=(y*width+x)*4;
    bgra[b]=rgba[a+2];bgra[b+1]=rgba[a+1];bgra[b+2]=rgba[a];bgra[b+3]=rgba[a+3];
   }return bgra;
  }
  return{info,gl,getError,clipControl,readBGRA,close,get closed(){return closed;},cleanup};
 }catch(e){close();throw e;}
}
