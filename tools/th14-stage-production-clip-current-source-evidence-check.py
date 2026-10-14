"""Bind real no-guard captures to byte-identical final current production sources.

The historical producer sourceBindings still names the finite-guard source
before its private shader substitution. Current bindings are computed afresh;
the complete consumed color-source files, not that old hash, bind final code.
"""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT='artifacts/th14/stage-production-clip-no-finite-guard-oct14/'
ORIGINAL='runtimes/th12/portable/sdl/'
evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    path=Path(p);path=path if path.is_absolute() else ROOT/path
    b=path.read_bytes();evidence[str(p)]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
def bound(p,binding):
    raw=track(p);assert len(raw)==binding['bytes'] and sha(raw)==binding['sha256'],p;return raw
receipt_path='docs/porting/th14-stage-production-clip-no-finite-guard-observed-oct14.json'
receipt=read(receipt_path)
assert receipt['diagnosticEvidenceVerified'] and not receipt['productionChanged']
assert not receipt['completeGame'] and not receipt['nativeEquivalent']
assert receipt['finiteShaderBranchImpactIsolated']
assert receipt['earlierPrivateCandidateCompleteBufferComparison']['color']['allCompleteBytesEqual']
assert receipt['earlierPrivateCandidateCompleteBufferComparison']['uv']['allCompleteBytesEqual']
for p,binding in receipt['evidence'].items():bound(p,binding)
bound('tools/th14-stage-production-clip-no-finite-guard-evidence-check.py',dict(bytes=len(track('tools/th14-stage-production-clip-no-finite-guard-evidence-check.py')),sha256=receipt['toolSha256']))
builds={mode:read(OUT+mode+'/build.json') for mode in ['color','uv']}
current={};identical=[]
files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp']
for name in files:
    p=ORIGINAL+name;raw=track(p);compiled=bound(OUT+'color/'+name,builds['color']['sources'][name])
    assert raw==compiled,'Current production differs from the physically tested color source: '+name
    current[p]=dict(bytes=len(raw),sha256=sha(raw));identical.append(dict(currentPath=p,compiledColorPath=OUT+'color/'+name,fullBytes=len(raw),sha256=sha(raw),allFileBytesEqual=True))
    uv=bound(OUT+'uv/'+name,builds['uv']['sources'][name])
    if name=='Shaders.hpp':
        assert raw.count(b'outColor=c;')==1
        assert uv==raw.replace(b'outColor=c;',b'outColor=vec4(vUV,0.0,1.0);')
    else:assert uv==raw
fixture='runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp'
actual_fixture=track(fixture);compiled_fixture=bound(OUT+'color/fixture.cpp',builds['color']['sources']['fixture.cpp'])
assert compiled_fixture.replace(b'"Renderer.hpp"',b'"../../../portable/sdl/Renderer.hpp"',1)==actual_fixture
current[fixture]=dict(bytes=len(actual_fixture),sha256=sha(actual_fixture))
for mode in ['color','uv']:
    b=builds[mode]
    assert b['onlyFiniteGuardRemoved'] and b['productionFrozen'] and b['vertexSourceChanged']
    assert '-O2' in b['flags'] and '-ffp-contract=off' in b['flags'] and '-fno-strict-aliasing' in b['flags']
    assert '-DPORT_TITLE=14' in b['flags']
    assert sha(track(OUT+mode+'/gpu.wasm'))==b['wasmSha256']
    assert sha(track(OUT+mode+'/gpu.mjs'))==b['loaderSha256']
    r=read(OUT+mode+'/capture/report.json')
    assert r['wasmSha256']==b['wasmSha256']
    for i,row in enumerate(r['reports']):
        name=f'frame-{i:03d}'+('.bgra' if mode=='color' else '.rgba32f')
        raw=track(OUT+mode+'/capture/'+name)
        assert sha(raw)==row['portableSha256'] and len(raw)==row['bytes']
    assert len(r['reports'])==(21 if mode=='color' else 23)
shader=track(ORIGINAL+'Shaders.hpp');cpp=track(ORIGINAL+'Renderer.cpp')
assert b'gl_Position.xy=numerator/viewport.zw;' in shader
assert b'isnan(numerator)' not in shader and b'isinf(numerator)' not in shader
assert b'vec4 eye=view*model*vec4(position.xyz,1.0);' in shader
assert b'volatile float product=a[row]*b[col*4];volatile float sum=product;' in cpp
assert b'product=a[k*4+row]*b[col*4+k];sum=sum+product;' in cpp
assert b'th14_multiply(projection,th14_multiply(view,world))' in cpp
# Other-title selections retain all original code tokens and raw string bytes.
def selected(text,title):
    stack=[];out=[]
    def active():return all(s[1] for s in stack if s[0])
    for line in text.splitlines(keepends=True):
        m=re.match(r'^\s*#\s*(if|ifdef|ifndef|else|elif|endif)\b(.*)',line)
        if not m:
            if active():out.append(line)
            continue
        kind,arg=m.groups()
        if kind=='if' and arg.strip()=='defined(PORT_TITLE) && PORT_TITLE == 14':stack.append([True,title==14]);continue
        if kind in ('if','ifdef','ifndef'):
            if active():out.append(line)
            stack.append([False,True]);continue
        assert stack
        if kind=='else':
            if stack[-1][0]:stack[-1][1]=not stack[-1][1]
            elif active():out.append(line)
        elif kind=='elif':
            assert not stack[-1][0]
            if active():out.append(line)
        else:
            if not stack[-1][0] and active():out.append(line)
            stack.pop()
    assert not stack;return ''.join(out)
token=re.compile(r'R"(?P<tag>[A-Za-z0-9_]*)\([\s\S]*?\)(?P=tag)"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/|\s+|[A-Za-z_]\w*|[0-9]+(?:\.[0-9]*)?|[^\w\s]')
def tokens(text):return [m.group(0) for m in token.finditer(text) if not m.group(0).isspace() and not m.group(0).startswith('//') and not m.group(0).startswith('/*')]
other_titles=[]
pre='artifacts/th14/stage-current-production-clip-scaled-bias-oct14/pre-edit/'
for title in [None,6,7,8,9,10,11,12,13,15,16,17,18,19,20]:
    for name in ['Renderer.cpp','Shaders.hpp']:
        assert tokens(selected(track(pre+name).decode(),title))==tokens(selected(track(ORIGINAL+name).decode(),title)),(title,name)
    other_titles.append('undefined' if title is None else title)
arith=read('docs/porting/th14-stage-scaled-bias-arithmetic-verified-oct14.json')
assert arith['diagnosticEvidenceVerified'] and arith['scaledIntermediateDomain']['allActualProductsAndNumeratorsFinite']
report=dict(diagnosticEvidenceVerified=True,currentProductionSourceVerified=True,completeGame=False,nativeEquivalent=False,
 productionChanged=True,label='Current-production-TH14-sequential-clip-scaled-bias-oct14',
 sourceBindings=current,currentHeaders={p:b for p,b in current.items() if p.endswith('.hpp')},
 historicalGuardProducerSourceBindings=builds['color']['sourceBindings'],
 compiledConsumedSourceFiles=identical,actualColorRendererAndShaderFileBytesEqualCurrentProduction=True,
 actualUVRendererFileBytesEqualCurrentProduction=True,actualUVShaderDiffersOnlyFragmentOutput=True,
 oldGuardShaderBindingReusedAsCurrent=False,realPhysicalCaptures=dict(colorFrames=21,colorFullBytes=25804800,uvFrames=23,uvFullBytes=113049600,totalFrames=44),
 actualWasmBindings={mode:dict(wasmSha256=builds[mode]['wasmSha256'],loaderSha256=builds[mode]['loaderSha256'],compileFlags=builds[mode]['flags']) for mode in ['color','uv']},
 color=receipt['color'],uv=receipt['uv'],gpu=receipt['gpu'],rendererStatistics=receipt['rendererStatistics'],
 otherTitleCodeTokensAndShaderStringBytesUnchanged=other_titles,finiteShaderFailureReceipt='docs/porting/th14-stage-production-clip-scaled-bias-observed-oct14.json',
 frozenPhysicalRecomputeReceipt=receipt_path,capturedFiniteDomain=arith['scaledIntermediateDomain'],
 evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),
 limits='Final actual production files are byte-identical to the fully consumed no-guard color sources that produced44 archived physical buffers; UV changes only fragment output and fixture float readback. Bindings are calculated from current production bytes, not the historical guarded producer shader hash. No new browser execution is invented and no reference corpus is rebased. Scope is the independently captured finite matrix/viewport/vertex domain, including source-modeled283 negative-w vertices and34 mixed-sign draws; unobserved extreme domains are not claimed universally correct. Color still differs880 channels across21 frames;7 complete Native UV controls retain5292 failed float words and3 primary full hashes remain different. Other16 primary cases retain full hashes and selected Native sample bytes only. This proves this source/capture identity and bounded improvement, not complete-game, all-mode, audio, loading or whole-memory1:1.')
path=ROOT/'docs/porting/th14-stage-production-clip-current-source-verified-oct14.json'
raw=(json.dumps(report,indent=2)+'\n').encode()
if path.exists():assert path.read_bytes()==raw,'Final receipt immutable'
else:path.write_bytes(raw)
print(json.dumps(dict(currentProductionSourceVerified=True,sourceBindings=current,colorDifferentChannels=report['color']['differentChannels'],uvPrimaryHashes=report['uv']['primaryFullHashMatches'],uvCompleteNativeCases=report['uv']['nativeFullBufferCases'],uvAllNativeFullFailedWords=report['uv']['allNativeFullCaseWordDifferences'],actualPhysicalFrames=44,otherTitleSelectionsUnchanged=len(other_titles),reportSha256=sha(raw))))
