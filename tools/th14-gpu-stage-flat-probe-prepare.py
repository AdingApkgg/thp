"""Separate constant-depth probe for the three remaining range-fog geometries."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
native=(ROOT/'tools/th14-gpu-stage-coefficient-native.py').read_text(encoding='utf8')
native=once(native,"artifacts/th14/gpu-stage-coefficient'","artifacts/th14/gpu-stage-flat-probe'")
native=once(native,'itertools.product(range(len(profiles)),','itertools.product((11,14,21),')
assert native.count('-.65,2,')==2;native=native.replace('-.65,2,','-.65,1,')
(ROOT/'tools/th14-gpu-stage-flat-probe-native.py').write_text(native,encoding='utf8')
cpp=(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-fog-fixture.cpp').read_text(encoding='utf8')
assert cpp.count('-.65f,2,')==2;cpp=cpp.replace('-.65f,2,','-.65f,1,')
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-flat-probe-fixture.cpp').write_text(cpp,encoding='utf8')
cpp=(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-direct-float-fixture.cpp').read_text(encoding='utf8')
cpp=once(cpp,'th14-gpu-stage-fog-fixture.cpp','th14-gpu-stage-flat-probe-fixture.cpp')
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-flat-float-fixture.cpp').write_text(cpp,encoding='utf8')
builder=(ROOT/'tools/th14-gpu-stage-coefficient-build.mjs').read_text(encoding='utf8')
builder=once(builder,"['before','candidate']","['before','candidate']")
builder=once(builder,"const name='coefficient-'+base","const name='flat-probe-'+base")
builder=builder.replace('th14-gpu-stage-direct-float-fixture.cpp','th14-gpu-stage-flat-float-fixture.cpp').replace('th14-gpu-stage-fog-fixture.cpp','th14-gpu-stage-flat-probe-fixture.cpp').replace('artifacts/th14/gpu-stage-coefficient/native.json','artifacts/th14/gpu-stage-flat-probe/native.json')
(ROOT/'tools/th14-gpu-stage-flat-probe-build.mjs').write_text(builder,encoding='utf8')
page=(ROOT/'tools/th14-gpu-stage-coefficient.html').read_text(encoding='utf8')
page=page.replace('7104','576').replace('stage-coefficient','stage-flat-probe').replace('coefficient-before','flat-probe-before').replace('coefficient-candidate','flat-probe-candidate')
start=page.index('const points=')+len('const points=');end=page.index(',actual=',start)
page=page[:start]+'[[15,25,10],[327,16,14],[335,16,14],[422,13,5]]'+page[end:]
page=page.replace('独立诊断直接输出雾系数','仅参数 11／14／21，将四个顶点 z 都置 1 的独立诊断直接输出雾系数')
(ROOT/'tools/th14-gpu-stage-flat-probe.html').write_text(page,encoding='utf8')
print('Prepared 576 constant-depth range-fog probes; production unchanged')
