"""Publish finite camera evidence together with the newly exposed mode failures."""
from pathlib import Path
import argparse, hashlib, importlib.util, json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/unified-event-context-trace-nov04'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def proof():
 bindings={};reports={}
 for name,tool,receipt in [
  ('cameraWindow','th14-observed-perspective-window-evidence-nov04.py','perspective-window-verified.json'),
  ('modeAudit','th14-full-camera-mode-evidence-nov04.py','expanded-modes-verified.json')]:
  path=R/'tools'/tool;spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  result=module.verify();raw=(H/receipt).read_bytes();assert json.loads(raw)==result
  for key,value in result['bindings'].items():
   if key in bindings:assert bindings[key]==value
   bindings[key]=value
  for item in (path,H/receipt):
   data=item.read_bytes();bindings[item.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data))
  reports[name]={key:value for key,value in result.items()if key not in('bindings','protectedFiles')}
 clock=json.loads((H/'verified.json').read_bytes());assert clock['verifierSha256']==SHA((R/'tools/th14-unified-event-context-evidence-nov04.py').read_bytes())
 reports['unifiedOriginalClock']={key:value for key,value in clock.items()if key not in('bindings','protectedFiles')}
 path=R/'tools/th14-unified-event-context-evidence-nov04.py';data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data))
 assert reports['cameraWindow']['measuredWindow']['wrongWords']==0 and reports['modeAudit']['expandedFailures']==12
 return dict(verifiedUnifiedCameraWindowEvidence=True,productionCoreChanged=False,
  productionSourceCommit='8c6d4678ca5abed189a7f7c6347128e311cd31c3',ordinaryCoreWasmSha256='fc24f408b1ea2bf5c0a054dd7b06d2e1e542d0145a2df7faacbed250b2288949',
  toolsAndEvidenceOnly=True,unresolvedExpandedModeRecords=12,originalValuesInjected=False,hostClockWindowReplayAdded=True,
  exactOriginalInstructionScheduleRecovered=False,independentSchedulingAccepted=False,oldRecordingFailureClosed=False,
  browserAcceptance=False,originalWholeGamePixelsOrPcmAccepted=False,completeGame=False,nativeEquivalent=False,
  **reports,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(R/'docs/porting');result=proof()
 if a.check:assert json.loads(out.read_bytes())==result
 else:
  assert not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode())
 print(json.dumps({key:value for key,value in result.items()if key not in('bindings','unifiedOriginalClock','modeAudit','cameraWindow')}))


if __name__=='__main__':main()
