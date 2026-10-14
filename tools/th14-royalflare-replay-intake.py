"""Download three explicitly listed independent player recordings as private data.

These are inputs, not executable code or a gameplay oracle. The original
4028e0/465840 codec verifier must validate selections before playback.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'artifacts/th14/royalflare-replay-reference-oct14'
PAGE = 'https://maribelhearn.com/royalflare/th14'
CASES = (
    ('th14_ud0933', 'YMD', 'MarisaA Normal, 2021-05-01', (1, 0, 1)),
    ('th14_ud0984', 'みょん吉', 'MarisaB Easy, 2021-12-14', (1, 1, 0)),
    ('th14_ud0967', 'Dean', 'SakuyaB Hard, 2021-10-19', (2, 1, 2)),
)


def download(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'TH14-reference-verification/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        assert response.status == 200
        data = response.read(2_000_001)
        assert len(data) <= 2_000_000
        return data


def write_once(path, data):
    if path.exists():
        assert path.read_bytes() == data, 'existing private input differs: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(data)


def main():
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    page = download(PAGE)
    write_once(DIRECTORY / 'source-page.html', page)
    for name, player, claim, expected in CASES:
        assert ('/replays/royalflare/th14/' + name + '.rpy').encode() in page
        url = 'https://maribelhearn.com/replays/royalflare/th14/' + name + '.rpy'
        data = download(url)
        assert data[:6] == b't13r\x02\x00'
        write_once(DIRECTORY / (name + '.rpy'), data)
        metadata = dict(status='DOWNLOADED_NOT_DECODED_OR_PLAYBACK_VERIFIED', completeGame=False,
                        nativeEquivalent=False, sourcePage=PAGE, sourceUrl=url, player=player,
                        sourceClaim=claim, expectedSelection=list(expected), bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(),
                        sourcePageSha256=hashlib.sha256(page).hexdigest(),
                        intakeToolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        scope='Intact independent public player input downloaded from a verified page link. '
                              'Private data only; no code execution, state generation, playback or original clear claim.')
        write_once(DIRECTORY / (name + '-source.json'), (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode())
        print(json.dumps(dict(name=name, bytes=len(data), sha256=metadata['sha256'], sourceUrl=url)))


if __name__ == '__main__':
    main()
