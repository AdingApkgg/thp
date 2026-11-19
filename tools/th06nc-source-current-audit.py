"""Record current versus historical TH06nc source snapshots, without widening scopes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def main():
 current=[];historical=[];coverage={}
 for path in sorted((ROOT/'docs/porting').glob('th06nc-*-verified.json')):
  raw=path.read_bytes();report=json.loads(raw);hashes=report.get('sourceSha256')
  if not isinstance(hashes,dict)or not hashes:continue
  name=path.relative_to(ROOT).as_posix();changed=[p for p,h in hashes.items()if not(ROOT/p).is_file()or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
  if changed or report.get('passed')is not True:
   historical.append({'report':name,'changedSources':changed,'passed':report.get('passed')});continue
  current.append({'report':name,'sha256':hashlib.sha256(raw).hexdigest()})
  for p in hashes:coverage.setdefault(p,[]).append(name)
 sources=sorted(p.relative_to(ROOT).as_posix()for p in(ROOT/'shared/th06nc').glob('*.mjs'));uncovered=[p for p in sources if p not in coverage]
 report={'scope':'Source snapshot audit only. An unchanged report supports only its declared scope; presence in a snapshot is not execution or whole-game/pixel equivalence. Historical reports are retained without rewriting their hashes.','currentReports':current,'historicalReports':historical,'sharedModuleCoverage':{p:coverage.get(p,[])for p in sources},'uncovered':uncovered,'passed':not uncovered,'completeGame':False,'nativeEquivalent':False}
 (ROOT/'docs/porting/th06nc-source-current-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'currentReports':len(current),'historicalReports':len(historical),'sharedModules':len(sources),'uncovered':uncovered}));assert not uncovered,uncovered
if __name__=='__main__':main()
