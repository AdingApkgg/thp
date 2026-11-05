"""Reuse the frozen retail instruction oracle for the nine model boundaries.

Only expands explicit inputs and strengthens quad assertions. The retail
single-shot and quad instructions, controlled sinks and x87 setup are intact.
"""
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-model-nov05'
parent = R / 'tools/th14-shot-lifetime-native-nov05.py'
raw = parent.read_bytes()
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(raw) == '94f544476ccbcb2976e8b0fa13dc8285f9fbf8556b22bdc942aa5259a29dbefb'
source = raw.decode()
proof = json.loads((H / 'model-audit.json').read_bytes())
assert proof['verifiedModelExplanation'] and proof['matchedOldCountDifferenceFrames'] == 9
changes = []


def replace(before, after):
    global source
    assert source.count(before) == 1, (before[:100], source.count(before))
    source = source.replace(before, after)
    changes.append((before, after))


replace('R=Path(__file__).resolve().parents[1]', 'R=Path('+repr(str(R))+')')
replace("H=R/'artifacts/th14/shot-lifetime-nov05'", "H=R/'artifacts/th14/original-nine-shot-model-nov05'")
replace("indices={case:json.loads((H/case/'model/shot-lifetime-index.json').read_bytes())['snapshots'] for case in ['baseline','late']}",
        "homes={'A':H/'retry1/on/model','B':R/'artifacts/th14/shot-lifetime-nov05/baseline/model'}\nindices={case:json.loads((home/'shot-lifetime-index.json').read_bytes())['snapshots']for case,home in homes.items()}")
replace('def row(case,frame,slot):', 'def row(case,stage,frame,slot):')
replace("if x['stage']==3 and x['stageFrame']==frame", "if x['stage']==stage and x['stageFrame']==frame")
replace("path=H/case/'model'/item['file']", "path=homes[case]/item['file']")
replace('def run(case,frame,slot,swap=False):', 'def run(case,stage,frame,slot,swap=False):')
replace('r=row(case,frame,slot)', 'r=row(case,stage,frame,slot)')
replace("other=row('late' if case=='baseline' else 'baseline',frame,slot)", "other=row('B'if case=='A'else'A',stage,frame,slot)")
replace('''    if not swap:
        expected_quad=r[68:80]
        error=max(abs(f(x)-f(y)) for x,y in zip(quad,expected_quad))
        assert tuple(quad)==expected_quad,(case,frame,error)
    else:error=None''', '''    expected_quad=(other if swap else r)[68:80]
    error=max(abs(f(x)-f(y))for x,y in zip(quad,expected_quad))
    assert tuple(quad)==expected_quad,(case,stage,frame,swap,error)''')
replace('return dict(case=case,stage=3,stageFrame=frame,slot=slot,rotationSwapped=swap,',
        'return dict(case=case,stage=stage,stageFrame=frame,slot=slot,rotationSwapped=swap,')
replace('quadBitIdentical=(None if swap else True)', 'quadBitIdentical=True')
replace('''for slot,frame,retained in [(216,1478,'late'),(234,2092,'baseline')]:
    for case in ['baseline','late']:
        rows.append(run(case,frame,slot))
        rows.append(run(case,frame,slot,True))
    rows.append(run(retained,frame+1,slot))''', '''audit=json.loads((H/'model-audit.json').read_bytes())
assert audit['verifiedModelExplanation']and len(audit['events'])==9
for event in audit['events']:
    assert event['slots'][0]==event['slots'][1]
    stage,frame,slot=event['stage'],event['previousStageFrame'],event['slots'][0]
    results={}
    for case in ['A','B']:
        first=run(case,stage,frame,slot);swapped=run(case,stage,frame,slot,True)
        assert first['retired']!=swapped['retired']
        rows.extend([first,swapped]);results[case]=first
    assert results['A']['retired']!=results['B']['retired']
    retained='B'if results['A']['retired']else'A'
    rows.append(run(retained,stage,frame+1,slot))''')
replace('cases=rows,rotationOnlyControls=4,', 'cases=rows,rotationOnlyControls=18,')
replace('cases=len(rows),rotationOnlyControls=4,', 'cases=len(rows),rotationOnlyControls=18,')
replace("schema='th14/shot-lifetime-retail-component/1'", "schema='th14/original-nine-shot-retail-component/1'")
restored = source
for before, after in reversed(changes):
    assert restored.count(after) == 1
    restored = restored.replace(after, before)
assert restored.encode() == raw
out = H / 'component'
assert not out.exists()
out.mkdir()
(out / 'oracle.py').write_text(source, encoding='utf8', newline='\n')
(out / 'prepared.json').write_text(json.dumps(dict(
    parentOracleSha256=sha(raw), oracleSha256=sha(source.encode()),
    exactReversalRestoresParent=True, retailInstructionExecutionUnchanged=True,
    onlyExplicitInputsAndQuadAssertionsChanged=True, plannedCases=45,
    plannedRotationOnlyControls=18, originalGameplayCapture=False,
    completeGame=False, toolSha256=sha(Path(__file__).read_bytes())), indent=2)+'\n')
exec(compile(source, str(out / 'oracle.py'), 'exec'),
     dict(__name__='__main__', __file__=str(out / 'oracle.py')))
