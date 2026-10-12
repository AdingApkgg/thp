import importlib,sys
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
img,_,_=importlib.import_module('th-anm-handlers').handlers(16)
d=Cs(CS_ARCH_X86,CS_MODE_32)
for a,b in ((0x402ff0,0x403390),(0x41bb50,0x41c390),(0x4171c0,0x4174b0)):
 print('\nRANGE',hex(a),hex(b))
 for i in d.disasm(img.read(a,b-a),a):print(f'{i.address:08x} {i.mnemonic} {i.op_str}')
for op in (400,401,402,403,404,405,406,407,408,409,410,411,416,417,420,422,424,425,426,427,428,429,430,431,440,441,442,443,444,445,446,447):
 group=img.read(0x422d70+op-300,1)[0];a=img.u32(0x422ab8+4*group)
 print('OP',op,hex(a))
