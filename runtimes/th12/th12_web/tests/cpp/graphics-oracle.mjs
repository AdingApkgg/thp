// Development-only reference DLL. No Windows library enters the browser build.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {PEImage} from '../../scripts/native/pe.mjs';
import {root,sha} from './helpers.mjs';
import {original} from './originals.mjs';
export function graphicsOracle(m){
 // Round 306: the DLL is a system reference, not a repository file - fourteen suites failed before they
 // ran because this path did not exist in the checkout. original() finds the machine's own copy and
 // names everything it searched when it cannot. The hash below still decides whether it is the right one.
 const bytes=readFileSync(original('native/d3dx9_37.dll'));
 if(sha(bytes)!=='c2ccb84c672a9d8966e82a28005a4269886ee304972ac3590c0b8a9c1622a3d8')throw Error('Unexpected reference math DLL');
 const image=new PEImage(bytes),base=0x1000000,delta=base-image.base;
 m.write(base,bytes.subarray(0,image.headerSize));
 // Round 307: a section's virtual size can exceed its raw size - the uninitialised tail - and that
 // tail is where a reference routine's tables and scratch live. Only the raw part used to be written,
 // so a read of the tail depended on whatever the guest happened to hold. Zero it, which is what the
 // loader does, and measure whether the family's in-image trap was this.
 let virtualBytes=0;
 for(const s of image.sections)if(s.virtualSize>s.rawSize){m.write(base+s.rva+s.rawSize,Buffer.alloc(s.virtualSize-s.rawSize));virtualBytes+=s.virtualSize-s.rawSize;}
 if(process.env.TH_GRAPHICS_TRACE)console.log('zeroed %d bytes of section tails',virtualBytes);
 for(const s of image.sections)if(s.rawSize)m.write(base+s.rva,bytes.subarray(s.raw,s.raw+s.rawSize));
 const reloc=image.directories[5];for(let offset=0;offset<reloc.size;){const p=base+reloc.rva+offset,page=m.u32(p),size=m.u32(p+4);if(size<8)break;const entries=Buffer.from(m.bytes(p+8,size-8));for(let i=0;i<entries.length;i+=2){const v=entries.readUInt16LE(i);if(v>>>12===3){const address=base+page+(v&4095);m.u32(address,m.u32(address)+delta);}else if(v>>>12)throw Error('Unsupported relocation');}offset+=size;}
 for(const e of image.imports){
  if(e.name==='_CIsqrt'){const code=m.allocate(16);m.write(code,Uint8Array.of(0xd9,0xfa,0xc3));m.u32(e.address+delta,code);}
  else if(e.name==='floor'){const code=m.allocate(64);m.write(code,Buffer.from('83ec08d93c24668b04246625fff3660d00046689442402d96c2402dd44240cd9fcd92c2483c408c3','hex'));m.u32(e.address+delta,code);}
  else m.u32(e.address+delta,m.registerImport(e));
 }
 const exports=new Map(),dir=base+image.directories[0].rva,count=m.u32(dir+24),names=base+m.u32(dir+32),ordinals=base+m.u32(dir+36),functions=base+m.u32(dir+28);
 for(let i=0;i<count;++i){const name=m.string(base+m.u32(names+i*4)),ordinal=Buffer.from(m.bytes(ordinals+i*2,2)).readUInt16LE(0);exports.set(name,base+m.u32(functions+ordinal*4));}
 for(const e of m.image.imports)if(e.dll==='d3dx9_37.dll'){const address=exports.get(e.name);if(!address)throw Error('Missing '+e.name);m.u32(e.address,address);}
 // Choose the DLL's shipped scalar math table. CPU-specific SSE/3DNow
 // dispatch and process initialization are intentionally outside this fixture.
 m.write(base+0x36c048,m.bytes(base+0x36c170,0x4a*4));m.u32(base+0x36c29c,0);
 return {base,image,exports};
}
