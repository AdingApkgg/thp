"""Replay %D calendar formatting, actual executable format and UCRT strftime.

Calendar/timezone acquisition is controlled; compares native formatted bytes.
"""
import ctypes,json,struct,hashlib,subprocess
from th06nc_native import Native,ROOT
def main():
 source='shared/th06nc/replay-date.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{formatReplayDate}from'./shared/th06nc/replay-date.mjs';const cases=[];for(const year of [1900,1999,2000,2026,2100,9999])for(const month of [1,2,11,12])for(const day of [1,15,28])cases.push({year,month,day,text:formatReplayDate({year,month,day})});console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();fmt=bytes(n.m.mem_read(0x14030c22c,16)).split(b'\0')[0];assert fmt==b'%D';crt=ctypes.CDLL('ucrtbase');fn=crt.strftime;fn.restype=ctypes.c_size_t;fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p];digest=hashlib.sha256()
 for c in cases:
  tm=(ctypes.c_int*9)(0,0,12,c['day'],c['month']-1,c['year']-1900,0,0,-1);output=ctypes.create_string_buffer(9);length=fn(output,9,fmt,tm);assert length==8 and output.value.decode()==c['text'],(c,length,output.value);digest.update(output.raw)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-date-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
