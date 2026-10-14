"""Freeze the exact capture consumer and production WebGL resample, privately."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/deferred-capture-pixels-oct14';PRIVATE=OUT/'private';SHA=lambda b:hashlib.sha256(b).hexdigest()
assert not (OUT/'webgl-build.json').exists(),'Completed build immutable'
PRIVATE.mkdir(parents=True,exist_ok=True)
source=ROOT/'artifacts/th14/deferred-capture-intrinsic-oct14/source/cpp'
bindings=[]
for p in source.rglob('*.hpp'):
    q=PRIVATE/'cpp'/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());bindings.append({'path':str(p),'snapshot':q.relative_to(OUT).as_posix(),'sha256':SHA(p.read_bytes())})
for p in (ROOT/'runtimes/th12/portable/sdl').glob('*'):
    if p.suffix not in ('.cpp','.hpp'):continue
    q=PRIVATE/'portable/sdl'/p.name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());bindings.append({'path':str(p),'snapshot':q.relative_to(OUT).as_posix(),'sha256':SHA(p.read_bytes())})
fixture=r'''#include "portable/sdl/Renderer.hpp"
#include "cpp/sdl/ApplicationCaptureTh14.hpp"
#include <emscripten.h>
#include <memory>
#include <cstring>
using namespace touhou::sdl;
namespace {
std::vector<u8> source(640*480*4),targetPixels(512*512*4);
std::unique_ptr<Renderer> renderer;
u32 targetVersion=0,targetFormat=23;
int result[10]{};
struct Session {struct Resources {struct Core {th11::AnmResource text;}core;}resources;}session;
struct Backend {bool forcedFalse=false;int calls=0;bool last=false;
 bool resample(u32 src,const i32*from,u32 dst,const i32*to,const float*w,u32 width,u32 height){++calls;return last=!forcedFalse&&renderer->resample(src,from,dst,to,w,width,height);}
};
struct Graphics {static constexpr u32 screen=1;Backend backend;bool nullTarget=false;int changedCalls=0;
 u32 texture(th11::AnmResource& text,u32 index){return !nullTarget&&&text==&session.resources.core.text&&index==1?2:0;}
 void changed(u32){++changedCalls;++targetVersion;}
}graphics;
struct Render {int flushCalls=0,invalidateCalls=0;void flush(){++flushCalls;renderer->flush();}void invalidate(){++invalidateCalls;}}render;
Surface resolve_fixture(void*,u32 id){
 if(id==1)return {1,640,480,PixelFormat::Bgra8,640*4,source.data(),u32(source.size()),0};
 if(id==2)return {2,512,512,targetFormat==23?PixelFormat::Rgb565:PixelFormat::Bgra8,512*(targetFormat==23?2u:4u),targetPixels.data(),512*512*(targetFormat==23?2u:4u),targetVersion};
 return {};
}
void reset(){renderer->release(1);renderer->release(2);targetVersion=0;graphics=Graphics{};render=Render{};
 for(unsigned i=0;i<512*512;++i){u32 v=targetFormat==23?0x5a6b:0x917c3a5e;std::memcpy(targetPixels.data()+i*(targetFormat==23?2:4),&v,targetFormat==23?2:4);}}
void consume(th11::DeferredCaptureRequestTh14 request){th11::DeferredCaptureQueueTh14 queue;queue.enqueue(request);u32 before=renderer->stats.resamples;th11::sdl::th14_consume_deferred_captures(queue,session,graphics,render);
 renderer->read(2);int a[]={queue.first_file_index(),graphics.changedCalls,render.flushCalls,render.invalidateCalls,graphics.backend.calls,graphics.backend.last,int(glGetError()),1,2,int(renderer->stats.resamples-before)};std::memcpy(result,a,sizeof result);}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE int capture_initialize(){session.resources.core.text.textures.resize(2);renderer=std::make_unique<Renderer>(10,resolve_fixture,nullptr);return renderer->initialize();}
EMSCRIPTEN_KEEPALIVE u8* capture_source(){return source.data();}
EMSCRIPTEN_KEEPALIVE const u8* capture_pixels(){return targetPixels.data();}
EMSCRIPTEN_KEEPALIVE const int* capture_words(){return result;}
EMSCRIPTEN_KEEPALIVE int capture_case(int format,int sl,int st,int sr,int sb,int dl,int dt,int dr,int db){targetFormat=format;reset();th11::DeferredCaptureRequestTh14 request;request.file_index=0;request.texture_index=1;request.source={sl,st,sr-sl,sb-st};request.destination={dl,dt,dr-dl,db-dt};consume(request);return 1;}
EMSCRIPTEN_KEEPALIVE int capture_control(int mode){targetFormat=23;reset();th11::DeferredCaptureRequestTh14 request;request.file_index=mode==0?7:0;request.texture_index=1;request.source={32,16,384,448};request.destination={0,0,256,256};graphics.nullTarget=mode==1;graphics.backend.forcedFalse=mode==2;consume(request);return 1;}
}
'''
(PRIVATE/'fixture.cpp').write_text(fixture,encoding='utf8')
sdk=ROOT/'runtimes/th12/tools/emsdk';python='C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';flags=['-O2','-g0','-std=c++17','-DPORT_TITLE=14','-ffp-contract=off','-fno-exceptions','-fno-rtti','--use-port=sdl3','--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web','-sALLOW_MEMORY_GROWTH=1','-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2','-sGL_SUPPORT_AUTOMATIC_ENABLE_EXTENSIONS=0','-sEXPORTED_FUNCTIONS=_capture_initialize,_capture_source,_capture_case,_capture_pixels,_capture_words,_capture_control','-sEXPORTED_RUNTIME_METHODS=HEAPU8','-I'+str(PRIVATE)]
env=dict(os.environ,EM_CONFIG=str(sdk/'.emscripten'),EMSDK=str(sdk),TEMP=str(OUT),TMP=str(OUT),TMPDIR=str(OUT));p=subprocess.run([python,str(sdk/'upstream/emscripten/emcc.py'),*flags,str(PRIVATE/'fixture.cpp'),str(PRIVATE/'portable/sdl/Renderer.cpp'),'-o',str(OUT/'capture.mjs')],cwd=ROOT,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(OUT/'webgl-build.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
report=dict(privateBuilt=True,productionChanged=False,completeGame=False,nativeEquivalent=False,bindings=bindings,fixtureSha256=SHA((PRIVATE/'fixture.cpp').read_bytes()),wasmSha256=SHA((OUT/'capture.wasm').read_bytes()),loaderSha256=SHA((OUT/'capture.mjs').read_bytes()),flags=flags,toolSha256=SHA(Path(__file__).read_bytes()),captureConsumerSha256=SHA((PRIVATE/'cpp/sdl/ApplicationCaptureTh14.hpp').read_bytes()),scope='Exact frozen v2 intrinsic ApplicationCapture helper and current production Renderer/ResampleShader, no source edits. Minimal typed Session/Graphics adapter resolves actual caller identity text/texture1 to explicit512x512 RGB565 target, real WebGL backend success path. Null resource/texture and controlledfalse backend adapter are separately labelled, never claimed to be GPU errors or Native HRESULT equivalents.')
(OUT/'webgl-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'privateBuilt':True,'wasmSha256':report['wasmSha256']}))
