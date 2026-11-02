"""Exercise exact Initialize input coverage and negative controls; no game is launched."""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02';tool=R/'tools/th14-verify-native-initialize-timing-v2-nov03.py';sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.mkdir(parents=True)
passed=[]
for plan in sorted((H/'counter-regressions').glob('case-*/plan.json')):
 c=json.loads(plan.read_bytes())['cases'][0];folder=plan.parent/c['key'];output=out/(c['key']+'.json');p=subprocess.run([sys.executable,'-X','utf8',str(tool),'--native',str(R/c['native']),'--model',str(folder/'model'),'--output',str(output)],capture_output=True);assert p.returncode==0,(c['key'],p.stderr.decode(errors='replace'));passed.append(c['key'])
assert len(passed)==16
native=R/'artifacts/th14/reimu-controller-z-live-context-nov01/native';original=json.loads((H/'counter-retained36826/model/report.json').read_bytes());controls=[]
for label in ['wrong-time','wrong-source','missing-phase','duplicate-phase','tampered-event']:
 d=out/label;d.mkdir();model=d/'model';model.mkdir();m=copy.deepcopy(original);entries=[x for x in m['observedPhaseInputs'] if x['phase']=='Initialize'];assert entries
 if label=='wrong-time':entries[-1]['readyNs']+=1
 elif label=='wrong-source':entries[-1]['completionSource']='unobserved'
 elif label=='missing-phase':m['observedPhaseInputs'].remove(entries[-1])
 elif label=='duplicate-phase':m['observedPhaseInputs'].append(copy.deepcopy(entries[-1]))
 (model/'report.json').write_text(json.dumps(m),encoding='utf8');n=native
 if label=='tampered-event':
  n=d/'native';n.mkdir();shutil.copyfile(native/'report.json',n/'report.json');shutil.copyfile(native/'selected-state.u32',n/'selected-state.u32');ev=[json.loads(x) for x in (native/'transition-events.jsonl').read_bytes().splitlines()];next(x for x in ev if x['event']=='replay-seeds-restored-before-globals-copy')['hostMonotonicNs']+=1;(n/'transition-events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in ev))
 bad=d/'must-not-pass.json';p=subprocess.run([sys.executable,'-X','utf8',str(tool),'--native',str(n),'--model',str(model),'--output',str(bad)],capture_output=True);assert p.returncode!=0 and not bad.exists(),label;(d/'rejection.log').write_bytes(p.stdout+p.stderr);controls.append({'name':label,'rejected':True})
result={'passed':True,'naturalCases':len(passed),'cases':passed,'negativeControls':controls,'verifierSha256':sha(tool.read_bytes()),'testToolSha256':sha(Path(__file__).read_bytes()),'scope':'Initialize phase event coverage and timestamp binding only','noOriginalProcessLaunched':True,'physicalAudioDevicesOpened':0,'productionChanged':False,'completeGame':False,'nativeEquivalent':False};(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
