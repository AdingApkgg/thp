// The oracle fixtures name the addresses of the title the port started from. The tables under
// docs/porting record the counterpart of each of those addresses in another title, measured by
// tools/th-twin-find.py (code), tools/th-twin-global.py (data) and tools/th-twin-global.py for the
// plain constants a fixture carries (a structure's size, which grows between titles).
// touch() translates a fixture's constant to the title this runtime targets, and returns it
// unchanged when no row claims it, so a fixture keeps working for the title it was written for.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {root,target} from './helpers.mjs';

const TABLES=['oracle-th11-th12.json','oracle-globals-th11-th12.json','oracle-constants-th11-th12.json'];
const translations=new Map();
// A row is applied only when it is settled, and only when its target is a conceivable address. The
// globals table distinguishes them itself: `ready:true` rows pair a global with its counterpart and
// agree across several reference sites, while a `ready:false` row lists candidates that do not.
//
// Round 311: the row for th11 0x4c3808 was applied with targetAddress 0x00001074 - a VALUE handed to
// the emulator from a twin site that was not an instruction start (the site disassembles as int3
// padding), so the candidate was noise, and eleven suites wrote files[0].original to 0x1074, below the
// guest window, and failed with a memory-bounds error three levels away from the table. A guess is not
// a measurement: unsettled rows and impossible targets are skipped here, and touch() then returns the
// fixture's own constant, which is the documented fixpoint.
const UNSETTLED=new Set(['candidate','withdrawn','unsettled','proposed']);
const TABLES_DIR=resolve(root,'../../../docs/porting');
// Round 314: an address is possible only inside one of the target image's sections. The floor check
// below admits 0x01035c8d, which a legacy ready row claimed for th11 0x4a8d88 and the translator then
// applied, so every suite using that address faulted by construction. The ranges are measured from the
// image by tools/th-image-sections.py, which makes this a fact about th12 rather than a bound picked by
// hand. A missing or unreadable file leaves the ranges null and the floor check alone still applies.
const RANGES=(()=>{
 try{
  const document=JSON.parse(readFileSync(resolve(TABLES_DIR,'oracle-image-sections.json'),'utf8'));
  if(document.title!==target.game)return null;
  return document.rows.map(row=>[BigInt(row.va),BigInt(row.va+row.size)]);
 }catch{return null;}
})();
const skipped=[];
for(const name of TABLES){
 try{
  const document=JSON.parse(readFileSync(resolve(TABLES_DIR,name),'utf8'));
  for(const row of document.rows){
   if(row.target!==target.game)continue;
   const status=String(row.status??row.confidence??row.verdict??'').toLowerCase();
   if(row.ready===false||UNSETTLED.has(status)){skipped.push([name,row.sourceAddress,'unsettled']);continue;}
   if(row.targetAddress){
    const address=BigInt(row.targetAddress);
    if(address<0x10000n){skipped.push([name,row.sourceAddress,'target '+row.targetAddress+' below the guest window']);continue;}
    if(RANGES&&!RANGES.some(range=>address>=range[0]&&address<range[1])){
     skipped.push([name,row.sourceAddress,'target '+row.targetAddress+' is outside the target image sections']);
     continue;
    }
    translations.set(BigInt(row.sourceAddress),address);
   }
   if(row.targetValue)translations.set(BigInt(row.sourceValue),BigInt(row.targetValue));
  }
 }catch{/* a runtime without the table keeps the fixture's own constants */}
}
if(process.env.TH_TOUCH_TRACE&&skipped.length)console.log('touch: skipped %d unsettled or impossible rows, e.g. %o',skipped.length,skipped.slice(0,3));
export function touch(value){
 const found=translations.get(BigInt('0x'+value.toString(16)));
 const result=found===undefined?value:Number(found);
 // A miss is not an error - touch() keeps a fixture's own constant when no row claims it - but a miss
 // immediately before a guest trap is the difference between "the table has no row for this address"
 // and "the row is wrong", and this session needed exactly that distinction more than once.
 // TH_TOUCH_LOG names every miss of a run, in order, so the last one before a trap is visible.
 if(process.env.TH_TOUCH_LOG&&found===undefined)console.error('touch miss 0x%s -> identity',value.toString(16));
 return result;
}
// Structure field offsets of the same title pair, measured with tools/th-twin-fields.py (which
// aligns one function's instruction streams in both images and reports every memory displacement
// that moved). An offset is a plain number, so a fixture can only use it where the number IS
// the offset - `touchField` keeps them out of `touch`'s value space.
const fieldTranslations=new Map();
try{
 const fields=JSON.parse(readFileSync(resolve(root,'../../../docs/porting','oracle-fields-th11-th12.json'),'utf8'));
 for(const row of fields.rows)if(row.target===target.game)
  fieldTranslations.set(BigInt(row.sourceOffset),BigInt(row.targetOffset));
}catch{/* a runtime without the table keeps the fixture's own offsets */}
export function touchField(offset){
 const found=fieldTranslations.get(BigInt('0x'+offset.toString(16)));
 return found===undefined?offset:Number(found);
}
export const translated=translations.size;
export const fieldsTranslated=fieldTranslations.size;
