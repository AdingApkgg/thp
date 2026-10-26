"""Bounded native WebGPU replay of retained Stage commands, not production.

Mirrors the stated production FFP math in WGSL. No browser, application input,
window or audio device. Every output byte is compared without tolerance.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,math,os,struct,sys,time
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
for name in ['output','wgpu-site','reference']:parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--frames',type=int,default=21);args=parser.parse_args()
sys.path.insert(0,str(args.wgpu_site.resolve(strict=True)));os.environ['WGPU_BACKEND_TYPE']='D3D12'
import wgpu
from wgpu.backends.wgpu_native import _ffi as wgpu_ffi
native_library=Path(wgpu_ffi.lib_path).resolve(strict=True)
native_library_info=dict(name=native_library.name,bytes=native_library.stat().st_size,sha256=hashlib.sha256(native_library.read_bytes()).hexdigest(),versionWord=int(wgpu_ffi.lib.wgpuGetVersion()))
import numpy as np
out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()and 1<=args.frames<=21;out.mkdir(parents=True)
(out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)
started=time.monotonic();SHA=lambda raw:hashlib.sha256(raw).hexdigest();f32=lambda value:struct.unpack('<f',struct.pack('<f',value))[0];from_word=lambda word:struct.unpack('<f',struct.pack('<I',word))[0];to_word=lambda value:struct.unpack('<I',struct.pack('<f',value))[0]
home=args.reference.resolve(strict=True);prepared_raw=(home/'prepared.json').read_bytes();prepared=json.loads(prepared_raw);reference=json.loads((home/'native.json').read_bytes());pixels=(home/'native.bgra').read_bytes();assert SHA(pixels)==reference['pixelsSha256']
adapter=wgpu.gpu.request_adapter_sync(power_preference='high-performance');assert adapter.info['backend_type']=='D3D12'
device=adapter.request_device_sync()
def buffer(data,usage):
 b=device.create_buffer_with_data(data=data,usage=usage|wgpu.BufferUsage.COPY_DST);return b
def rgba(word,reciprocal=False):return[f32(((word>>shift)&255)*f32(1/255)if reciprocal else((word>>shift)&255)/255)for shift in [16,8,0,24]]
def multiply(a,b):
 result=[]
 for col in range(4):
  for row in range(4):
   value=f32(a[row]*b[col*4])
   for k in range(1,4):value=f32(value+f32(a[k*4+row]*b[col*4+k]))
   result.append(value)
 return result
def projectable(points,matrix,viewport):
 epsilon=2**-23;minimum=2**-126;maximum=float.fromhex('0x1.fffffep127')
 if not viewport[2]or not viewport[3]:return False
 if any(not math.isfinite(c)or(c!=0 and abs(c)<minimum)for c in matrix):return False
 for point in points:
  if any(not math.isfinite(c)or(c!=0 and abs(c)<minimum)for c in point):return False
  q=[];error=[]
  for row in range(4):
   products=[matrix[col*4+row]*(1 if col==3 else point[col])for col in range(4)];magnitude=sum(abs(v)for v in products)
   if not math.isfinite(magnitude)or magnitude>maximum*.25:return False
   q.append(sum(products));error.append(8*epsilon*magnitude+8*minimum)
  low_w=q[3]-error[3]
  if not(low_w>0 and q[2]-error[2]>0 and q[2]+error[2]<low_w):return False
  for axis in range(2):
   scale=max(1.,float(viewport[axis+2])*.5);amount=(abs(q[axis])+error[axis])*scale
   if amount>maximum*.25 or amount/low_w>maximum/1024:return False
 return True
def alpha_boundaries():
 shader=device.create_shader_module(code='''
@group(0) @binding(0) var<storage,read> values:array<vec4f>;
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0,1);}
@fragment fn fs(@builtin(position) p:vec4f)->@location(0) vec4f{return vec4f(0,0,0,values[u32(p.x)].x);}''')
 pipeline=device.create_render_pipeline(layout='auto',vertex={'module':shader,'entry_point':'vs'},fragment={'module':shader,'entry_point':'fs','targets':[{'format':'bgra8unorm'}]})
 values=device.create_buffer(size=4096,usage=wgpu.BufferUsage.STORAGE|wgpu.BufferUsage.COPY_DST);bind=device.create_bind_group(layout=pipeline.get_bind_group_layout(0),entries=[{'binding':0,'resource':{'buffer':values}}]);target=device.create_texture(size=(256,1,1),format='bgra8unorm',usage=wgpu.TextureUsage.RENDER_ATTACHMENT|wgpu.TextureUsage.COPY_SRC)
 def sample(words):
  payload=np.zeros((256,4),dtype='<f4');payload[:,0]=np.asarray(words,dtype='<u4').view('<f4');device.queue.write_buffer(values,0,payload)
  encoder=device.create_command_encoder();render=encoder.begin_render_pass(color_attachments=[{'view':target.create_view(),'load_op':'clear','store_op':'store','clear_value':(0,0,0,0)}]);render.set_pipeline(pipeline);render.set_bind_group(0,bind);render.draw(3);render.end();device.queue.submit([encoder.finish()]);return bytes(device.queue.read_texture({'texture':target},{'offset':0,'bytes_per_row':1024,'rows_per_image':1},(256,1,1)))[3::4]
 lo=[0]+[to_word((i-1)/255)for i in range(1,256)];hi=[0]+[to_word(i/255)for i in range(1,256)]
 for _ in range(32):
  if all(hi[i]-lo[i]<=1 for i in range(1,256)):break
  middle=[lo[i]+(hi[i]-lo[i])//2 for i in range(256)];result=sample(middle)
  for i in range(1,256):
   if hi[i]-lo[i]>1:
    if result[i]>=i:hi[i]=middle[i]
    else:lo[i]=middle[i]
 lower,upper=sample(lo),sample(hi)
 for i in range(1,256):assert hi[i]-lo[i]==1 and lower[i]<i<=upper[i]
 target.destroy();values.destroy();return[from_word(word)for word in hi]
boundaries=alpha_boundaries();(out/'alpha-boundaries.json').write_text(json.dumps(boundaries)+'\n')
shader_source='''
struct Uniform{factor:vec4f,fogColor:vec4f,flags:vec4u,alpha:vec4f,color:vec4u,args:vec4u,clipMatrix:mat4x4f,eyeMatrix:mat4x4f,uvMatrix:mat4x4f,linearFog:vec4f,vertexFlags:vec4u,viewport:vec4f};
@group(0) @binding(0) var<uniform> u:Uniform;
@group(1) @binding(0) var tex:texture_2d<f32>;
@group(1) @binding(1) var texSampler:sampler;
struct Input{@location(0) clip:vec4f,@location(1) color:vec4f,@location(2) uv:vec2f,@location(3) fog:f32,@location(4) eligible:f32};
struct Output{@builtin(position) position:vec4f,@location(0) color:vec4f,@location(1) uv:vec2f,@location(2) fog:f32};
fn round_even(v:vec2f)->vec2f{let a=floor(v);let fraction=v-a;return select(select(a,a+1.0,fraction>vec2f(0.5)),select(a,a+1.0,(vec2i(a)&vec2i(1))!=vec2i(0)),fraction==vec2f(0.5));}
@vertex fn vs(v:Input)->Output{var o:Output;o.position=v.clip;o.color=v.color.bgra;o.uv=v.uv;o.fog=v.fog;
 if(u.vertexFlags.x==0u){let original=vec4f(v.clip.xyz,1);o.position=u.clipMatrix*original;
 if(v.eligible>0.5){let half_viewport=u.viewport.zw*0.5;let pixel=round_even(((vec2f(o.position.x,-o.position.y)*half_viewport)/o.position.w+half_viewport)*256.0)/256.0;o.position.x=(pixel.x/half_viewport.x-1.0)*o.position.w;o.position.y=-(pixel.y/half_viewport.y-1.0)*o.position.w;}
 if(u.vertexFlags.y!=0u){o.uv=(u.uvMatrix*vec4f(v.uv,1,0)).xy;}
 if(u.flags.x!=0u){let z=abs((u.eyeMatrix*original).z);o.fog=u.linearFog.x-z*u.linearFog.y;}else{o.fog=1;}}
 return o;}
fn argument(value:u32,t:vec4f,c:vec4f)->vec4f{var result=c;let source=value&15u;if(source==2u){result=t;}else if(source==3u){result=u.factor;}else if(source==4u){result=vec4f(0);}
 if((value&16u)!=0u){result=1.0-result;}if((value&32u)!=0u){result=vec4f(result.a);}return result;}
fn operation(mode:u32,a:vec4f,b:vec4f)->vec4f{if(mode==2u){return a;}if(mode==3u){return b;}if(mode==4u){return a*b;}if(mode==5u){return a*b*2.0;}if(mode==6u){return a*b*4.0;}if(mode==7u){return a+b;}if(mode==8u){return a+b-0.5;}if(mode==9u){return(a+b-0.5)*2.0;}if(mode==10u){return a-b;}return a;}
struct FragmentOut{@location(0) color:vec4f,@builtin(frag_depth) depth:f32};
@fragment fn fs(v:Output)->FragmentOut{let t=textureSample(tex,texSampler,v.uv);var c=v.color;if(u.flags.w!=0u){c=clamp(operation(u.color.x,argument(u.color.z,t,v.color),argument(u.color.w,t,v.color)),vec4f(0),vec4f(1));c.a=clamp(operation(u.color.y,argument(u.args.x,t,v.color),argument(u.args.y,t,v.color)).a,0.0,1.0);}
 if(u.flags.y!=0u){var accepted=true;let f=u.flags.z;let ge=c.a>=u.alpha.x;let gt=c.a>=u.alpha.y;if(f==1u){accepted=false;}else if(f==2u){accepted=!ge;}else if(f==3u){accepted=ge&&!gt;}else if(f==4u){accepted=!gt;}else if(f==5u){accepted=gt;}else if(f==6u){accepted=!ge||gt;}else if(f==7u){accepted=ge;}if(!accepted){discard;}}
 if(u.flags.x!=0u){let fog=clamp(v.fog,0.0,1.0);let rest=u.fogColor.rgb-u.fogColor.rgb*fog;c=vec4f(c.rgb*fog+rest,c.a);}
 let quantized=floor(v.position.z*1048576.0)/1048576.0;let scaled=quantized*65536.0;let depth=(floor(scaled)+ceil(fract(scaled)-quantized-0.5))/65535.0;return FragmentOut(c,depth);}
'''
(out/'shader.wgsl').write_bytes(shader_source.encode());shader=device.create_shader_module(code=shader_source)
pipelines={};textures={};texture_bindings={}
def pipeline_for(rs):
 key=tuple(rs[i]for i in [14,23,19,20,171])
 if key in pipelines:return pipelines[key]
 assert rs[19]==5 and rs[20]in[2,6]and rs[171]in[1,3]and rs[23]in[4,8]
 part={'src_factor':'src-alpha','dst_factor':'one'if rs[20]==2 else'one-minus-src-alpha','operation':'reverse-subtract'if rs[171]==3 else'add'}
 pipeline=device.create_render_pipeline(label=str(key),layout='auto',vertex={'module':shader,'entry_point':'vs','buffers':[{'array_stride':36,'attributes':[{'shader_location':0,'offset':0,'format':'float32x4'},{'shader_location':1,'offset':16,'format':'unorm8x4'},{'shader_location':2,'offset':20,'format':'float32x2'},{'shader_location':3,'offset':28,'format':'float32'},{'shader_location':4,'offset':32,'format':'float32'}]}]},fragment={'module':shader,'entry_point':'fs','targets':[{'format':'bgra8unorm','blend':{'color':part,'alpha':part}}]},primitive={'topology':'triangle-list'},depth_stencil={'format':'depth16unorm','depth_write_enabled':bool(rs[14]),'depth_compare':'less-equal'if rs[23]==4 else'always'})
 pipelines[key]=pipeline;return pipeline
for meta in prepared['textures']+[dict(handle=0,width=1,height=1,format=21,pitch=4,inline=b'\xff'*4)]:
 original=meta.get('inline')or(home/meta['file']).read_bytes()
 if'sha256'in meta:assert SHA(original)==meta['sha256']
 width,height,fmt=meta['width'],meta['height'],meta['format'];texture_format='bgra8unorm';bytes_per_pixel=4
 if fmt==21:data=original
 else:
  assert fmt in [23,26];words=np.ndarray((height,width),dtype='<u2',buffer=original,strides=(meta['pitch'],2))
  if fmt==23:
   values=np.empty((height,width,4),dtype=np.uint8)
   low=words&31;green=(words>>5)&63;high=(words>>11)&31
   values[:,:,0]=(low<<3)|(low>>2);values[:,:,1]=(green<<2)|(green>>4);values[:,:,2]=(high<<3)|(high>>2);values[:,:,3]=255
   data=values.tobytes()
  else:
   values=np.empty((height,width,4),dtype=np.uint8)
   for channel,shift in enumerate([0,4,8,12]):values[:,:,channel]=((words>>shift)&15)*17
   data=values.tobytes()
 texture=device.create_texture(size=(width,height,1),format=texture_format,usage=wgpu.TextureUsage.TEXTURE_BINDING|wgpu.TextureUsage.COPY_DST);device.queue.write_texture({'texture':texture},data,{'bytes_per_row':width*bytes_per_pixel},(width,height,1));textures[meta['handle']]=texture
def texture_binding(handle,ss,pipeline):
 key=(id(pipeline),handle,*[ss[i]for i in [1,2,5,6]])
 if key not in texture_bindings:
  address=lambda value:'repeat'if value==1 else'mirror-repeat'if value==2 else'clamp-to-edge'
  sampler=device.create_sampler(address_mode_u=address(ss[1]),address_mode_v=address(ss[2]),mag_filter='nearest'if ss[5]==1 else'linear',min_filter='nearest'if ss[6]==1 else'linear')
  texture_bindings[key]=device.create_bind_group(layout=pipeline.get_bind_group_layout(1),entries=[{'binding':0,'resource':textures[handle].create_view()},{'binding':1,'resource':sampler}])
 return texture_bindings[key]
identity=[float(i%5==0)for i in range(16)];reports=[]
for frame in prepared['frames'][:args.frames]:
 assert time.monotonic()-started<300;storage.check_budget(out)
 rs={7:1,14:1,15:1,19:5,20:6,22:1,23:8,24:1,25:7,27:1,28:1,34:0xffa0a0a0,35:0,36:to_word(1000),37:to_word(5000),38:to_word(1),48:0,137:0,140:3,161:0,168:15,171:1,194:0,206:0,60:0xffffffff};ts={1:4,2:2,3:3,4:4,5:2,6:3,11:0,24:2};ss={1:1,2:1,5:2,6:2,7:0,11:0};matrices={key:identity[:]for key in [256,2,3,16]};texture=0;viewport=[0,0,640,480,0,1];fvf=0;clear_color=0xff42678b;clear_depth=1;draws=[];vertices=bytearray();uniform=bytearray(frame['directDraws']*512)
 for command in frame['initialState']+frame['commands']:
  kind=command['kind']
  if kind=='renderState':rs[command['key']]=command['value']
  elif kind=='textureStageState':
   if command['stage']==0:ts[command['key']]=command['value']
  elif kind=='samplerState':
   if command['sampler']==0:ss[command['key']]=command['value']
  elif kind=='transform':matrices[command['key']]=[from_word(v)for v in command['words']]
  elif kind=='texture':assert command['sampler']==0;texture=command['handle']
  elif kind=='viewport':viewport=[v if i<4 else from_word(v)for i,v in enumerate(command['words'])]
  elif kind=='fvf':fvf=command['value']
  elif kind=='clear':
   assert not draws
   if command['rectangles']:assert command['rectangles']==[0,0,640,480]
   if command['flags']&1:clear_color=command['color']
   if command['flags']&2:clear_depth=from_word(command['depthWord'])
  elif kind=='draw':
   assert command['topology']==5 and fvf in[0x44,0x102,0x142]and command['stride']==(24 if fvf==0x142 else 20)
   assert rs[48]==0 and rs[140]==3 and ts[24]in[0,2]and rs[27]==1 and rs[7]==1 and rs[206]==0 and rs[168]==15 and rs[194]==0 and rs[22]==1
   assert all(ts[key]in range(2,11)for key in[1,4])
   stride=command['stride']//4;records=[command['words'][i:i+stride]for i in range(0,len(command['words']),stride)];assert len(records)==command['count']+2
   eye=multiply(matrices[2],matrices[256]);clip=multiply(matrices[3],eye);near,far=from_word(rs[36]),from_word(rs[37]);scale=f32(1/f32(far-near));bias=f32(far*scale);first=len(vertices)//36
   positions=[[from_word(v)for v in record[:3]]for record in records];quad_eligible=fvf==0x102 and command['count']==2 and projectable(positions,clip,viewport)
   for triangle in range(command['count']):
    indices=[triangle,triangle+1,triangle+2]if triangle%2==0 else[triangle+1,triangle,triangle+2]
    eligible=quad_eligible if fvf==0x102 and command['count']==2 else fvf!=0x44 and projectable([positions[i]for i in indices],clip,viewport)
    for index in indices:
     words=records[index];point=positions[index]
     if fvf==0x44:
      x,y,w,h=viewport[:4];rhw=from_word(words[3]);sx=f32(round(f32(f32(point[0]-x)*256))/256);sy=f32(round(f32(f32(point[1]-y)*256))/256);q=[f32(f32(f32(sx/w)*2-1)/rhw),f32(-f32(f32(sy/h)*2-1)/rhw),f32(point[2]/rhw),f32(1/rhw)];color=words[4];uv=[0,0]
     else:q=point+[1];color=words[3]if fvf==0x142 else 0xffffffff;uv=[from_word(v)for v in words[-2:]]
     vertices.extend(struct.pack('<4fI4f',*q,color,*uv,1.,float(eligible)))
   at=len(draws)*512
   for offset,values,fmt in[(0,rgba(rs[60]),'f'),(16,rgba(rs[34],True),'f'),(32,[rs[28],rs[15],rs[25],int(texture!=0)],'I'),(48,[boundaries[rs[24]],2 if rs[24]==255 else boundaries[rs[24]+1],0,0],'f'),(64,[ts[1],ts[4],ts[2],ts[3],ts[5],ts[6],0,0],'I'),(96,clip,'f'),(160,eye,'f'),(224,matrices[16],'f'),(288,[bias,scale,0,0],'f'),(304,[int(fvf==0x44),int(ts[24]==2),0,0],'I'),(320,viewport[:4],'f')]:struct.pack_into('<'+fmt*len(values),uniform,at+offset,*values)
   pipeline=pipeline_for(rs);draws.append(dict(first=first,count=command['count']*3,offset=at,viewport=viewport[:],pipeline=pipeline,texture=texture_binding(texture,ss,pipeline)))
  else:assert kind in['controlledScreenQueue','controlledScreenFlush'],kind
 assert len(draws)==frame['directDraws']
 vertex_buffer=buffer(vertices,wgpu.BufferUsage.VERTEX);uniform_buffer=buffer(uniform,wgpu.BufferUsage.UNIFORM)
 binds=[device.create_bind_group(layout=draw['pipeline'].get_bind_group_layout(0),entries=[{'binding':0,'resource':{'buffer':uniform_buffer,'offset':draw['offset'],'size':336}}])for draw in draws]
 target=device.create_texture(size=(641,481,1),format='bgra8unorm',usage=wgpu.TextureUsage.RENDER_ATTACHMENT|wgpu.TextureUsage.COPY_SRC);depth=device.create_texture(size=(641,481,1),format='depth16unorm',usage=wgpu.TextureUsage.RENDER_ATTACHMENT)
 encoder=device.create_command_encoder();render=encoder.begin_render_pass(color_attachments=[{'view':target.create_view(),'load_op':'clear','store_op':'store','clear_value':rgba(clear_color)}],depth_stencil_attachment={'view':depth.create_view(),'depth_load_op':'clear','depth_store_op':'store','depth_clear_value':clear_depth});render.set_scissor_rect(0,0,640,480);render.set_vertex_buffer(0,vertex_buffer)
 for index,draw in enumerate(draws):
  x,y,w,h,minimum,maximum=draw['viewport'];render.set_viewport(x+.5,y+.5,w,h,minimum,maximum);render.set_pipeline(draw['pipeline']);render.set_bind_group(0,binds[index]);render.set_bind_group(1,draw['texture']);render.draw(draw['count'],1,draw['first'])
 render.end();device.queue.submit([encoder.finish()]);actual=bytes(device.queue.read_texture({'texture':target},{'offset':0,'bytes_per_row':2560,'rows_per_image':480},(640,480,1)));assert len(actual)==640*480*4
 reference_frame=next(row for row in reference['frames']if(row['stage'],row['frame'])==(frame['stage'],frame['frame']));expected=pixels[reference_frame['offset']:reference_frame['offset']+reference_frame['bytes']];assert SHA(expected)==reference_frame['sha256']
 a=np.frombuffer(actual,dtype=np.uint8);b=np.frombuffer(expected,dtype=np.uint8);different=np.flatnonzero(a!=b);first=[]
 for i in different[:12]:
  i=int(i);first.append(dict(x=i//4%640,y=i//2560,channel=i%4,actual=int(a[i]),native=int(b[i])))
 row=dict(stage=frame['stage'],frame=frame['frame'],differentChannels=len(different),actualSha256=SHA(actual),nativeSha256=SHA(expected),first=first);reports.append(row);(out/f"stage{frame['stage']}-frame{frame['frame']}.bgra").write_bytes(actual);print(json.dumps(row),flush=True)
 for resource in[target,depth,vertex_buffer,uniform_buffer]:resource.destroy()
 result=dict(schema='th14/native-webgpu-stage/1',nativeWgpuComponent=True,adapter=dict(adapter.info),wgpuVersion=wgpu.__version__,requiredFeatures=[],backend='D3D12',frames=len(reports),exactFrames=sum(row['differentChannels']==0 for row in reports),differentChannels=sum(row['differentChannels']for row in reports),rows=reports,preparedSha256=SHA(prepared_raw),nativePixelsSha256=SHA(pixels),shaderSha256=SHA(shader_source.encode()),toolSha256=SHA(Path(__file__).read_bytes()),actualProductionCppRenderer=False,productionSemanticsPartiallyMirrored=True,postclipFractionalViewport=True,packedRgb565ExpandedToFloat32=False,packedRgb565BitReplicatedTo8=True,alphaConversionMeasuredOnOwnDevice=True,browserRun=False,appUiControlled=False,physicalAudioDevicesOpened=0,productionChanged=False,completeGame=False,nativeEquivalent=False,elapsedSeconds=time.monotonic()-started,sourceBindings={path:SHA((R/path).read_bytes())for path in ['runtimes/th12/portable/sdl/Renderer.cpp','runtimes/th12/portable/sdl/Shaders.hpp','runtimes/th12/portable/sdl/GraphicsState.hpp']},scope='WGSL mirror of the stated fixed-function subset and retained Stage commands. The C++ renderer is not executed; no production WebGPU backend or browser is tested. Same screen-queue exclusions as the reference. Uses only declared core WebGPU features; no native pixels are used as renderer inputs.')
 result['wgpuNativeLibrary']=native_library_info
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
for texture in textures.values():texture.destroy()
device.destroy();sys.exit(0 if result['exactFrames']==result['frames']else 1)
