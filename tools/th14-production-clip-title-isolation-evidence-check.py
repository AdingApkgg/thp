"""Verify TH14-only production code and preserve other-title token/string paths.

This checks the frozen production source used for actual browser captures, not
mutable working files. Compile-time title selection is simulated structurally;
unrelated existing preprocessor conditionals are retained unchanged.
"""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='artifacts/th14/stage-current-production-clip-scaled-bias-oct14/'
evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
def select_title(text,title):
    stack=[];out=[]
    def active():return all(s[1] for s in stack if s[0])
    for line in text.splitlines(keepends=True):
        directive=re.match(r'^\s*#\s*(if|ifdef|ifndef|else|elif|endif)\b(.*)',line)
        if not directive:
            if active():out.append(line)
            continue
        kind,arg=directive.groups()
        if kind=='if' and arg.strip()=='defined(PORT_TITLE) && PORT_TITLE == 14':
            stack.append([True,title==14]);continue
        if kind in ('if','ifdef','ifndef'):
            if active():out.append(line)
            stack.append([False,True]);continue
        assert stack,'Unbalanced source conditional'
        if kind=='else':
            if stack[-1][0]:stack[-1][1]=not stack[-1][1]
            elif active():out.append(line)
        elif kind=='elif':
            assert not stack[-1][0],'Unexpected title elif'
            if active():out.append(line)
        else:
            special=stack[-1][0]
            if not special and active():out.append(line)
            stack.pop()
    assert not stack
    return ''.join(out)
TOKEN=re.compile(r'R"(?P<tag>[A-Za-z0-9_]*)\([\s\S]*?\)(?P=tag)"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/|\s+|[A-Za-z_]\w*|[0-9]+(?:\.[0-9]*)?|[^\w\s]')
def tokens(source):
    return [t for t in TOKEN.findall(source)]
def semantic_tokens(source):
    out=[]
    for match in TOKEN.finditer(source):
        t=match.group(0)
        if t.isspace() or t.startswith('//') or t.startswith('/*'):continue
        out.append(t)
    return out
before=read(BASE+'pre-edit/sources.json');frozen=read(BASE+'sources.json')
for name,h in before.items():assert sha(track(BASE+'pre-edit/'+name))==h
for name,h in frozen['snapshots'].items():assert sha(track(BASE+'source/'+name))==h
assert track(BASE+'source/Renderer.hpp')==track(BASE+'pre-edit/Renderer.hpp')
results=[]
for title in [None,6,7,8,9,10,11,12,13,15,16,17,18,19,20]:
    row=dict(title='undefined' if title is None else title,files={})
    for name in ['Renderer.cpp','Shaders.hpp']:
        old=select_title(track(BASE+'pre-edit/'+name).decode(),title)
        new=select_title(track(BASE+'source/'+name).decode(),title)
        ot,nt=semantic_tokens(old),semantic_tokens(new)
        assert ot==nt,(title,name)
        row['files'][name]=dict(identicalAllCodeTokensAndStringBytes=True,tokenCount=len(ot),tokenSequenceSha256=sha(json.dumps(ot,separators=(',',':')).encode()))
    results.append(row)
cpp=track(BASE+'source/Renderer.cpp').decode();old_cpp=track(BASE+'pre-edit/Renderer.cpp').decode()
def method(source,start,next_start):
    a=source.index(start);b=source.index(next_start,a+len(start));return source[a:b]
for start,end in [('void Renderer::draw(Topology','void Renderer::flush()'),('void Renderer::flush()','void Renderer::discard()'),('void Renderer::discard()','void Renderer::issue(')]:
    assert method(cpp,start,end)==method(old_cpp,start,end),start
assert cpp[cpp.index('extern "C" {'):]==old_cpp[old_cpp.index('extern "C" {'):]
actual14=select_title(cpp,14)
for fragment in ['volatile float product=a[row]*b[col*4];volatile float sum=product;','product=a[k*4+row]*b[col*4+k];sum=sum+product;','th14_multiply(projection,th14_multiply(view,world))','const u32 records=instanceSize/68;std::vector<u8> expanded(records*132);','std::memcpy(expanded.data()+record*132,input+record*68,68);','std::memcpy(expanded.data()+record*132+68,clip.data(),64);','glDrawArraysInstanced(mode,0,n,instanceSize/68);']:assert fragment in actual14
assert 'diagnostic' not in actual14 and 'gpu_clip_' not in actual14
shader=select_title(track(BASE+'source/Shaders.hpp').decode(),14)
assert 'vec4 eye=view*model*vec4(position.xyz,1.0);' in shader
assert 'if(any(isnan(numerator))||any(isinf(numerator)))gl_Position.xy+=gl_Position.w/viewport.zw;else gl_Position.xy=numerator/viewport.zw;' in shader
assert cpp.count('glVertexAttribDivisor(9+i,1)')==1
assert 'u32(!!instance)' in actual14
build=read(BASE+'color/build.json')
assert '-O2' in build['flags'] and '-ffp-contract=off' in build['flags'] and '-fno-strict-aliasing' in build['flags']
report=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,
 frozenProductionSourceBindings=frozen['sourceBindings'],otherTitleSelections=results,rendererHeaderByteUnchanged=True,
 drawQueueFlushDiscardMethodsByteUnchanged=True,productionExportsByteUnchanged=True,noDiagnosticProductionExports=True,
 th14QueueBytes=68,th14UploadedInstanceBytes=132,originalWorldAndFactorBytesPreserved=68,eachInstanceOwnDerivedClipBytes=64,
 instanceDrawCountStillOriginal68BRecords=True,instanceVAOKeyIncludesInstancedFlag=True,worldLocations=[4,5,6,7],factorLocation=8,clipLocations=[9,10,11,12],allInstanceAttributeDivisors=1,
 pointerCacheBoundary='Emscripten upload replaces backing store and returns base0, so cached VAO pointers retain valid base/132B stride. Non-Emscripten attribute setup executes on every draw and updates current aligned upload base. Non-instance VAOs have separate keys and attrs9..12 stay disabled; instanced=false selects uniform clip.',
 finiteFallbackBoundary='Frozen actual finite-branch production source has general any-isnan/isinf numerator fallback. Physical color regression is retained in its failed report; this structural review is not approval of that failed variant. Later no-guard selection remains a separate source and physical receipt.',
 currentCompileFlags=build['flags'],evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),
 limits='Other-title source selections have all code tokens and string-literal bytes unchanged, including original GLSL, but this is not a GPU or game regression run for those titles. TH14 source retains real batching, original world/factor records and fog/eye, with new derived clip attrs. Binary32 volatile stores prevent product/partial-sum reassociation by the actual CPU optimized build; GLSL shader fusion/rounding is separately physically measured. No game-core source, external publication or Native game process was changed here.')
path=ROOT/'docs/porting/th14-production-clip-title-isolation-verified-oct14.json'
path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(diagnosticEvidenceVerified=True,unchangedOtherTitleSelections=len(results),unchangedMethodsAndExports=True,queueBytes=68,uploadedInstanceBytes=132,currentOptimization='-O2')))
