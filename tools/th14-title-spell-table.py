"""Extract retail spell selector metadata; originals remain read-only."""
import hashlib,importlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
assert hashlib.sha256(img.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
def read(a,n):return next(img.data[raw+a-b:raw+a-b+n] for _,b,size,raw,count in img.sections if b<=a and a+n<=b+count)
table=[list(struct.unpack('<65i',read(0x4d4d80+s*260,260))) for s in range(7)]
result={'executableSha256':hashlib.sha256(img.data).hexdigest(),'address':'4d4d80','rows':[3,4,4,6,5,6,12],'table':table,'difficulty':list(read(0x4d55a0,120))}
(ROOT/'artifacts/th14/spell-menu-table-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if '--write-header' in sys.argv:
 lines=['#pragma once','#include "Types.hpp"','namespace th11 {','// Retail TH14 4d4d80 (seven 13-row groups); negative ids terminate each row.','inline constexpr i32 th14_spell_counts[]={3,4,4,6,5,6,12};','inline constexpr i32 th14_spell_choices[7][13][5]={']
 for stage in table:lines.append('    {'+','.join('{'+','.join(map(str,stage[r*5:r*5+5]))+'}' for r in range(13))+'},')
 lines+=['};','inline constexpr i32 th14_spell_difficulty(i32 id){return id<26?(id+2)%4:id<108?id%4:4;}','}']
 (ROOT/'runtimes/th12/th12_web/cpp/game/SpellMenuTh14.hpp').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('PASS seven retail spell groups and120 difficulty bytes; header generated' if '--write-header' in sys.argv else 'PASS spell metadata extracted')
