"""Offline clip dot models for the three residual strip boundary vertices.

Models are hypotheses, never actual uninstru mented GPU position observations.
"""
import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
prepared=read('artifacts/th14/stage-gpu-stream-replay/prepared.json')
native=read('artifacts/th14/stage-current-residual-native-composed-uv-fe406-oct14/native.json')
proof=read('docs/porting/th14-stage-current-residual-native-composed-full-observed-oct14.json')
assert proof['diagnosticEvidenceVerified'] and proof['differentFloatWords']==0 and proof['completeComparedBytes']==14745600
planes=read('docs/porting/th14-stage-current-residual-uv-plane-observed-oct14.json')
assert planes['diagnosticEvidenceVerified'];track('tools/th14-stage-current-residual-uv-plane-check.py')
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
rows=[]
for ni,(case,vertex_index,axis,triangle_segment,triangle_index,corner) in enumerate(zip(native['frames'],[73,68,18],[1,0,1],[35,33,8],[1,0,0],[3,2,2])):
    frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(case['stage'],case['frame']))
    draw=[c for c in frame['commands'] if c['kind']=='draw'][case['originalDrawIndex']]
    floats=struct.unpack('<%df'%len(draw['words']),struct.pack('<%dI'%len(draw['words']),*draw['words']))
    position=[*floats[vertex_index*6:vertex_index*6+3],1.0]
    matrix=struct.unpack('<16f',struct.pack('<16I',*case['computedClipMatrixWords']));models={}
    for mode in ['separateSeq','separatePair','doubleDot','fmaForward','fmaReverse']:
        values=[]
        for row in range(4):
            operands=[matrix[row+k*4] for k in range(4)];terms=[a*b for a,b in zip(operands,position)]
            if mode=='separateSeq':
                s=f32(terms[0])
                for k in range(1,4):s=f32(s+f32(terms[k]))
            elif mode=='separatePair':s=f32(f32(f32(terms[0])+f32(terms[1]))+f32(f32(terms[2])+f32(terms[3])))
            elif mode=='doubleDot':s=f32(sum(terms))
            elif mode=='fmaForward':
                s=f32(terms[0])
                for k in range(1,4):s=f32(math.fma(operands[k],position[k],s))
            else:
                s=f32(terms[3])
                for k in [2,1,0]:s=f32(math.fma(operands[k],position[k],s))
            values.append(s)
        screen=[(values[0]/values[3]+1)*320,(-values[1]/values[3]+1)*240]
        models[mode]=dict(clipValues=values,clipWords=list(struct.unpack('<4I',struct.pack('<4f',*values))),idealDoubleViewport=screen,nearestSnap8XY=[round(v*256)/256 for v in screen])
    triangle=planes['rows'][ni]['segments'][triangle_segment]['triangles'][triangle_index]
    fits=triangle['fits'];inferred={key:fits[key]['vertices'][corner]['nearestSnap8XY'] for key in fits}
    assert planes['rows'][ni]['segments'][triangle_segment]['submittedVertices'][corner]==vertex_index
    all_words_equal=len({tuple(model['clipWords']) for model in models.values()})==1
    rows.append(dict(stage=case['stage'],frame=case['frame'],draw=case['originalDrawIndex'],vertex=vertex_index,criticalAxis=axis,submittedPosition=position,computedOriginalMatrixWords=case['computedClipMatrixWords'],indirectPlaneSnap8XY=inferred,indirectFitsConditionNumber={k:v['conditionNumber'] for k,v in fits.items()},allFiveDotModelWordsEqual=all_words_equal,models=models))
assert [row['allFiveDotModelWordsEqual'] for row in rows]==[True,True,False]
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,rows=rows,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),hypothesis='Four explicit GLSL row dot calls may change actual ANGLE dot arithmetic relative to mat4*vec4. This must be physically tested; the first two critical vertices have identical offline clip words in five ordinary dot models, so no model predicts a clip-word repair there.',scope='Only frozen original submitted positions and CPU-composed original world/view/projection matrices. Five explicitly declared offline double/binary32/FMA dot models are not actual production GPU readback. Plane-derived snapped coordinates are indirect rounded-UV estimates, never runtime inputs. No injected Native/fitted matrices or varying values, pixel masks, hardcoded corrections or production edits.')
(ROOT/'docs/porting/th14-stage-current-residual-critical-dot-observed-oct14.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'diagnosticEvidenceVerified':True,'allFiveDotModelWordsEqual':[row['allFiveDotModelWordsEqual'] for row in rows]}))
