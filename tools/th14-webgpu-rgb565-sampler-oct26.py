"""Compare isolated RGB565/float texture sampling on our own native devices."""
from pathlib import Path
import argparse,ctypes as C,hashlib,importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
for name in ['output','wgpu-site','angle-directory']:parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args();sys.path.insert(0,str(args.wgpu_site.resolve(strict=True)));os.environ['WGPU_BACKEND_TYPE']='D3D12'
import numpy as np
import wgpu
from wgpu.backends.wgpu_native import _ffi as wgpu_ffi
native_library=Path(wgpu_ffi.lib_path).resolve(strict=True)
native_library_info=dict(name=native_library.name,bytes=native_library.stat().st_size,sha256=hashlib.sha256(native_library.read_bytes()).hexdigest(),versionWord=int(wgpu_ffi.lib.wgpuGetVersion()))
out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
(out/'run-tool.py').write_bytes(Path(__file__).read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)
spec=importlib.util.spec_from_file_location('gles',R/'tools/th14-native-gles-context.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);e=g.Context(args.angle_directory.resolve(strict=True));gles_info=e.info
def gl(name,result,*args):return g.fn(e.gles,name,result,*args)
U,I,F,P=C.c_uint,C.c_int,C.c_float,C.c_void_p
def shader(kind,source):
 handle=gl('glCreateShader',U,U)(kind);data=C.c_char_p(source.encode());gl('glShaderSource',None,U,I,C.POINTER(C.c_char_p),P)(handle,1,C.byref(data),None);gl('glCompileShader',None,U)(handle);ok=I();gl('glGetShaderiv',None,U,U,C.POINTER(I))(handle,0x8b81,C.byref(ok));assert ok.value;return handle
vs=shader(0x8b31,'#version 300 es\nvoid main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));gl_Position=vec4(p*2.0-1.0,0,1);}')
fs=shader(0x8b30,'#version 300 es\nprecision highp float;uniform highp sampler2D tex;out vec4 color;void main(){color=texture(tex,(floor(gl_FragCoord.xy)+vec2(0.75))*(1.0/256.0));}')
program=gl('glCreateProgram',U)();gl('glAttachShader',None,U,U)(program,vs);gl('glAttachShader',None,U,U)(program,fs);gl('glLinkProgram',None,U)(program);ok=I();gl('glGetProgramiv',None,U,U,C.POINTER(I))(program,0x8b82,C.byref(ok));assert ok.value;gl('glUseProgram',None,U)(program)
vao=U();gl('glGenVertexArrays',None,I,C.POINTER(U))(1,C.byref(vao));gl('glBindVertexArray',None,U)(vao)
packed=np.arange(65536,dtype='<u2').reshape((256,256))
native_source=np.stack([(packed>>11)&31,(packed>>5)&63,packed&31],axis=-1)
color32=np.empty((256,256,4),dtype=np.uint8)
color32[:,:,0]=(native_source[:,:,0]<<3)|(native_source[:,:,0]>>2)
color32[:,:,1]=(native_source[:,:,1]<<2)|(native_source[:,:,1]>>4)
color32[:,:,2]=(native_source[:,:,2]<<3)|(native_source[:,:,2]>>2);color32[:,:,3]=255
color8=np.floor(native_source.astype(np.float64)*255/np.array([31,63,31])+.5).astype(np.uint8)
def texture(internal,fmt,kind,w,h,data):
 handle=U();gl('glGenTextures',None,I,C.POINTER(U))(1,C.byref(handle));gl('glBindTexture',None,U,U)(0xde1,handle)
 gl('glTexImage2D',None,U,I,I,I,I,I,U,U,P)(0xde1,0,internal,w,h,0,fmt,kind,data.ctypes.data if data is not None else None)
 for key,value in[(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812f),(0x2803,0x812f)]:gl('glTexParameteri',None,U,U,I)(0xde1,key,value)
 return handle.value
gl('glPixelStorei',None,U,I)(0xcf5,1)
source565=texture(0x8d62,0x1907,0x1401,256,256,color8);source32=texture(0x8058,0x1908,0x1401,256,256,color32)
target=texture(0x8814,0x1908,0x1406,256,256,None);fbo=U();gl('glGenFramebuffers',None,I,C.POINTER(U))(1,C.byref(fbo));gl('glBindFramebuffer',None,U,U)(0x8d40,fbo);gl('glFramebufferTexture2D',None,U,U,U,U,I)(0x8d40,0x8ce0,0xde1,target,0);assert gl('glCheckFramebufferStatus',U,U)(0x8d40)==0x8cd5
gl('glViewport',None,I,I,I,I)(0,0,256,256)
outputs={}
for name,handle,filter_value in [('gles565-nearest',source565,0x2600),('gles8-nearest',source32,0x2600),('gles565-linear',source565,0x2601),('gles8-linear',source32,0x2601)]:
 gl('glBindTexture',None,U,U)(0xde1,handle);gl('glTexParameteri',None,U,U,I)(0xde1,0x2801,filter_value);gl('glTexParameteri',None,U,U,I)(0xde1,0x2800,filter_value);gl('glDrawArrays',None,U,I,I)(4,0,3);data=np.zeros((256,256,4),dtype='<f4');gl('glReadPixels',None,I,I,I,I,U,U,P)(0,0,256,256,0x1908,0x1406,data.ctypes.data);assert gl('glGetError',U)()==0;outputs[name]=data.reshape((-1,4))
e.close()
adapter=wgpu.gpu.request_adapter_sync(power_preference='high-performance');assert adapter.info['backend_type']=='D3D12';device=adapter.request_device_sync()
source=device.create_texture(size=(256,256,1),format='rgba8unorm',usage=wgpu.TextureUsage.TEXTURE_BINDING|wgpu.TextureUsage.COPY_DST);device.queue.write_texture({'texture':source},color32,{'bytes_per_row':1024},(256,256,1))
code='''@group(0) @binding(0) var tex:texture_2d<f32>;@group(0) @binding(1) var smp:sampler;
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0,1);}
@fragment fn fs(@builtin(position) p:vec4f)->@location(0) vec4f{return textureSample(tex,smp,(floor(p.xy)+vec2f(0.75))*(1.0/256.0));}'''
module=device.create_shader_module(code=code);pipeline=device.create_render_pipeline(layout='auto',vertex={'module':module,'entry_point':'vs'},fragment={'module':module,'entry_point':'fs','targets':[{'format':'rgba32float'}]});smp=device.create_sampler(min_filter='linear',mag_filter='linear',address_mode_u='clamp-to-edge',address_mode_v='clamp-to-edge');bind=device.create_bind_group(layout=pipeline.get_bind_group_layout(0),entries=[{'binding':0,'resource':source.create_view()},{'binding':1,'resource':smp}])
target=device.create_texture(size=(256,256,1),format='rgba32float',usage=wgpu.TextureUsage.RENDER_ATTACHMENT|wgpu.TextureUsage.COPY_SRC);encoder=device.create_command_encoder();render=encoder.begin_render_pass(color_attachments=[{'view':target.create_view(),'load_op':'clear','store_op':'store','clear_value':(0,0,0,0)}]);render.set_pipeline(pipeline);render.set_bind_group(0,bind);render.draw(3);render.end();device.queue.submit([encoder.finish()]);raw=bytes(device.queue.read_texture({'texture':target},{'offset':0,'bytes_per_row':4096,'rows_per_image':256},(256,256,1)));outputs['wgpu8-linear']=np.frombuffer(raw,dtype='<f4').reshape((-1,4)).copy();target.destroy();source.destroy();device.destroy()
for name,data in outputs.items():(out/(name+'.f32')).write_bytes(data.tobytes())
tests={}
for left,right in [('gles565-nearest','gles8-nearest'),('gles565-linear','gles8-linear'),('gles565-linear','wgpu8-linear')]:
 native,data=outputs[left],outputs[right];delta=np.abs(data-native);where=np.argwhere(data.view('<u4')!=native.view('<u4'));tests[left+'-vs-'+right]=dict(differentWords=len(where),maxAbsoluteDifference=float(delta.max()),first=[dict(pixel=int(i),channel=int(c),native=float(native[i,c]),actual=float(data[i,c]))for i,c in where[:8]])
result=dict(schema='th14/native-webgpu-rgb565/1',tests=tests,sourceWordCount=65536,sourceEncoding='all16bitwords ascending',selectedSamples={name:{str(index):data[index].tolist()for index in [0,64,128,192,256]}for name,data in outputs.items()},outputs={name:sha(data.tobytes())for name,data in outputs.items()},glesInfo=gles_info,wgpuAdapter=dict(adapter.info),wgpuVersion=wgpu.__version__,requiredFeatures=[],samplerModes=['nearest','linear'],linearTexelFraction=[0.25,0.25],ownOffscreenDevicesOnly=True,physicalAudioDevicesOpened=0,browserRun=False,productionChanged=False,toolSha256=sha(Path(__file__).read_bytes()))
result['wgpuNativeLibrary']=native_library_info
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(tests));assert all(test['differentWords']==0 for test in tests.values())
