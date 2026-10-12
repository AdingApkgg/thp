// The box of one-at-a-time engine acceptance cases (see engine-case.mjs for why one process each).
//
//   node engine-acceptance.mjs window --from 0x402540 --to 0x402570 [--mode bare] [--implant c3]
//   node engine-acceptance.mjs sample --count 24
//   node engine-acceptance.mjs case --entry 0x402551 [--mode bare] [--implant c3]
//
// It spawns one node process per case, prints a table, and with --out merges the cases into a JSON
// box document. The grid a run covers is written into the document, so a table can be re-measured
// instead of quoted.
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

const argv=process.argv.slice(2);
const value=(name,fallback)=>{const at=argv.indexOf('--'+name);return at<0?fallback:argv[at+1];};
const has=name=>argv.includes('--'+name);
const command=argv[0];
const number=text=>Number(text)>=0?Number(text):undefined;
const here=fileURLToPath(new URL('.',import.meta.url));
const caseFile=here+'engine-case.mjs';

const cases=[];
if(command==='case'){
  const spec={entry:value('entry','0x402551'),mode:value('mode','bare')};
  if(value('implant',null)!==null)spec.implant=value('implant');
  if(value('frame',null)!==null)spec.frame=value('frame');
  if(value('esi',null)!==null)spec.esi=value('esi');
  if(value('limit',null)!==null)spec.limit=Number(value('limit'));
  if(value('trace',null)!==null)spec.trace=Number(value('trace'));
  cases.push(spec);
}else if(command==='prefix'){
  const tail=value('tail',process.env.TAIL??'');
  for(const length of value('lengths','2,5,9,13,16,19,22,25,28,32').split(','))
    cases.push({entry:value('from','0x402551'),mode:value('mode','bare'),prefixBytes:Number(length),
      implant:tail.slice(0,Number(length)*2)+'c3'});
}else if(command==='window'){
  const from=Number(value('from','0x402540')),to=Number(value('to','0x402570'));
  for(let address=from;address<=to;address++)
    cases.push({entry:'0x'+address.toString(16),mode:value('mode','bare'),implant:value('implant',null)||undefined});
}else if(command==='sample'){
  // a deterministic spread of `.text` addresses (th12's .text runs 0x401000..0x497ad5)
  const count=Number(value('count','24')),step=0x1024;
  for(let index=0;index<count;index++){
    const address=0x402000+index*step*7%0x90000;
    cases.push({entry:'0x'+address.toString(16),mode:value('mode','bare'),implant:value('implant','c3')});
  }
}else{
  console.error('usage: engine-acceptance.mjs case|window|sample [options]');process.exit(2);
}

const results=[];
for(const spec of cases){
  const run=spawnSync(process.execPath,[caseFile,JSON.stringify(spec)],{encoding:'utf8'});
  const line=(run.stdout??'').trim().split('\n').filter(Boolean).pop();
  let result;
  try{result=JSON.parse(line);}
  catch{result={spec,verdict:'runner-error',detail:((run.stderr??'')+String(line)).trim().slice(-90)};}
  results.push(result);
  console.log('  '+String(result.spec.entry).padEnd(9)+String(result.spec.mode).padEnd(7)+
    String(result.spec.implant??'-').padEnd(7)+result.verdict.padEnd(7)+result.detail);
}
const tally=results.reduce((all,row)=>(all[row.verdict]=(all[row.verdict]??0)+1,all),{});
console.log('  tally: '+JSON.stringify(tally));
const out=value('out',null);
if(out){
  const document=existsSync(out)?JSON.parse(readFileSync(out,'utf8')):
    {instrument:'runtimes/th12/th12_web/tests/cpp/engine-{acceptance,case}.mjs under tools/emsdk/node',
     method:'one case per node process (section 67)',runs:[]};
  document.runs=document.runs??[];
  document.runs.push({command,argv:argv.slice(1),cases:results.length,tally,
    results:results.map(row=>({entry:row.spec.entry,mode:row.spec.mode,implant:row.spec.implant??null,
      verdict:row.verdict,detail:row.detail}))});
  writeFileSync(out,JSON.stringify(document,null,2).replace(/\n/g,'\r\n')+'\n');
  console.log('  wrote '+out);
}
