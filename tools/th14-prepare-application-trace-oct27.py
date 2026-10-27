"""Prepare a private renderer/host trace of one actual Application frame.

Production sources are copied and instrumented only in the new artifact folder.
The trace observes semantic draw inputs before either graphics backend; no
captured pixels or game values are supplied back to the C++ application.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()

CPP = r'''
#include <cstring>
extern "C" int th14_trace_active();
extern "C" void th14_trace_event(unsigned,const unsigned*,unsigned,const void*,unsigned);
namespace touhou::sdl {
static u32 trace_word(float v){u32 n;std::memcpy(&n,&v,4);return n;}
static void trace_surface(Renderer& r,u32 id){if(!id)return;const auto s=r.resolve(r.owner,id);
 const u32 h[]{id,s.width,s.height,u32(s.format),s.pitch,s.size,s.version};
 th14_trace_event(4,h,7,s.data,s.data?s.size:0);}
static void trace_draw(Renderer& r,const State& d,Topology primitive,u32 count,const void* data,u32 size,const void* index,IndexType indexFormat,const void* instance,u32 instanceSize){
 trace_surface(r,d.target);trace_surface(r,d.depth);trace_surface(r,d.texture);
 const auto& p=d.pipeline;const auto& v=d.viewport;u32 words[125];u32 n=0;
 auto put=[&](u32 value){words[n++]=value;};auto scalar=[&](float value){put(trace_word(value));};
 put(0x54524331);put(d.target);put(d.depth);put(d.texture);
 put(v.x);put(v.y);put(v.width);put(v.height);scalar(v.min);scalar(v.max);
 put(d.stride);put(d.layout.screen);put(d.layout.diffuse);put(d.layout.specular);put(d.layout.uv);
 put(p.depthTest);put(p.depthWrite);put(p.blend);put(p.alphaTest);put(p.fog);put(p.rangeFog);put(p.dither);
 put(u32(p.depthCompare));put(u32(p.alphaCompare));put(u32(p.sourceBlend));put(u32(p.destinationBlend));put(u32(p.blendEquation));put(u32(p.cull));
 put(p.colorMask);put(p.alphaReference);put(p.fogColor);put(p.textureFactor);put(u32(p.fogMode));scalar(p.fogNear);scalar(p.fogFar);scalar(p.fogDensity);
 auto combiner=[&](const Combiner& c){put(u32(c.operation));for(const auto a:{c.first,c.second}){put(u32(a.source));put(a.complement);put(a.alphaOnly);}};
 combiner(p.color);combiner(p.alpha);put(p.textureTransform);put(u32(p.minFilter));put(u32(p.magFilter));put(u32(p.addressU));put(u32(p.addressV));
 for(const auto& matrix:d.matrix)for(float value:matrix)scalar(value);
 const u32 indexCount=index?vertex_count(primitive,count):0;
 if(index){u32 maximum=0;for(u32 i=0;i<indexCount;++i){u32 value;if(indexFormat==IndexType::UInt16){uint16_t q;std::memcpy(&q,static_cast<const u8*>(index)+i*2,2);value=q;}else std::memcpy(&value,static_cast<const u8*>(index)+i*4,4);if(value>maximum)maximum=value;}const u32 needed=(maximum+1)*d.stride;if(needed>size)size=needed;}
 const u32 indexBytes=indexCount*(indexFormat==IndexType::UInt16?2:4);
 put(u32(primitive));put(count);put(size);put(u32(indexFormat));put(indexBytes);put(instanceSize);
 th14_trace_event(1,words,n,data,size);
 if(indexBytes)th14_trace_event(2,nullptr,0,index,indexBytes);
 if(instanceSize)th14_trace_event(3,nullptr,0,instance,instanceSize);
}
static void trace_clear(Renderer& r,u32 flags,u32 c,float depth,u32 stencil,const i32* rects,u32 count){
 trace_surface(r,r.state.target);trace_surface(r,r.state.depth);const auto& v=r.state.viewport;
 i32 box[]{i32(v.x),i32(v.y),i32(v.x+v.width),i32(v.y+v.height)};if(!rects){rects=box;count=1;}
 const u32 h[]{r.state.target,r.state.depth,flags,c,trace_word(depth),stencil,v.x,v.y,v.width,v.height,count};
 th14_trace_event(10,h,11,rects,count*16);
}
static void trace_copy(Renderer& r,u32 src,const i32* rect,u32 dst,const i32* point){
 trace_surface(r,src);trace_surface(r,dst);const u32 h[]{src,dst};i32 data[]{rect[0],rect[1],rect[2],rect[3],point[0],point[1]};th14_trace_event(11,h,2,data,24);
}
static void trace_resample(Renderer& r,u32 src,const i32* from,u32 dst,const i32* to,const float* weights,u32 width,u32 height){
 trace_surface(r,src);trace_surface(r,dst);u32 h[]{src,dst,u32(from[0]),u32(from[1]),u32(from[2]),u32(from[3]),u32(to[0]),u32(to[1]),u32(to[2]),u32(to[3]),width,height,u32(weights!=nullptr)};
 th14_trace_event(12,h,13,weights,weights?width*height*8:0);
}
}
'''

HOST = r'''
trace_events=[];trace_blobs={};trace_bytes=0;trace_initial=None;trace_armed=False
def trace_blob(raw):
 global trace_bytes
 digest=sha(raw)
 if digest not in trace_blobs:
  trace_bytes+=len(raw);assert trace_bytes<=args.trace_byte_budget,'Single-frame trace byte budget exceeded'
  folder=O/'trace-blobs';folder.mkdir(exist_ok=True);(folder/(digest+'.bin')).write_bytes(raw)
  trace_blobs[digest]=dict(file='trace-blobs/'+digest+'.bin',bytes=len(raw),sha256=digest)
 return trace_blobs[digest]
def trace_active():return trace_armed and globals().get('frame_index',0)==args.trace_frame
def trace_event(caller,kind,pointer,count,data,size):
 assert trace_active() and 0<=count<=160 and 0<=size<=64*1024**2
 m=memory(caller);words=list(struct.unpack('<'+'I'*count,m.read(caller,pointer,pointer+count*4)))if count else []
 row=dict(sequence=len(trace_events),kind=kind,words=words)
 if size:row['blob']=trace_blob(bytes(m.read(caller,data,data+size)))
 if kind==1:assert count==125 and words[0]==0x54524331
 trace_events.append(row)
def trace_backend(caller,name,args):
 if not trace_active():return
 m=memory(caller);read=lambda p,n:bytes(m.read(caller,p,p+n))
 words=lambda p,n:list(struct.unpack('<'+'I'*n,read(p,n*4)))
 row=None
 if name=='th14_webgpu_upload':
  handle,w,h,p=args;row=dict(kind=100,words=[handle,w,h],blob=trace_blob(read(p,w*h*4)))
 elif name=='th14_webgpu_draw':
  p,v,n=args;row=dict(kind=101,words=[n,448],blob=trace_blob(read(p,448)+read(v,n*40)))
 elif name=='th14_webgpu_clear':
  target,depth,flags,color,value,stencil,p,count=args
  row=dict(kind=110,words=[target,depth,flags,color,struct.unpack('<I',struct.pack('<f',value))[0],stencil,count],rectangles=words(p,count*4))
 elif name=='th14_webgpu_copy':
  source,p,target,q=args;row=dict(kind=111,words=[source,target],rectangles=words(p,4),point=words(q,2))
 elif name=='th14_webgpu_resample':
  source,p,target,q,data,w,h,im,om=args
  row=dict(kind=112,words=[source,target,w,h],rectangles=words(p,4)+words(q,4),sourceMask=words(im,4),destinationMask=words(om,4))
  if data:row['blob']=trace_blob(read(data,w*h*8))
 elif name=='th14_webgpu_present':row=dict(kind=120,words=list(args))
 elif name=='th14_webgpu_release':row=dict(kind=130,words=list(args))
 if row is not None:row['sequence']=len(trace_events);trace_events.append(row)
def trace_begin():
 global trace_initial,trace_armed
 assert args.backend=='webgpu' and trace_initial is None
 e.flush();resources=[]
 for handle,item in list(e.resources.items()):
  had_target=item['target']is not None
  resources.append(dict(handle=handle,width=item['width'],height=item['height'],hadRenderTarget=had_target,
   dirtyBeforeSnapshot=item['dirty'],pixels=trace_blob(e.read(handle))))
 trace_initial=dict(resources=resources,depths={str(k):dict(format=v['format'],size=v['size'])for k,v in e.depths.items()},
  initialDepthContentsNotCaptured=True,initialGpuColorContentsObservedOnly=True)
 trace_armed=True
def trace_finish():
 global trace_armed
 assert trace_initial is not None
 result=dict(schema='th14/actual-application-render-trace/1',frame=args.trace_frame,
  events=trace_events,initial=trace_initial,uniqueBlobBytes=trace_bytes,uniqueBlobs=len(trace_blobs),
  semanticInputsObservedBeforeBackend=True,nativeValuesProvidedToEngine=False,
  initialDepthContentsNotCaptured=True,sourceToolSha256=sha(tool_raw),backend=args.backend,
  completeGame=False,nativeEquivalent=False,browserAcceptance=False)
 (O/'render-trace.json').write_text(json.dumps(result,indent=2)+'\n')
 trace_armed=False
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--process-host', action='store_true', help='Use the declared startup tick/cookie host instead of the legacy relative-time host')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    renderer_path = ROOT / 'runtimes/th12/portable/sdl/Renderer.cpp'
    renderer_raw = renderer_path.read_bytes()
    renderer = renderer_raw.decode().replace('\r\n', '\n')
    replacements = [
        ('#include "Renderer.hpp"', '#include "Renderer.hpp"\n' + CPP),
        ('\n stats.batches++;', '\n if(th14_trace_active())trace_draw(*this,d,primitive,count,data,size,index,indexFormat,instance,instanceSize);\n stats.batches++;'),
        ('void Renderer::clear(u32 flags,u32 c,float depth,u32 stencil,const i32* rects,u32 count){flush();', 'void Renderer::clear(u32 flags,u32 c,float depth,u32 stencil,const i32* rects,u32 count){flush();if(th14_trace_active())trace_clear(*this,flags,c,depth,stencil,rects,count);'),
        ('void Renderer::copy(u32 src,const i32* rect,u32 dst,const i32* point){flush();', 'void Renderer::copy(u32 src,const i32* rect,u32 dst,const i32* point){flush();if(th14_trace_active())trace_copy(*this,src,rect,dst,point);'),
        ('bool Renderer::resample(u32 src,const i32* from,u32 dst,const i32* to,const float* weights,u32 width,u32 height){', 'bool Renderer::resample(u32 src,const i32* from,u32 dst,const i32* to,const float* weights,u32 width,u32 height){flush();if(th14_trace_active())trace_resample(*this,src,from,dst,to,weights,width,height);'),
        ('void Renderer::present(u32 id){flush();pending=id;', 'void Renderer::present(u32 id){flush();if(th14_trace_active()){const u32 h[]{id};th14_trace_event(20,h,1,nullptr,0);}pending=id;'),
    ]
    for before, after in replacements:
        assert renderer.count(before) == 1, before
        renderer = renderer.replace(before, after)
    sources = {}
    builder_path = ROOT / 'tools/th14-build-native-application.py'
    raw = builder_path.read_bytes(); sources[builder_path.relative_to(ROOT).as_posix()] = SHA(raw)
    builder = raw.decode().replace('\r\n', '\n')
    marker = 'R=Path(__file__).resolve().parents[1]'
    assert builder.count(marker) == 1
    builder = builder.replace(marker, 'R=Path(' + repr(str(ROOT)) + ')')
    marker = "R/'runtimes/th12/portable/sdl/Renderer.cpp'"
    assert builder.count(marker) == 2
    builder = builder.replace(marker, 'Path(' + repr(str(out / 'Renderer.cpp')) + ')')
    marker = "'-I'+str(inc),'-I'+str(src)]"
    assert builder.count(marker) == 1
    builder = builder.replace(marker, "'-I'+str(inc),'-I'+str(src),'-I'+str(R/'runtimes/th12/portable/sdl')]")
    runner_path = ROOT / ('tools/th14-native-application-process-host-oct27.py' if args.process_host else 'tools/th14-native-application.py')
    raw = runner_path.read_bytes(); sources[runner_path.relative_to(ROOT).as_posix()] = SHA(raw)
    runner = raw.decode().replace('\r\n', '\n')
    assert runner.count('R=Path(__file__).resolve().parents[1]') == 1
    runner = runner.replace('R=Path(__file__).resolve().parents[1]', 'R=Path(' + repr(str(ROOT)) + ')')
    marker = 'args=parser.parse_args();B=args.build.resolve();O=args.output.resolve()'
    assert runner.count(marker) == 1
    runner = runner.replace(marker, "parser.add_argument('--trace-frame',type=int,default=2264)\nparser.add_argument('--trace-byte-budget',type=int,default=128*1024**2)\n" + marker + "\nassert 1<=args.trace_frame<=args.maximum_frames and 0<args.trace_byte_budget<=256*1024**2")
    marker = 'def platform(name):'
    assert runner.count(marker) == 1
    runner = runner.replace(marker, HOST + '\n' + marker)
    marker = "  calls[name]+=1\n  if name.startswith('th14_webgpu_')"
    assert runner.count(marker) == 1
    runner = runner.replace(marker, "  calls[name]+=1\n  if name=='th14_trace_active':return int(trace_active())\n  if name=='th14_trace_event':return trace_event(caller,*args)\n  trace_backend(caller,name,args)\n  if name.startswith('th14_webgpu_')")
    marker = "   ok=api['component_tick'](store,held,pause)"
    assert runner.count(marker) == 1
    runner = runner.replace(marker, "   if frame_index==args.trace_frame:trace_begin()\n" + marker + "\n   if frame_index==args.trace_frame:trace_finish()")
    ast.parse(builder); ast.parse(runner)
    out.mkdir(parents=True)
    (out / 'preparer-source.py').write_bytes(Path(__file__).read_bytes())
    for name, source in [('Renderer.cpp', renderer), ('builder.py', builder), ('runner.py', runner)]:
        (out / name).write_text(source, encoding='utf8')
    (out / 'prepared.json').write_text(json.dumps(dict(
        baseSources=sources, baseRendererSha256=SHA(renderer_raw),
        generatedFiles={name: SHA((out / name).read_bytes()) for name in ['Renderer.cpp', 'builder.py', 'runner.py']},
        preparerSha256=SHA(Path(__file__).read_bytes()), productionSourcesChanged=False,
        traceRequiresBaselinePixelEquality=True, initialDepthContentsNotCaptured=True,
        nativeValuesProvidedToEngine=False, completeGame=False, nativeEquivalent=False), indent=2) + '\n')
    print(json.dumps(dict(prepared=True, output=str(out), productionSourcesChanged=False)))


if __name__ == '__main__':
    main()
