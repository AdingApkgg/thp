"""Reuse the immutable complete-buffer verifier for the controlled snap8 trial.

Only artifact paths, the declared shader delta, and report labels differ from
the current-production baseline. All Native/portable comparisons remain strict.
"""
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'tools/th14-stage-current-graphics-evidence-check.py'
raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='2617122babce1637f8ed4256df9ead13e6cfd512cdcaef12e0128e47de8207da'
code=raw.decode('utf8')
def replace(a,b):
    global code
    assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
replace("OUT='artifacts/th14/stage-current-graphics-fe406-oct14/'","OUT='artifacts/th14/stage-current-world-snap8-fe406-oct14/'")
replace("'tools/th14-stage-current-graphics-build.mjs'","'tools/th14-stage-current-world-snap8-build.mjs'")
replace("b['vertexSourceChanged']==r['vertexSourceChanged']==False","b['vertexSourceChanged']==r['vertexSourceChanged']==True")
replace("assert shader==frozen.replace(b'outColor=c;',b'outColor=vec4(vUV,0.0,1.0);') if mode=='uv' else shader==frozen", """anchor=b'gl_Position.xy+=gl_Position.w/viewport.zw;'
    step=b'vec2 worldScreen=(gl_Position.xy/gl_Position.w*0.5+vec2(0.5))*viewport.zw;worldScreen=roundEven(worldScreen*256.0)/256.0;gl_Position.xy=((worldScreen+vec2(0.5))/viewport.zw*2.0-vec2(1.0))*gl_Position.w;'
    assert b['worldShaderAnchor'].encode()==anchor and b['worldShaderReplacement'].encode()==step
    expected=frozen.replace(anchor,step)
    if mode=='uv':expected=expected.replace(b'outColor=c;',b'outColor=vec4(vUV,0.0,1.0);')
    assert shader==expected and b['worldViewportQuantizationBits']==8
    base_prefix='artifacts/th14/stage-current-graphics-fe406-oct14/'+mode+'/'
    assert b['baselineBuildSha256']==sha(track(base_prefix+'build.json'))
    assert b['baselineReportSha256']==source['baselineReportSha256']""")
replace("label='Sourcefe406-current-graphics-oct14'","label='Sourcefe406-current-world-snap8-oct14'")
replace("'docs/porting/th14-stage-current-graphics-observed-oct14.json'","'docs/porting/th14-stage-current-world-snap8-observed-oct14.json'")
replace("Current color module preserves frozen production Renderer/Shaders source. UV changes fragment color output only and keeps the exact current vertex source, no transform feedback.","Diagnostic color/UV modules add only the declared uniform world snap8 viewport step; current projection*eye, Renderer, EXT_clip_control and D16 formula are retained. UV additionally changes fragment output. No transform feedback.")
marker="path=ROOT/'docs/porting/th14-stage-current-world-snap8-observed-oct14.json';"
comparison="""baseline=read(source['baselineReportPath'])
assert sha(track(source['baselineReportPath']))==source['baselineReportSha256']
assert sha(track('artifacts/th14/stage-current-graphics-fe406-oct14/sources.json'))==source['baselineSourcesSha256']
assert baseline['sourceBindings']==source['sourceBindings']
track('tools/th14-stage-current-world-snap8-serve.mjs')
assert sha(track('tools/th14-stage-current-graphics-evidence-check.py'))=='2617122babce1637f8ed4256df9ead13e6cfd512cdcaef12e0128e47de8207da'
comparison_rows=[]
for before,after in zip(baseline['uv']['rows'],uv_rows,strict=True):
    assert (before['stage'],before['frame'],before['draw'])==(after['stage'],after['frame'],after['draw'])
    assert before['nativeSha256']==after['nativeSha256']
    comparison_rows.append(dict(index=after['index'],stage=after['stage'],frame=after['frame'],draw=after['draw'],beforeFullHashMatch=before['strictFullBufferHashEqual'],afterFullHashMatch=after['strictFullBufferHashEqual'],beforeSampleWordDifferences=sum(s['differentWords'] for s in before['samples']),afterSampleWordDifferences=sum(s['differentWords'] for s in after['samples']),beforeCoverageDifferences=before.get('coverageDifferences'),afterCoverageDifferences=after.get('coverageDifferences'),beforeCommonCoveredUVDifferences=before.get('differentUVOnCommonCoverage'),afterCommonCoveredUVDifferences=after.get('differentUVOnCommonCoverage')))
receipt['comparisonToCurrentProduction']=dict(baselineReportSha256=source['baselineReportSha256'],beforeColorDifferentChannels=baseline['color']['differentChannels'],afterColorDifferentChannels=different,beforeColorMaxDelta=baseline['color']['maxDelta'],afterColorMaxDelta=maximum,beforeColorExactFrames=baseline['color']['exactFrames'],afterColorExactFrames=exact,beforePrimaryFullUVHashMatches=baseline['uv']['primaryFullHashMatches'],afterPrimaryFullUVHashMatches=primary_exact,beforeExtraCoverageControlFullHashMatches=baseline['uv']['extraControlFullHashMatches'],afterExtraCoverageControlFullHashMatches=control_exact,beforeSampleWordDifferences=baseline['uv']['differentSampleWords'],afterSampleWordDifferences=sample_difference,rows=comparison_rows)
receipt['evidence']=evidence
"""
replace(marker,comparison+marker)
exec(compile(code,str(Path(__file__)), 'exec'),{'__file__':__file__})
