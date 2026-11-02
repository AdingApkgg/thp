"""Reject TH14 capture reports with unexpected debug exceptions before strict replay verification."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();n=a.native.resolve();out=a.output.resolve()
assert n.is_relative_to(R/'artifacts/th14') and out.is_relative_to(R/'artifacts/th14') and not out.exists()
raw=(n/'report.json').read_bytes();report=json.loads(raw)
assert report['childExited'] and not report['error'], 'Original process did not finish cleanly'
assert 'debugErrors' in report and isinstance(report['debugErrors'],list), 'Original debug exception list missing or malformed'
assert not report['debugErrors'], 'Original capture contains debug exceptions; preserve as diagnostic until individually explained'
result=dict(passed=True,scope='Only checks that the original observer reported no debug exceptions; gameplay, timing and complete game still need separate gates.',nativeReportSha256=hashlib.sha256(raw).hexdigest(),childExited=True,debugExceptionCount=0,completeGame=False,nativeEquivalent=False,verifierSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
