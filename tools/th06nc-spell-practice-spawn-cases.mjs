import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {EnemyPool} from '../shared/th06nc/enemy-pool.mjs';
import {readEcl} from '../shared/th06nc/ecl.mjs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {spawnSpellPracticeEnemy} from '../shared/th06nc/spell-practice-spawn.mjs';
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),count=Math.max(...table.map(r=>r.subroutine))+1,base=16+count*4,program=Buffer.alloc(base+count*40),cases=[];program.writeUInt16LE(count);
for(let i=0;i<count;i++){const p=base+i*40;program.writeUInt32LE(p,16+i*4);for(const [offset,time,opcode,length]of [[0,0,111,16],[16,1,0,12],[28,-1,-1,12]]){program.writeInt32LE(time,p+offset);program.writeInt16LE(opcode,p+offset+4);program.writeUInt16LE(length,p+offset+6);program[p+offset+9]=255;}program.writeInt32LE(1000+i,p+12);}
const parsed=readEcl(program),sha=b=>createHash('sha256').update(b).digest('hex');
for(const id of [...table.map(r=>r.id),131,255,256,-1])for(const occupied of [0,3,256])for(const started of [false,true]){
 const environment={difficulty:1,spellPractice:true,spellPracticeIndex:id,spellEnemyStarted:started},pool=new EnemyPool(parsed,{environment});for(let i=0;i<occupied;i++)pool.storage[i*0x10b0+0xbc]=128;
 const entry=spawnSpellPracticeEnemy(pool,table),again=spawnSpellPracticeEnemy(pool,table);
 if(again)throw Error('spell enemy repeated');cases.push({id,occupied,started,afterStarted:environment.spellEnemyStarted,slot:entry?.slot??null,enemy:entry?Buffer.from(entry.enemy).toString('hex'):null,poolSha256:sha(pool.storage)});
}
writeFileSync('tools/tmp/th06nc-spell-practice-spawn-cases.json',JSON.stringify({table,program:program.toString('hex'),cases}));console.log(JSON.stringify({cases:cases.length,subroutines:count}));
