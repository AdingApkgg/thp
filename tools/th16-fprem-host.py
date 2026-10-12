"""Run the retail CRT's position-independent FPREM body on the Windows host.

This checks the sign of exact-zero remainders independently of Unicorn's x87
emulation. Only this bounded arithmetic body executes, with finite operands.
"""
import ctypes,hashlib,importlib,json,platform,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    assert platform.system()=='Windows' and ctypes.sizeof(ctypes.c_void_p)==8
    img,_,_=importlib.import_module('th-anm-handlers').handlers(16)
    body=img.read(0x487ad4,14);assert body==bytes.fromhex('d9c9d9f89bdfe09b9e7af7ddd9c3')
    # Save/restore x87 control word in arg4. Initialize, load numerator then
    # denominator, execute the unchanged retail loop, store its result in arg3.
    code=bytes.fromhex('41d939dbe3dd01dd02')+body[:-1]+bytes.fromhex('41dd1841d929c3')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.VirtualAlloc.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_uint32];kernel.VirtualAlloc.restype=ctypes.c_void_p
    kernel.VirtualFree.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32];kernel.VirtualFree.restype=ctypes.c_int
    address=kernel.VirtualAlloc(None,4096,0x3000,0x40);assert address,ctypes.get_last_error()
    try:
        ctypes.memmove(address,code,len(code));ptr=ctypes.POINTER(ctypes.c_double)
        fn=ctypes.CFUNCTYPE(None,ptr,ptr,ptr,ctypes.POINTER(ctypes.c_uint16))(address)
        proof=json.loads((ROOT/'artifacts/th16/anm-math-native.json').read_text());rows=[]
        f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
        for row in proof['cases']:
            if row['op'] not in (111,121):continue
            a=f32(-2.75 if row['refs']&2 else row['a']);b=f32(.125 if row['refs']&4 else row['b'])
            if row['op']==111:a,b=(1.5 if row['refs']&1 else -3),a
            x,y,out,cw=ctypes.c_double(a),ctypes.c_double(b),ctypes.c_double(),ctypes.c_uint16()
            fn(ctypes.byref(x),ctypes.byref(y),ctypes.byref(out),ctypes.byref(cw))
            bits=struct.unpack('<I',struct.pack('<f',out.value))[0]
            index=0 if row['refs']&1 else 8
            oracle=row['words'][4+index] if index==0 else row['words'][index]
            # Every nonzero output must match; the emulated FPREM may lose -0.
            assert bits==oracle or bits==0x80000000 and oracle==0,(row,bits,oracle)
            rows.append(dict(op=row['op'],a=row['a'],b=row['b'],refs=row['refs'],hostBits=bits,unicornBits=oracle))
        result=dict(passed=True,title=16,scope='Original retail CRT FPREM loop copied unchanged (except its final return) into a host x64 ABI wrapper. Finite numerator/denominator operands and first-four-variable references from ANM 111/121 cases. No other retail code, CRT dispatch, animation or gameplay claim.',bodyAddress='0x487ad4',bodyHex=body.hex(),wrapperHex=code.hex(),executableSha256=hashlib.sha256(img.data).hexdigest(),host=platform.machine(),cases=len(rows),unicornNegativeZeroDisagreements=sum(r['hostBits']!=r['unicornBits'] for r in rows),rows=rows,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        (ROOT/'artifacts/th16/fprem-host.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'PASS {len(rows)} original FPREM host cases; {result["unicornNegativeZeroDisagreements"]} Unicorn negative-zero disagreements')
    finally:assert kernel.VirtualFree(address,0,0x8000)
if __name__=='__main__':main()
