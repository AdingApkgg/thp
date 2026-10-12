# Tasofro resource access

`archives.mjs` is a browser-compatible module for original TFPK archives
(TH13.5/14.5/15.5) and CG archives (TH17.5). It imports no Node APIs.
The native shared C++ `Archive` reader separately handles TH7.5/10.5/12.3 DAT.

```js
import {openTfpk, openCg, tfpkPathHash} from './archives.mjs';

// file is a File chosen by the user. Reads stay local.
const readAt = async (offset, length) =>
  new Uint8Array(await file.slice(offset, offset + length).arrayBuffer());
const archive = await openTfpk(readAt, file.size);
const hash = tfpkPathHash('data/script/boot.nut', archive.version);
const entry = archive.entries.find(entry => entry.hash === hash);
if (entry) {
  const bytes = await archive.readEntry(entry.index);
}
```

`openCg(readAt, size)` provides the same `entries` / `readEntry(index)` interface;
its hashes are hexadecimal strings because its directory stores 64-bit fields.
Both readers check directory bounds before exposing entries. Neither writes to
the supplied file. The callback must return exactly the requested byte range.

TFPK archives may omit the original filename dictionary; those entries have
`name: null`, retaining the original hash. `tfpkPathHash` accepts ASCII strings
or raw Shift-JIS bytes. It does not silently reinterpret Japanese paths as UTF-8.
TH14.5's local Chinese `th145c.pak` uses an unrecognized RSA key; the default
validation covers original packages and official update packages.

These modules provide resource access. Squirrel/ACT/PAT execution, rendering,
input, battle logic, sound and replay compatibility remain separate port work.

Validation from the repository root:

```powershell
node tools/th-tasofro-resources.mjs --verify-all
py -3 -m unittest discover -s tools/tests -p test_tasofro_resources.py -v
node --test shared/tasofro/archives.test.mjs
```

The Python comparison requires the pinned public-domain `reference/135tk`
checkout described in `NOTICE.txt`. It independently reads every directory
entry and checks decoded prefixes against the JS reports. Full-entry hashes
record what the JS reader decoded; they are not original-engine gameplay proof.
