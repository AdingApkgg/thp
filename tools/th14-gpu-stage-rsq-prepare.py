"""Generate a pure RSQ probe, comparing only R with native authored assembly."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=(ROOT/'tools/th14-gpu-stage-flat-probe-build.mjs').read_text(encoding='utf8')
s=s.replace("['before','candidate']","['candidate']").replace("const name='flat-probe-'+base","const name='flat-probe-rsq'")
a="if(file==='Shaders.hpp'){";assert s.count(a)==1
s=s.replace(a,a+"const expression='vFog=fogEnabled?(transformed?specular.a:fog):1.0;';assert.ok(source.includes(expression));source=source.replace(expression,'vFog=fogEnabled?inversesqrt(dot(eye.xyz,eye.xyz)):1.0;');")
s=s.replace('artifacts/th14/gpu-stage-flat-probe/native.json','artifacts/th14/gpu-native-shader-probe/rsq-output/native.json')
(ROOT/'tools/th14-gpu-stage-rsq-build.mjs').write_text(s,encoding='utf8')
p=(ROOT/'tools/th14-gpu-stage-flat-probe.html').read_text(encoding='utf8')
p=p.replace('stage-flat-probe','stage-rsq').replace('flat-probe-before','flat-probe-rsq').replace('flat-probe-candidate','flat-probe-rsq')
p=p.replace('for(let ch=0;ch<4;ch++)','for(let ch=0;ch<1;ch++)').replace('groups,critical}','groups:groups.slice(0,1),alphaExcluded:true,critical}')
p=p.replace('仅参数 11／14／21，将四个顶点 z 都置 1 的独立诊断直接输出雾系数','仅参数 11／14／21 的恒定深度 RSQ 指令对照；原生运行自行编写的顶点指令，浏览器直接读取 inversesqrt，比较 R 通道，排除透明度')
(ROOT/'tools/th14-gpu-stage-rsq.html').write_text(p,encoding='utf8')
print('Prepared separate RSQ arithmetic probe')
