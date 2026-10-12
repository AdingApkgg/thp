"""Encode a title's own PCM as local OGG and verify decoded frame and loop bounds.

The same reading the TH14 preparation used, for any title that ships an archive and a converted
runtime directory: `thbgm.fmt` is the layout (offset, preload, intro, length, then the format
word), `thbgm.dat` holds the PCM the layout points into, and the room's comments give the cue
order. Every row the header carries is asserted to be exactly the comments followed by the records
no comment names, so the table, the layout and the room have to agree before a byte is written.

  py -3 tools/th-prepare-music.py <title>
"""
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]


def target_path(title):
    nested = ROOT / ('runtimes/th%d/target.json' % title)
    if nested.exists():
        return nested
    return ROOT / ('runtimes/th%d/th%d_web/target.json' % (title, title))


def main(title):
    archive = json.loads((ROOT / ('artifacts/archive-differential/th%d.json' % title)).read_text(encoding='utf-8'))
    data = Path(archive['extraction'])
    formats = (data / 'thbgm.fmt').read_bytes()
    sha = lambda b: hashlib.sha256(b).hexdigest()
    assert sha(formats) == next(r['sha256'] for r in archive['decoded'] if r['name'] == 'thbgm.fmt')
    comments = [c.decode() for c in re.findall(rb'@bgm/([A-Za-z0-9_]+)', (data / 'musiccmt.txt').read_bytes())]
    comment_stems = [c.removesuffix('.wav') for c in comments]
    names = [formats[n:n + 16].split(b'\0')[0].decode('ascii').removesuffix('.wav')
             for n in range(0, len(formats) - 51, 52) if formats[n]]
    # The comment file is written with the `.wav` suffix on some titles and without it on others, so
    # the comparison is on stems: TH14 writes no suffix and TH16/17/18 write it.
    expected = comment_stems + [s for s in names if s not in comment_stems]
    catalog = (ROOT / 'runtimes/th12/th12_web/cpp/game/MusicCatalog.hpp').read_text(encoding='utf-8')
    block = re.search(r'th%d_music_tracks\[\]=\{(.*?)\};' % title, catalog, re.S)
    actual = [name for _, name in re.findall(r'\{(\d+),"([^"]+)"\}', block.group(1))]
    assert actual == expected, ('the header and the files disagree',
                               [n for n, (a, e) in enumerate(zip(actual, expected)) if a != e])
    target = json.loads(target_path(title).read_text(encoding='utf-8'))
    source_path = Path(target['dataArchives']['thbgm.dat']['path'])
    out = ROOT / ('runtimes/th%d/th%d_web/assets/sdl-native' % (title, title))
    (out / 'music').mkdir(parents=True, exist_ok=True)
    report = []
    with source_path.open('rb') as source:
        magic = source.read(4)
        assert magic == b'ZWAV', magic
        for n, stem in enumerate(names):
            name, offset, preload, intro, length = struct.unpack_from('<16sIIII', formats, n * 52)
            format_tag, channels, rate, byte_rate, align, bits = struct.unpack_from('<HHIIHH', formats, n * 52 + 32)
            assert format_tag == 1 and channels == 2 and bits == 16 and align == 4 and byte_rate == rate * align
            assert length % align == 0 and intro % align == 0 and 0 <= intro < length and offset + length <= source_path.stat().st_size
            if n + 1 < len(names):
                assert offset + length == struct.unpack_from('<I', formats, (n + 1) * 52 + 16)[0]
            source.seek(offset)
            pcm = source.read(length)
            assert len(pcm) == length
            samples = np.frombuffer(pcm, dtype='<i2').reshape(-1, channels)
            path = out / 'music' / (stem + '.ogg')
            if not path.exists() or sf.info(str(path)).frames != len(samples):
                pending = path.with_suffix('.ogg.tmp')
                with sf.SoundFile(str(pending), 'w', samplerate=rate, channels=channels, subtype='VORBIS',
                                  format='OGG', compression_level=.4) as dest:
                    for at in range(0, len(samples), 16384):
                        dest.write(samples[at:at + 16384].astype(np.float32) / 32768.)
                pending.replace(path)
            decoded, decoded_rate = sf.read(str(path), dtype='int16', always_2d=True)
            assert decoded.shape == samples.shape and decoded_rate == rate
            report.append(dict(name=stem + '.wav', file=path.name, frames=len(samples), loopFrame=intro // align,
                              rate=rate, channels=channels, encodedBytes=path.stat().st_size,
                              pcmSha256=sha(pcm), encodedSha256=sha(path.read_bytes()), codec='vorbis', lossless=False))
            print('%d/%d %s: %d frames, loop %d' % (n + 1, len(names), stem, len(samples), intro // align), flush=True)
    (out / 'music-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    proof = dict(passed=True, title=title, tracks=len(report), comments=len(comments),
                 frames=sum(r['frames'] for r in report), formatSha256=sha(formats),
                 musicOrder=expected, tracksVerified=report,
                 scope='Local Vorbis conversion per title; decoded frame counts, sample rates, channels, loop boundaries and room cue mapping. Lossy encoding, not PCM equivalence.',
                 toolSha256=sha(Path(__file__).read_bytes()))
    (ROOT / ('docs/porting/th%d-music-verified.json' % title)).write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print('PASS: %d original TH%d music tracks, %d decoded frames.' % (len(report), title, proof['frames']))


if __name__ == '__main__':
    main(int(sys.argv[1]))
