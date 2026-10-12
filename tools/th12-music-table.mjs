// Derive TH12's music cue table and check the engine's copy against it.
//
// A cue number is the music-room index: the room sets `music_request = selected`
// and indexes the comments parsed from `musiccmt.txt`. That file's entry paths
// match th12's `thbgm.fmt` records 0..16 one for one, which is what fixes the
// order; record 17 (`th10_17.wav`) ships with no room comment.
//
//   node tools/th12-music-table.mjs            # print the derived table
//   node tools/th12-music-table.mjs --check    # verify MusicCatalog.hpp agrees
import { readFileSync, mkdtempSync, rmSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DAT = 'H:/Games/th/12/th12.dat';
const THDAT = resolve(root, 'tools/thtk/extracted/thtk-bin-12/thdat.exe');
const SOURCE = resolve(root, 'runtimes/th12/th12_web/cpp/game/MusicCatalog.hpp');

// os.tmpdir() is not writable in this environment; tools/tmp is gitignored.
const scratch = resolve(root, 'tools/tmp/music-table');
mkdirSync(scratch, { recursive: true });
const work = mkdtempSync(resolve(scratch, 'run-'));
let formats, comments;
try {
  execFileSync(THDAT, ['-x', 'd', DAT, 'thbgm.fmt', 'musiccmt.txt'], { cwd: work, stdio: 'pipe' });
  formats = readFileSync(resolve(work, 'thbgm.fmt'));
  comments = readFileSync(resolve(work, 'musiccmt.txt'));
} finally {
  rmSync(work, { recursive: true, force: true });
}

// thbgm.fmt: 52-byte records, <16s name> then u32 offsets; the name is the
// second field the runtime looks up, so the stem is the cue's file.
const records = [];
for (let at = 0; at + 52 <= formats.length && formats[at]; at += 52) {
  const name = formats.subarray(at, at + 16).toString('latin1').split('\0')[0];
  if (!/^[a-z0-9_]+\.wav$/.test(name)) throw Error(`record ${records.length}: bad name ${JSON.stringify(name)}`);
  const tail = [formats.readUInt16LE(at + 32), formats.readUInt16LE(at + 34),
                formats.readUInt32LE(at + 36), formats.readUInt32LE(at + 40),
                formats.readUInt16LE(at + 44), formats.readUInt16LE(at + 46)];
  if (tail.join() !== '1,2,44100,176400,4,16') throw Error(`record ${name}: unexpected tail ${tail}`);
  records.push(basename(name, '.wav'));
}

// musiccmt.txt: an entry is '@' + path line + title line, in music-room order.
const lines = comments.toString('latin1').split(/\r\n|\n|\r/);
const room = [];
for (let i = 0; i < lines.length; i++) {
  if (lines[i][0] !== '@') continue;
  const path = lines[i].slice(1);
  if (!/^bgm\/[a-z0-9_]+\.wav$/.test(path)) throw Error(`comment ${room.length}: bad path ${JSON.stringify(path)}`);
  room.push(basename(path, '.wav'));
}

const problems = [];

// The room order must be the head of the thbgm order; that is the evidence the
// cue numbers come from, so it is checked before anything is trusted.
if (room.length >= records.length) problems.push(`musiccmt lists ${room.length} tracks, thbgm has only ${records.length}`);
for (let i = 0; i < room.length && i < records.length; i++) {
  if (room[i] !== records[i]) problems.push(`musiccmt[${i}] is ${room[i]} but thbgm[${i}] is ${records[i]}`);
}
if (records[records.length - 1] !== 'th10_17') problems.push(`last thbgm record is ${records[records.length - 1]}, expected the th10_17 leftover`);

const source = readFileSync(SOURCE, 'utf8');
const block = /music_tracks\[\]\s*=\s*\{([\s\S]*?)\};/.exec(source);
if (!block) problems.push('MusicCatalog.hpp: could not find the music_tracks array');
else {
  const listed = [...block[1].matchAll(/\{\s*(\d+)\s*,\s*"([^"]+)"\s*\}/g)].map(m => ({ cue: Number(m[1]), file: m[2] }));
  if (listed.length !== records.length) problems.push(`engine lists ${listed.length} cues, thbgm has ${records.length} records`);
  for (let i = 0; i < Math.min(listed.length, records.length); i++) {
    if (listed[i].cue !== i) problems.push(`entry ${i} declares cue ${listed[i].cue}`);
    if (listed[i].file !== records[i]) problems.push(`cue ${i}: engine has ${listed[i].file}, thbgm has ${records[i]}`);
  }
}

if (problems.length) {
  console.error(`th12 music table: ${problems.length} problem(s)`);
  for (const p of problems) console.error('  - ' + p);
  process.exit(1);
}
console.log(`th12 music table: OK — ${records.length} cues match thbgm.fmt, ` +
            `first ${room.length} confirmed by musiccmt.txt order`);
