"""Freeze newline-preserving review/copy files from proven intrinsic v2.

Only line-ending normalization changes from the already compiled prototype.
Historical prototype byte bindings remain immutable.
"""
import hashlib,json,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BEFORE=ROOT/'artifacts/th14/deferred-capture-intrinsic-oct14';OUT=ROOT/'artifacts/th14/deferred-capture-intrinsic-final-oct14';sha=lambda b:hashlib.sha256(b).hexdigest()
inputs=json.loads((BEFORE/'intrinsic-inputs.json').read_bytes());proof_path=ROOT/'docs/porting/th14-deferred-capture-intrinsic-verified-oct14.json';proof=json.loads(proof_path.read_bytes());completion=json.loads((BEFORE/'intrinsic-complete.json').read_bytes())
assert proof['privateIntrinsicEvidenceVerified'] and proof['applicationSyntaxPassed'] and len(proof['non14PreprocessedTokenIsolation'])==6
assert completion['reportSha256']==sha(proof_path.read_bytes()) and completion['patchSha256']==inputs['patchSha256']
OUT.mkdir(parents=True,exist_ok=True);assert not(OUT/'final-complete.json').exists(),'Final copy files are immutable'
normalize=lambda b:b.replace(b'\r\n',b'\n')
rows=[];patch=[]
for relative in inputs['modifiedExistingFiles']:
    before=(BEFORE/'before'/relative).read_bytes();compiled=(BEFORE/'source'/relative).read_bytes()
    expected_eol=b'\r\n' if before.count(b'\r\n')==before.count(b'\n') and before.count(b'\n') else b'\n'
    final=normalize(compiled)
    if expected_eol==b'\r\n':final=final.replace(b'\n',b'\r\n')
    assert normalize(final)==normalize(compiled),'Semantic source must be identical to compiled v2'
    target=OUT/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(final)
    original=OUT/'before'/relative;original.parent.mkdir(parents=True,exist_ok=True);original.write_bytes(before)
    patch.extend(difflib.unified_diff(normalize(before).decode('utf8').splitlines(True),normalize(final).decode('utf8').splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
    rows.append(dict(path=relative,beforeSha256=sha(before),afterSha256=sha(final),compiledV2Sha256=sha(compiled),bytesBefore=len(before),bytesAfter=len(final),preservedOriginalLineEndings='CRLF' if expected_eol==b'\r\n' else 'LF',copyPath=target.as_posix(),beforePath=original.as_posix(),newlineNormalizedBytesEqualCompiledV2=True))
helpers=[]
for relative in proof['newHelpers']:
    data=(BEFORE/'source'/relative).read_bytes();target=OUT/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    patch.extend(difflib.unified_diff([],normalize(data).decode('utf8').splitlines(True),fromfile='/dev/null',tofile='b/'+relative))
    helpers.append(dict(path=relative,bytes=len(data),sha256=sha(data),copyPath=target.as_posix(),bytesEqualCompiledV2=True))
patch_path=OUT/'intrinsic-final.patch';patch_path.write_bytes(''.join(patch).encode('utf8'))
out=dict(privateIntrinsicFinalVerified=True,productionChanged=False,productionAdopted=False,completeGame=False,nativeEquivalent=False,
 modifiedFiles=rows,newHelpers=helpers,patchPath=patch_path.as_posix(),patchSha256=sha(patch_path.read_bytes()),
 validatedPrototypeReport=proof_path.relative_to(ROOT).as_posix(),validatedPrototypeReportSha256=sha(proof_path.read_bytes()),validatedPrototypeCompletionSha256=sha((BEFORE/'intrinsic-complete.json').read_bytes()),
 codeValidation=dict(entryCases=7,controlledRetirements=6,typedImmediateSourceCases=6,nativeVmDestroyPreservedBytes=640,applicationSyntaxPassed=True,non14TokenIsolations=6),
 loaderGetter=proof['loaderFirstSlotGetter'],postDrawQueue=proof['postDrawQueue'],headlessRetirement=proof['headlessExplicitNoTargetRetirement'],toolSha256=sha(Path(__file__).read_bytes()),
 scope='Final copy/review source preserves each existing file original LF or CRLF convention. Every final file equals the already compiled/syntax-checked/token-isolated intrinsic v2 after newline normalization; helpers remain byte-identical. Only review diff generation and existing-file line endings are corrected. Frozen v1/v2 tools/reports/modules are untouched. Root/loading must merge Application small hunks instead of replacing that whole file, and rebuild all production objects for the AnmManager/GameSession layout before adoption. No GPU/pixel equivalence or production execution claimed.')
report=ROOT/'docs/porting/th14-deferred-capture-intrinsic-final-verified-oct14.json';report.write_bytes((json.dumps(out,indent=2)+'\n').encode('utf8'))
(OUT/'final-complete.json').write_bytes((json.dumps(dict(reportSha256=sha(report.read_bytes()),patchSha256=out['patchSha256'],toolSha256=out['toolSha256']),indent=2)+'\n').encode('utf8'))
print(json.dumps({'privateIntrinsicFinalVerified':True,'patchPath':out['patchPath'],'patchSha256':out['patchSha256'],'modifiedFiles':rows,'newHelpers':helpers}))
