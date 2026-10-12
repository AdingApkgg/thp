"""Expand measured shape vertices across 8-bit subpixel midpoint neighborhoods.

These are controlled raster inputs derived from recorded shapes. The retail
dispatcher is not rerun for the translated/perspective variants.
"""
import json,struct,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'artifacts/th14/gpu-screen-grid';OUT.mkdir(parents=True,exist_ok=True)
oracle_path=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'
oracle=json.loads(oracle_path.read_bytes());cases=[];words=[];draw_records=[];case_records=[];offset=0
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
for base_index in [424,439,512,527,423,694]:
 for axis in range(2):
  for place in [2,15,62,127,239,431]:
   midpoint=struct.unpack('<I',struct.pack('<f',place+.5/256))[0]
   for neighbor in [-2,-1,0,1,2]:
    target=struct.unpack('<f',struct.pack('<I',midpoint+neighbor))[0]
    for rhw in range(2):
     source=oracle['shapes'][base_index];translation=target-source['draws'][0]['vertices'][0][axis];draws=[]
     for d in source['draws']:
      vertices=[]
      for i,v in enumerate(d['vertices']):
       vertex=v[:];vertex[axis]=f32(vertex[axis]+translation)
       if rhw:vertex[3]=[.75,1.25,1.5,.5][i%4]
       vertices.append(vertex)
      draws.append(dict(topology=d['topology'],count=d['count'],stride=20,vertices=vertices))
     draws[0]['vertices'][0][axis]=target
     vs=[v for d in draws for v in d['vertices']]
     left=max(0,math.floor(min(v[0] for v in vs))-2);top=max(0,math.floor(min(v[1] for v in vs))-2)
     right=min(640,math.ceil(max(v[0] for v in vs))+3);bottom=min(480,math.ceil(max(v[1] for v in vs))+3)
     if left>=right or top>=bottom:left=top=0;right=bottom=1
     crop=[left,top,right-left,bottom-top];size=crop[2]*crop[3]*4
     row=dict(index=len(cases),baseIndex=base_index,axis=axis,place=place,neighbor=neighbor,rhw=rhw,target=target,crop=crop,offset=offset,size=size,status=0,drawCount=len(draws),draws=draws)
     cases.append(row);offset+=size;case_records.append((len(draw_records),len(draws),*crop))
     for d in draws:
      start=len(words)
      for v in d['vertices']:words.extend(struct.unpack('<5I',struct.pack('<4fI',*v)))
      draw_records.append((d['topology']-1,d['count'],start))
array=lambda rows:','.join('{'+','.join(str(v)+'u' for v in row)+'}' for row in rows)
data='struct GridDraw {u32 topology,count,offset;};\nstruct GridCase {u32 start,count,left,top,width,height;};\n'
data+='static constexpr u32 grid_words[]={'+','.join(hex(w)+'u' for w in words)+'};\n'
data+='static constexpr GridDraw grid_draws[]={'+array(draw_records)+'};\nstatic constexpr GridCase grid_cases[]={'+array(case_records)+'};\n'
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-screen-grid-data.hpp').write_text(data,encoding='utf8')
(OUT/'prepared.json').write_text(json.dumps(dict(cases=cases,bytes=offset,width=640,height=480,renderOracleSha256=hashlib.sha256(oracle_path.read_bytes()).hexdigest(),prepareToolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),completeGame=False,nativeEquivalent=False,limits='Controlled translated and variable-RHW inputs derived from six original-recorded shape cases, not original dispatcher execution for these variants. Six positions on each screen axis, five adjacent float32 bit values around an 8-bit subpixel midpoint, with constant or varying reciprocal-W. Actual native/portable raster outputs are compared.'),indent=2)+'\n',encoding='utf8')
native=(ROOT/'tools/th14-gpu-original-shapes-native.py').read_text(encoding='utf8').replace("OUT=ROOT/'artifacts/th14/gpu-original-shapes'","OUT=ROOT/'artifacts/th14/gpu-screen-grid'")
native=native.replace("source=materials['shapes'][row['index']]","source=row")
native=native.replace('Recorded original','Controlled derived').replace('recorded original','controlled derived')
(ROOT/'tools/th14-gpu-screen-grid-native.py').write_text(native,encoding='utf8')
html=(ROOT/'tools/th14-gpu-original-shapes-variants.html').read_text(encoding='utf8').replace("||'clip-linear'","||'before'").replace('_gpu_original_shape_case','_gpu_screen_grid_case').replace('810 场景','720 场景').replace('原作形状绘制对照','屏幕子像素边界对照')
html=html.replace('原作实际记录的矩形、渐变、边框、圆面和线条顶点送入 Direct3D9；移植代码独立计算并送入生产 SDL/WebGL。保留 640×480 像素网格，不代表完整游戏帧。','从原作顶点生成平移与透视变化的受控输入，测试 1/256 像素中点附近的相邻 float32 值。两侧绘制同一输入，不代表这些变体执行过原版绘制分发。')
html=html.replace('mode:c.mode,anchor:c.anchor,parent:c.parent,resolution:c.resolution,','baseIndex:c.baseIndex,axis:c.axis,place:c.place,neighbor:c.neighbor,rhw:c.rhw,')
(ROOT/'tools/th14-gpu-screen-grid.html').write_text(html,encoding='utf8')
print(f'Prepared {len(cases)} controlled subpixel boundary cases, {offset} bytes')
