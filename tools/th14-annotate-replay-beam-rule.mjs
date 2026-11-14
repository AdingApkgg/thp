// Creates a separate copy only after the recording's rule is explicitly chosen.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {parseArgs} from 'node:util';
import {annotateTh14ReplayBeamRule} from '../runtimes/th12/portable/browser/th14-replay-beam-rules.mjs';
const {values}=parseArgs({options:{input:{type:'string'},output:{type:'string'},rule:{type:'string'},'expect-sha256':{type:'string'}}});
if(!values.input||!values.output||!['native','bounded'].includes(values.rule)||!/^[a-f0-9]{64}$/i.test(values['expect-sha256']??''))throw new Error('Usage: node tools/th14-annotate-replay-beam-rule.mjs --input OLD.rpy --output NEW.rpy --rule native|bounded --expect-sha256 SHA256. Use only when the TH14 recording rule is known; rules cannot be inferred.');
const source=resolve(values.input),target=resolve(values.output);
if(source===target)throw new Error('Output must be a new file');
const hash=b=>createHash('sha256').update(b).digest('hex');
const input=await readFile(source),inputSha256=hash(input);
if(inputSha256!==values['expect-sha256'].toLowerCase())throw new Error('Input hash mismatch');
const result=annotateTh14ReplayBeamRule(input,values.rule==='bounded'?1:0);
await writeFile(target,result,{flag:'wx'});
console.log(JSON.stringify({inputSha256,outputSha256:hash(result),rule:values.rule,addedBytes:20,inputPreserved:true,originalPrefixPreserved:true,scope:'explicit user-selected annotation; container checks only, not gameplay acceptance'}));
