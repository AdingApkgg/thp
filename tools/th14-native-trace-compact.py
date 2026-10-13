"""Remove JSON whitespace only, preserving every original capture value and row."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    source,target=[(ROOT/name).resolve() for name in (a.input,a.output)]
    assert all(path.is_relative_to(ROOT/'artifacts/th14') for path in (source,target))
    assert source!=target and not target.exists()
    raw=source.read_bytes();original=json.loads(raw)
    encoded=json.dumps(original,separators=(',',':'),ensure_ascii=True).encode()
    assert json.loads(encoded)==original
    target.write_bytes(encoded)
    receipt=dict(source=source.relative_to(ROOT).as_posix(),sourceBytes=len(raw),sourceSha256=hashlib.sha256(raw).hexdigest(),
                 output=target.relative_to(ROOT).as_posix(),outputBytes=len(encoded),outputSha256=hashlib.sha256(encoded).hexdigest(),
                 allValuesEqual=True,frames=len(original['frames']),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 scope='JSON whitespace representation only. Exact parsed equality includes every frame, array, field, difference and metadata value. No filtering, trimming, row merging or normalization of gameplay values.')
    target.with_suffix('.compact-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
