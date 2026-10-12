"""Execute original x64 helpers in Unicorn; no game process or Steam API runs."""
import hashlib
import importlib
import json
import struct
import sys
import unittest
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_RAX,UC_X86_REG_RSP

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
pkgl=importlib.import_module('th06nc-pkgl')
sections=importlib.import_module('th-disasm').sections


class OriginalPkgl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target=json.loads((ROOT/'runtimes/th06nc/target.json').read_text())
        blob=Path(cls.target['executable']).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=cls.target['sha256']:raise ValueError('TH06nc executable changed')
        cls.machine=Uc(UC_ARCH_X86,UC_MODE_64)
        cls.machine.mem_map(0x140000000,0xd00000)
        for section in sections(blob):
            cls.machine.mem_write(0x140000000+section['va'],blob[section['raw']:section['raw']+section['rawsize']])
        cls.machine.mem_map(0x70000000,0x20000)

    def execute(self,address,data,seed=0):
        machine=self.machine
        machine.mem_write(0x70001000,data+b'\0')
        stack=0x7001f008
        machine.mem_write(stack,struct.pack('<Q',0x70000000))
        machine.reg_write(UC_X86_REG_RSP,stack)
        machine.reg_write(UC_X86_REG_RCX,0x70001000)
        machine.reg_write(UC_X86_REG_RDX,len(data))
        machine.reg_write(UC_X86_REG_R8,seed)
        machine.emu_start(address,0x70000000,count=1000000)
        self.assertEqual(machine.reg_read(UC_X86_REG_RSP),stack+8,'original helper returned')
        return machine.reg_read(UC_X86_REG_RAX),bytes(machine.mem_read(0x70001000,len(data)))

    def test_original_basename_crc(self):
        for name in ('th06MD.dat','data/th06MD.dat',r'H:\Games\th\06nc\data\th06CM.dat','Mixed.Case.dat','file',''):
            with self.subTest(name=name):
                result,_=self.execute(0x140059e20,name.encode())
                self.assertEqual(pkgl.archive_seed(name),result)

    def test_original_xor_for_every_shipped_entry_seed(self):
        data_root=Path(self.target['executable']).parent/'data'
        seeds={0,1,0xffffffff,0x80000000}
        for path in data_root.glob('*.dat'):
            seeds.add(pkgl.archive_seed(path.name))
            seeds.update(row['key'] for row in pkgl.directory(path))
        for seed in sorted(seeds):
            _,native=self.execute(0x140059cb0,bytes(32),seed)
            self.assertEqual(pkgl.decrypt(bytes(32),seed),native,f'seed {seed:#x}')

    def test_original_xor_byte_tails(self):
        for n in (0,1,7,15,16,17,31,255,257):
            data=bytes((i*37+11)&255 for i in range(n))
            _,native=self.execute(0x140059cb0,data,0x87654321)
            self.assertEqual(pkgl.decrypt(data,0x87654321),native)


if __name__=='__main__':unittest.main()
