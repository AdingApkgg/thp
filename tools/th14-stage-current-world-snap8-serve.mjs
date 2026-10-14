// New isolated endpoint, reuse the exact validated comparison page/server logic.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
let s=readFileSync(resolve(root,'tools/th14-stage-current-graphics-serve.mjs'),'utf8');
assert.equal(createHash('sha256').update(s).digest('hex'),'2e72fbcf13e1f919bc1c93a6fc3d2457da90494233ac1c5c77c4b8b246546e80','Comparison server source changed');
for(const [a,b] of [['stage-current-graphics-fe406-oct14','stage-current-world-snap8-fe406-oct14'],['TH14_CURRENT_GRAPHICS_PORT','TH14_CURRENT_WORLD_SNAP8_PORT'],['8237','8239']])s=s.replaceAll(a,b);
// Use Node's module loader so imports and immutable file routes are unchanged.
const source=s.replace('import.meta.dirname',JSON.stringify(import.meta.dirname));
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
