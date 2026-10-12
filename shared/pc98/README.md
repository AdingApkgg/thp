# PC-98 resource access

`openHdi(bytes)` from `hdi.mjs` reads an HDI header, PC-98 DOS partition table,
and FAT12/FAT16 filesystem entirely in the browser. Each partition exposes
`entries` and `readFile(path)`. File names default to Shift-JIS; callers may
provide `{filenameEncoding: 'gbk'}` for a disk or comparison tool using CP936.
The input buffer must remain unchanged while the returned reader is in use.

```js
import {openHdi} from './hdi.mjs';
const disk = openHdi(new Uint8Array(await file.arrayBuffer()));
const script = disk.partitions[0].readFile('REIIDEN/GAME.BAT');
```

The local `jp.hdi` contains all five original PC-98 titles. Their boot paths
are recorded separately in `runtimes/th01` through `runtimes/th05/target.json`.
Mounting the disk does not execute the games. PC-98 CPU, graphics and sound
support and browser gameplay acceptance remain outstanding.

```powershell
node tools/th-pc98-resources.mjs
node --test shared/pc98/hdi.test.mjs
```

The independent test compares all 163 live FAT files to 7-Zip. PC-98 lacks the
IBM-PC boot signature 7-Zip requires, so the test adds only `55AA` at byte 510
in a disposable partition copy under ignored artifacts. It does not change
FAT metadata, file contents or the original HDI. `SEVEN_ZIP` selects the 7-Zip
executable and `SEVEN_ZIP_FAT_ENCODING` selects its filename code page.
