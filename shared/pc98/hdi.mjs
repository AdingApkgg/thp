// Read-only HDI/PC-98 partition and FAT12/FAT16 access. CPU, GDC and sound
// emulation are separate requirements; mounting this disk is not game execution.
const check=(ok,message)=>{if(!ok)throw Error(message);};
export function openHdi(input,{filenameEncoding='shift_jis'}={}){
 const bytes=new Uint8Array(input.buffer,input.byteOffset,input.byteLength);
 const data=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 const word=p=>data.getUint16(p,true),dword=p=>data.getUint32(p,true);
 check(bytes.length>=32,'truncated HDI header');
 const header=dword(8),length=dword(12),sector=dword(16),tracks=dword(20),heads=dword(24),cylinders=dword(28);
 check(header>=32&&header<=bytes.length&&length===bytes.length-header,'invalid HDI extent');
 check([256,512,1024].includes(sector)&&tracks>0&&heads>0&&cylinders>0&&sector*tracks*heads*cylinders===length,'invalid HDI geometry');
 check(length>=2*sector,'missing PC-98 partition table');
 const partitions=[];
 for(let i=0;i<Math.min(16,sector/32);i++){
  const p=header+sector+i*32;
  if((bytes[p]&0x7f)!==0x21)continue; // PC-98 DOS partition MID.
  const s=bytes[p+8],h=bytes[p+9],c=word(p+10);
  check(s<tracks&&h<heads&&c<cylinders,'invalid partition CHS');
  const start=header+((c*heads+h)*tracks+s)*sector;
  check(start+64<=bytes.length,'partition outside HDI');
  const bps=word(start+11),spc=bytes[start+13],reserved=word(start+14),fats=bytes[start+16],rootCount=word(start+17);
  const total=word(start+19)||dword(start+32),fatSectors=word(start+22);
  check([512,1024,2048,4096].includes(bps)&&spc>0&&(spc&(spc-1))===0&&reserved>0&&fats>0&&fatSectors>0&&rootCount>0,'unsupported FAT BPB');
  check(total*bps<=bytes.length-start,'FAT volume outside HDI');
  const rootSectors=Math.ceil(rootCount*32/bps),firstData=reserved+fats*fatSectors+rootSectors;
  const clusters=Math.floor((total-firstData)/spc),bits=clusters<4085?12:16;
  check(clusters>0&&clusters<65525,'unsupported FAT cluster count');
  const fat=start+reserved*bps,root=start+(reserved+fats*fatSectors)*bps,body=start+firstData*bps,clusterBytes=spc*bps;
  check(Math.ceil((clusters+2)*bits/8)<=fatSectors*bps,'FAT table is too short');
  const next=n=>bits===12?((n&1)?word(fat+Math.floor(n*1.5))>>4:word(fat+Math.floor(n*1.5))&0xfff):word(fat+n*2);
  const end=bits===12?0xff8:0xfff8;
  function chain(first){
   const list=[],seen=new Set();let n=first;
   while(n<end){check(n>=2&&n<clusters+2&&!seen.has(n),'invalid or cyclic FAT chain');seen.add(n);list.push(n);n=next(n);}
   return list;
  }
  function clusterData(first){const numbers=chain(first),out=new Uint8Array(numbers.length*clusterBytes);
   numbers.forEach((n,j)=>out.set(bytes.subarray(body+(n-2)*clusterBytes,body+(n-1)*clusterBytes),j*clusterBytes));return out;}
  function directory(raw,path){
   const entries=[],v=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);
   for(let at=0;at+32<=raw.length;at+=32){
    if(raw[at]===0)break;if(raw[at]===0xe5||raw[at+11]===0x0f||(raw[at+11]&8))continue;
    const decode=b=>new TextDecoder(filenameEncoding).decode(b).trimEnd();
    const stem=decode(raw.subarray(at,at+8)),extension=decode(raw.subarray(at+8,at+11));
    if(stem==='.'||stem==='..')continue;
    const name=stem+(extension?'.'+extension:'');
    entries.push({path:path+name,name,directory:!!(raw[at+11]&16),cluster:v.getUint16(at+26,true),bytes:v.getUint32(at+28,true)});
   }
   return entries;
  }
  const entries=[],seenDirectories=new Set();
  function walk(rows,depth){check(depth<64,'FAT directory nesting too deep');
   for(const entry of rows){check(entries.length<100000,'too many FAT entries');entries.push(entry);
    if(entry.directory){check(!seenDirectories.has(entry.cluster),'cyclic FAT directory');seenDirectories.add(entry.cluster);
     walk(directory(clusterData(entry.cluster),entry.path+'/'),depth+1);}
   }
  }
  walk(directory(bytes.subarray(root,root+rootCount*32),''),0);
  partitions.push({index:i,label:new TextDecoder('shift_jis').decode(bytes.subarray(p+16,p+32)).trim(),
   offset:start,bytes:total*bps,fatBits:bits,sectorBytes:bps,clusterBytes,entries,
   readFile(path){const entry=entries.find(e=>e.path.toUpperCase()===path.replaceAll('\\','/').toUpperCase());
    check(entry&&!entry.directory,'file not found in FAT volume');if(!entry.bytes)return new Uint8Array();
    const content=clusterData(entry.cluster);check(entry.bytes<=content.length,'file exceeds FAT chain');return content.slice(0,entry.bytes);}
  });
 }
 check(partitions.length>0,'no PC-98 DOS partition found');
 return {format:'HDI',headerBytes:header,physicalSectorBytes:sector,partitions};
}
