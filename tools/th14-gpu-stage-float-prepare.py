"""Generate reviewable RGBA32F stage-fog diagnostics from existing fixtures.

Original assets and the production renderer remain read-only.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def replace_one(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
native=(ROOT/'tools/th14-gpu-stage-fog-native.py').read_text(encoding='utf-8-sig')
native=replace_one(native,"artifacts/th14/gpu-stage-fog'","artifacts/th14/gpu-stage-float'")
native=replace_one(native,"profiles=json.loads((OUT/'profiles.json').read_text())['profiles']","profiles=json.loads((ROOT/'artifacts/th14/gpu-stage-fog/profiles.json').read_text())['profiles']")
native=replace_one(native,'sha((OUT/"profiles.json").read_bytes())','sha((ROOT/"artifacts/th14/gpu-stage-fog/profiles.json").read_bytes())')
assert native.count('[32,32,21,')==2
native=native.replace('[32,32,21,','[32,32,116,')
native=replace_one(native,'lock.bits+y*lock.pitch,128','lock.bits+y*lock.pitch,512')
native=replace_one(native,"out/'native.bgra'","out/'native.rgba32f'")
native=replace_one(native,'report=dict(generated=True,','report=dict(generated=True,outputFormat="A32B32G32R32F",outputByteOrder="RGBA float32 little endian",')
(ROOT/'tools/th14-gpu-stage-float-native.py').write_text(native,encoding='utf8')
fixture=(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-world-direct-float-fixture.cpp').read_text()
fixture=replace_one(fixture,'th14-gpu-world-profiles-fixture.cpp','th14-gpu-stage-fog-fixture.cpp')
fixture=replace_one(fixture,'gpu_world_direct_float_case','gpu_stage_direct_float_case')
fixture=replace_one(fixture,'gpu_world_profile_case','gpu_stage_fog_case')
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-direct-float-fixture.cpp').write_text(fixture,encoding='utf8')
builder=(ROOT/'tools/th14-gpu-world-direct-float-build.mjs').read_text()
builder=replace_one(builder,"out=resolve(root,'artifacts/th14/gpu-world-profiles')","out=resolve(root,'artifacts/th14/gpu-stage-fog')")
builder=replace_one(builder,"['control','euler-color']","['before','candidate']")
builder=builder.replace('th14-gpu-world-direct-float-fixture.cpp','th14-gpu-stage-direct-float-fixture.cpp')
builder=builder.replace('_gpu_world_direct_float_case','_gpu_stage_direct_float_case')
builder=builder.replace('th14-gpu-world-profiles-fixture.cpp','th14-gpu-stage-fog-fixture.cpp')
builder=builder.replace('artifacts/th14/gpu-world-profiles-float/native.json','artifacts/th14/gpu-stage-float/native.json')
(ROOT/'tools/th14-gpu-stage-direct-float-build.mjs').write_text(builder,encoding='utf8')
page=(ROOT/'tools/th14-gpu-world-direct-float.html').read_text(encoding='utf8')
page=page.replace('1920','7104').replace('direct-float-control','direct-float-before').replace('direct-float-euler-color','direct-float-candidate')
page=page.replace('/direct','/stage-direct').replace('./colors/','./stage-float/').replace("fetch('./'+variant","fetch('./stage/'+variant").replace("import('./'+variant","import('./stage/'+variant")
page=page.replace('_gpu_world_direct_float_case','_gpu_stage_direct_float_case')
start=page.index('const points=' )+len('const points=');end=page.index(',actual=',start)
page=page[:start]+'[[2127,25,10],[2823,16,14],[2831,16,14],[3087,25,10],[3855,25,10],[4070,13,5],[4623,25,10],[6543,25,10],[6735,25,10]]'+page[end:]
(ROOT/'tools/th14-gpu-stage-direct-float.html').write_text(page,encoding='utf8')
coefficient=replace_one(native,"artifacts/th14/gpu-stage-float'","artifacts/th14/gpu-stage-coefficient'")
coefficient=replace_one(coefficient,'((1,4),(2,2),(3,0),(5,2),(6,0))','((1,2),(2,3),(3,0),(5,2),(6,0))')
coefficient=replace_one(coefficient,'colors=[0xc8b56e29','rs(60,0xffffffff)\n        colors=[0xc8b56e29')
coefficient=replace_one(coefficient,'(34,profiles[profile]["color"])','(34,0xff000000)')
(ROOT/'tools/th14-gpu-stage-coefficient-native.py').write_text(coefficient,encoding='utf8')
coefficient_builder=replace_one(builder,"const name='direct-float-'+base","const name='coefficient-'+base")
coefficient_builder=replace_one(coefficient_builder,"if(file==='Renderer.hpp')",'''if(file==='Shaders.hpp'){
   const anchor='outColor=c;';assert.equal(source.split(anchor).length,2);source=source.replace(anchor,'outColor=vec4(vec3(fogEnabled?clamp(vFog,0.0,1.0):1.0),c.a);');
  }
  if(file==='Renderer.hpp')''')
coefficient_builder=coefficient_builder.replace('shaderUnmodifiedFromBase:true','shaderUnmodifiedFromBase:false').replace('artifacts/th14/gpu-stage-float/native.json','artifacts/th14/gpu-stage-coefficient/native.json')
(ROOT/'tools/th14-gpu-stage-coefficient-build.mjs').write_text(coefficient_builder,encoding='utf8')
coefficient_page=page.replace('stage-direct','stage-coefficient').replace('stage-float/','stage-coefficient/').replace('direct-float-before','coefficient-before').replace('direct-float-candidate','coefficient-candidate').replace('shaderUnmodifiedFromBase:true','shaderUnmodifiedFromBase:false')
coefficient_page=coefficient_page.replace('保留生产/候选着色器，只在独立诊断渲染器中更换 RGBA32F 目标和读取类型。真实 D3D9 A32B32G32R32F 对照。','独立诊断直接输出雾系数；原生白色纹理因子、黑色雾色读取同一系数。修改片元输出仅作定位，不作为未修改着色器的整幅颜色证明。')
(ROOT/'tools/th14-gpu-stage-coefficient.html').write_text(coefficient_page,encoding='utf8')
print('Prepared native RGBA32F fixture, unchanged-shader diagnostic modules and visible comparison page')
