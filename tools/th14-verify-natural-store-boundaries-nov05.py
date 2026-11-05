"""Reuse unchanged expanded/native-slot gates for the per-store diagnostic."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/natural-store-boundaries-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()


def main(stage):
    if stage=='slots':
        parent=R/'tools/th14-audit-native-shot-slots-nov05.py'
        expected='835473ad56cd297b1ccdeedab981d349735aa86b0e00a96ed1474c5d742b9c5a'
        changes=[("H=R/'artifacts/th14/shot-lifetime-native-nov05'","H=R/'artifacts/th14/natural-store-boundaries-nov05'",1),
            ("native=H/'prefix-slots-v2/native'","native=R/'artifacts/th14/original-nine-shot-native-nov05/prefix-slots-v2/native'",1),
            ("H/'comparison-on/model'","H/'on/model'",1),
            ("H/'comparison-on/result.json'","H/'on/result.json'",1)]
    else:
        parent=R/'tools/th14-verify-original-nine-shot-native-nov05.py'
        expected='f31615047c539b2e8d98551b99759a9c0094ab999375abcf7322d7777691c396'
        changes=[("H = R / 'artifacts/th14/original-nine-shot-native-nov05'","H = R / 'artifacts/th14/natural-store-boundaries-nov05'",1),
            ("native = H / 'prefix-slots-v2/native'","native = R / 'artifacts/th14/original-nine-shot-native-nov05/prefix-slots-v2/native'",1),
            ("home = H / (case if case.startswith('overlap-') else 'comparison-'+case)","home = H / case",1),
            ("H / 'native-register-proof.json'","R / 'artifacts/th14/original-nine-shot-native-nov05/native-register-proof.json'",2)]
        sys.argv=[str(Path(__file__)),'--case',stage]
    raw=parent.read_bytes()
    assert SHA(raw)==expected
    source=raw.decode()
    for before,after,count in changes:
        assert source.count(before)==count,(before,source.count(before))
        source=source.replace(before,after)
    restored=source
    for before,after,count in reversed(changes):
        assert restored.count(after)==count
        restored=restored.replace(after,before)
    assert restored.encode()==raw
    exec(compile(source,str(Path(__file__)),'exec'),dict(__name__='__main__',__file__=str(Path(__file__).resolve())))
    if stage!='slots':
        path=H/stage/'expanded-verified.json'
        proof=json.loads(path.read_bytes())
        proof.update(perStoreAcknowledgementDiagnostic=True,logicalAcknowledgementBoundariesOnly=True,
                     independentTimingAccepted=False,exactNativeScheduleAccepted=False)
        path.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['off','on','slots'],required=True)
    main(parser.parse_args().stage)
