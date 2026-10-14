// Reuse the already validated isolated page and restricted capture routes.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const file=resolve(import.meta.dirname,'th14-stage-sequential-clip-scaled-bias-serve.mjs');
let source=readFileSync(file,'utf8');
assert.equal(createHash('sha256').update(source).digest('hex'),'df1fc879a0508e99378e4f58096158799285b19e09eec6d942ec15e28f930127');
for(const [a,b] of [['stage-current-sequential-clip-scaled-bias-fe406-oct14','stage-current-sequential-row-dot-fe406-oct14'],['TH14_SEQUENTIAL_CLIP_SCALED_BIAS_PORT','TH14_SEQUENTIAL_ROW_DOT_PORT'],['8248','8251']])source=source.replaceAll(a,b);
source=source.replace('import.meta.dirname',JSON.stringify(import.meta.dirname));
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
