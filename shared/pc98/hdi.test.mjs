import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,readdirSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {openHdi} from './hdi.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th01/target.json'),'utf8'));
const original=readFileSync(target.diskImage.path);

test('All Japanese PC-98 disk files agree byte-for-byte with 7-Zip FAT extraction',()=>{
 assert.equal(createHash('sha256').update(original).digest('hex'),target.diskImage.sha256);
 // 7-Zip's FAT reader uses the local ANSI page for 8.3 names (CP936 on
 // this host). Match that spelling for comparison; the runtime defaults to SJIS.
 const disk=openHdi(original,{filenameEncoding:process.env.SEVEN_ZIP_FAT_ENCODING??'gbk'}),parent=resolve(root,'artifacts/pc98');mkdirSync(parent,{recursive:true});
 const extraction=mkdtempSync(join(parent,'sevenzip-'));
 let compared=0;
 for(const partition of disk.partitions){
  const raw=Buffer.from(original.subarray(partition.offset,partition.offset+partition.bytes));
  // PC-98 boot sectors have no IBM-PC 55AA marker. Add ONLY that marker in
  // this disposable volume copy so 7-Zip recognizes its unchanged FAT/BPB.
  // The original disk and all FAT metadata and file bytes remain untouched.
  raw[510]=0x55;raw[511]=0xaa;
  const image=join(extraction,`volume-${partition.index}.img`),files=join(extraction,`files-${partition.index}`);
  writeFileSync(image,raw);
  execFileSync(process.env.SEVEN_ZIP??'C:/Program Files/7-Zip/7z.exe',['x','-tFAT','-y',`-o${files}`,image],{windowsHide:true,stdio:'pipe'});
  const paths=[];
  function walk(directory,prefix=''){for(const entry of readdirSync(directory,{withFileTypes:true})){
   if(entry.isDirectory())walk(join(directory,entry.name),prefix+entry.name+'/');else paths.push(prefix+entry.name);}}
  walk(files);
  assert.deepEqual(paths.sort(),partition.entries.filter(e=>!e.directory).map(e=>e.path).sort());
  for(const path of paths){assert.deepEqual(Buffer.from(partition.readFile(path)),readFileSync(join(files,path)),path);compared++;}
 }
 writeFileSync(join(parent,'sevenzip-comparison.json'),JSON.stringify({passed:true,compared,diskSha256:target.diskImage.sha256,
  compatibilityChange:'Only 55AA at byte 510 in a disposable partition copy.',extraction},null,2)+'\n');
 console.log(`Compared ${compared} FAT files against 7-Zip.`);
});

test('HDI reader rejects broken geometry and cyclic FAT allocation',()=>{
 assert.throws(()=>openHdi(new Uint8Array(16)),/truncated HDI/);
 const geometry=Buffer.from(original);geometry.writeUInt32LE(0,16);
 assert.throws(()=>openHdi(geometry),/geometry/);
 const disk=openHdi(original),p=disk.partitions[0],broken=Buffer.from(original);
 const entry=p.entries.find(e=>e.directory),fat=p.offset+broken.readUInt16LE(p.offset+14)*p.sectorBytes;
 const at=fat+Math.floor(entry.cluster*1.5),word=broken.readUInt16LE(at);
 broken.writeUInt16LE(entry.cluster&1?(word&15)|(entry.cluster<<4):(word&0xf000)|entry.cluster,at);
 assert.throws(()=>openHdi(broken),/cyclic FAT chain/);
});
