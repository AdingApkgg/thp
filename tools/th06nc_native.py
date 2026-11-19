"""Shared read-only executable fixture for TH06nc headless native checks."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RBX,UC_X86_REG_RDI,UC_X86_REG_RSI,UC_X86_REG_R14,UC_X86_REG_R15,UC_X86_REG_RBP,UC_X86_REG_RSP
ROOT=Path(__file__).resolve().parents[1]


class Native:
    def __init__(self):
        self.target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes());blob=Path(self.target['executable']).read_bytes();assert hashlib.sha256(blob).hexdigest()==self.target['sha256']
        self.m=Uc(UC_ARCH_X86,UC_MODE_64);self.m.mem_map(0x140000000,0xd00000)
        for s in importlib.import_module('th-disasm').sections(blob):self.m.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
        self.assets,self.manager,self.stack,self.vm,self.owner=0x70000000,0x71000000,0x72000000,0x73000000,0x74000000
        for addr,size in [(self.assets,0x200000),(self.manager,0x40000),(self.stack,0x10000),(self.vm,0x10000),(self.owner,0x20000)]:self.m.mem_map(addr,size)

    def load_title(self,refs):
        m=self.m
        self.assetByFile={};self.ranges=[]
        # Native manager constructor marks all 0x800 unloaded sprite slots -1.
        for i in range(0x800):m.mem_write(self.manager+0x62c+i*64,struct.pack('<i',-1))
        for index,ref in enumerate(refs):
            asset=self.assets+index*0x10000;raw=bytearray((ROOT/'runtimes/th06nc/artifacts/scripts'/ref.get('archive','th06TL.dat')/ref['file']).read_bytes());assert len(raw)<0x10000
            struct.pack_into('<I',raw,8,ref['slot']);m.mem_write(asset,bytes(raw));m.mem_write(self.manager+8+ref['slot']*8,struct.pack('<Q',asset))
            self.assetByFile[ref['file']]=asset;self.ranges.append((asset,asset+len(raw)))
            for reg,value in [(UC_X86_REG_RBX,self.manager),(UC_X86_REG_RDI,asset),(UC_X86_REG_RSI,ref['slot']),(UC_X86_REG_R14,0),(UC_X86_REG_R15,ref['base']),(UC_X86_REG_RBP,self.stack+0x8100),(UC_X86_REG_RSP,self.stack+0x8000)]:m.reg_write(reg,value)
            m.emu_start(0x1400024ae,0x14000270b,count=1000000)
        m.mem_write(0x140a6e9b0,struct.pack('<Q',self.manager))
