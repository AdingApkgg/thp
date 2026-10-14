"""Make reviewable combined19-file patches from immutable private source."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'artifacts/th14/staged-loader-integration-oct14'
FROZEN = HOME / 'cancel-v3'
SOURCE = FROZEN / 'source/runtimes/th12/th12_web'
BASELINE = HOME / 'baseline/runtimes/th12/th12_web'
SHA = lambda b: hashlib.sha256(b).hexdigest()

manifest_bytes = (FROZEN / 'frozen-source.json').read_bytes()
manifest = json.loads(manifest_bytes)
for row in manifest['files']:
    assert SHA((FROZEN / 'source/runtimes' / row['path']).read_bytes()) == row['sha256']

changes, patches = [], []
for path in sorted((SOURCE / 'cpp').rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(SOURCE)
    old_path = BASELINE / relative
    old = old_path.read_bytes() if old_path.exists() else b''
    new = path.read_bytes()
    if old == new:
        continue
    repo = 'runtimes/th12/th12_web/' + relative.as_posix()
    changes.append(dict(path=repo, baselineSha256=SHA(old) if old else None,
                        baselineBytes=len(old), newSha256=SHA(new), newBytes=len(new)))
    patches.extend(difflib.unified_diff(old.decode('utf-8').replace('\r\n', '\n').splitlines(True),
                                       new.decode('utf-8').replace('\r\n', '\n').splitlines(True),
                                       fromfile='a/' + repo if old else '/dev/null',
                                       tofile='b/' + repo))
assert len(changes) == 19, len(changes)
patch_bytes = ''.join(patches).encode('utf-8')
patch_path = FROZEN / 'combined-stage-loader-intrinsic.patch'
patch_path.write_bytes(patch_bytes)

# A separate Application patch has only changed hunks, never a whole-file copy.
app_repo = 'runtimes/th12/th12_web/cpp/sdl/Application.cpp'
app_old = (BASELINE / 'cpp/sdl/Application.cpp').read_text().replace('\r\n', '\n')
app_new = (SOURCE / 'cpp/sdl/Application.cpp').read_text().replace('\r\n', '\n')
app_patch = ''.join(difflib.unified_diff(app_old.splitlines(True), app_new.splitlines(True),
                                       fromfile='a/' + app_repo, tofile='b/' + app_repo)).encode()
(FROZEN / 'application-composed.patch').write_bytes(app_patch)

receipt = dict(combinedPrivateSourceFrozen=True, productionChanged=False, productionVerified=False,
               nativeEquivalent=False, completeGame=False, changedFiles=changes,
               changedFileCount=19, frozenSourceSha256=SHA(manifest_bytes),
               combinedPatch=str(patch_path.relative_to(ROOT)).replace('\\', '/'),
               combinedPatchSha256=SHA(patch_bytes), applicationHunkPatchSha256=SHA(app_patch),
               intrinsicSourceReport='docs/porting/th14-deferred-capture-intrinsic-final-verified-oct14.json',
               helperReport='docs/porting/th14-stage-upload-owner-unit-verified-oct14.json',
               supervisorReport='docs/porting/th14-loader-supervisor-flags-verified-oct14.json',
               scope='Frozen combined private19-file implementation; exact baseline/new byte SHA retained. '
                     'Unified patches normalize line endings for review only. Application is composed from '
                     'small upload/clock/cancel/host-close and separately reviewed capture hunks. No1:1, '
                     'current production, final browser/GPU pixels/ending or inherited v2 runtime claim.',
               toolSha256=SHA(Path(__file__).read_bytes()))
(FROZEN / 'combined-source.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(changedFileCount=19, combinedPatchSha256=SHA(patch_bytes),
                      frozenSourceSha256=SHA(manifest_bytes))))
