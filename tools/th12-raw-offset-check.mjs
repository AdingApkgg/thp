// Guards the lesson from docs/th12/oracle-repointing.md sections 35 and 36: a byte offset copied from the
// machine is only equivalent to a field when the two layouts agree, and otherwise it is an out-of-bounds
// write that lands on whatever this port keeps at that address. Opcode 0x119 did that - a store at
// 0x1e0+index*4 wrote into relative_position's timer and absolute_angle - and it went unnoticed until the
// oracle comparison was widened.
//
// The check flags the shape rather than the address, because the address is exactly what cannot be trusted:
// a reinterpret_cast to a byte pointer of some object followed by a positive offset. Three shapes are
// legitimate and must not be flagged:
//   - the container-of idiom  reinterpret_cast<u8*>(&member) - offsetof(T, member), which subtracts;
//   - within-buffer pointer arithmetic on a script or instruction pointer, which is not an object;
//   - an indexed store through a named base such as &e.drops, which is layout independent by construction.
// So only `&<identifier>)` followed by `+` is reported, and identifiers known to be buffers are excused.
import {readFileSync} from 'node:fs';
import {readdir} from 'node:fs/promises';
import path from 'node:path';

const ROOT = process.argv[2] ?? 'runtimes/th12/th12_web/cpp';
// Script, instruction and buffer pointers: arithmetic on them is byte-level by design and says nothing about
// where this port stores its fields.
const BUFFERS = new Set(['marker','current','script_begin','script','buffer','data','bytes','base','pointer','p']);

async function files(dir){const out=[];for(const e of await readdir(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())out.push(...await files(f));else if(/\.(cpp|hpp)$/.test(e.name))out.push(f);}return out;}

const PATTERN = /reinterpret_cast<\s*(?:const\s+)?(?:u8|char|i8|unsigned char)\s*\*>\s*\(\s*&([A-Za-z_][A-Za-z0-9_]*(?:->[A-Za-z_][A-Za-z0-9_]*)*)\s*\)\s*\+/g;

let count = 0;
for(const file of await files(ROOT)){
    const text = readFileSync(file,'utf8');
    const lines = text.split('\n');
    lines.forEach((line,index)=>{
        PATTERN.lastIndex = 0;
        let match;
        while((match = PATTERN.exec(line))!==null){
            const target = match[1].split('->').pop();
            if(BUFFERS.has(target))continue;
            ++count;
            console.log(`${file.replace(/\\/g,'/')}:${index+1}: raw byte offset on &${match[1]}: ${line.trim().slice(0,120)}`);
        }
    });
}

if(count!==0){
    console.log(`\n${count} raw byte offset write(s): use a named field with a measured capacity instead`);
    process.exit(1);
}
console.log('no raw byte offset writes in the port cpp');
