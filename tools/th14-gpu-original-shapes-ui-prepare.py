"""Prepare reviewable independent shape build/page/server from the quad harness."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
build=(ROOT/'tools/th14-gpu-original-quads-build.mjs').read_text(encoding='utf8')
build=build.replace('artifacts/th14/gpu-original-quads','artifacts/th14/gpu-original-shapes')
build=build.replace('th14-gpu-original-quads-fixture.cpp','th14-gpu-original-shapes-fixture.cpp').replace('th14-gpu-original-quads-data.hpp','th14-gpu-original-shapes-data.hpp')
for kind in ['build.mjs','html','serve.mjs']:build=build.replace('th14-gpu-original-quads-'+kind,'th14-gpu-original-shapes-'+kind) if kind!='html' else build.replace('th14-gpu-original-quads.html','th14-gpu-original-shapes.html')
build=build.replace('_gpu_original_quad_case','_gpu_original_shape_case').replace('native.cases.length,640','native.cases.length,810')
(ROOT/'tools/th14-gpu-original-shapes-build.mjs').write_text(build,encoding='utf8')
html=(ROOT/'tools/th14-gpu-original-quads.html').read_text(encoding='utf8')
html=html.replace('原作四角绘制对照','原作形状绘制对照').replace('640 场景','810 场景')
html=html.replace('原作实际记录的四角顶点送入 Direct3D9；移植代码独立计算三角形并送入生产 SDL/WebGL。保留 640×480 像素网格，使用诊断纹理，不代表完整游戏帧。','原作实际记录的矩形、渐变、边框、圆面和线条顶点送入 Direct3D9；移植代码独立计算并送入生产 SDL/WebGL。保留 640×480 像素网格，不代表完整游戏帧。')
html=html.replace('_gpu_original_quad_case','_gpu_original_shape_case')
html=html.replace('mode:c.mode,colorMode:c.colorMode,relation:c.relation,tinted:c.tinted,visibility:c.visibility,sample:c.sample,','mode:c.mode,anchor:c.anchor,parent:c.parent,resolution:c.resolution,')
(ROOT/'tools/th14-gpu-original-shapes.html').write_text(html,encoding='utf8')
server=(ROOT/'tools/th14-gpu-original-quads-serve.mjs').read_text(encoding='utf8').replace('gpu-original-quads','gpu-original-shapes').replace('8150','8151').replace('original quads','original shapes')
(ROOT/'tools/th14-gpu-original-shapes-serve.mjs').write_text(server,encoding='utf8')
print('Prepared independent shape WebGL build, visible result page and localhost server')
