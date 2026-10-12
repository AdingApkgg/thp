"""Executable-backed regressions for the ANM/ECL dispatch mix-up."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
handlers=importlib.import_module('th-opcode-handlers')
audit=importlib.import_module('th-opcode-body-audit')
anm=importlib.import_module('th-anm-handlers')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


class DispatchTests(unittest.TestCase):
    def test_each_ecl_table_reads_the_ecl_opcode_field(self):
        for name,row in handlers.TITLES.items():
            with self.subTest(title=name):
                failures,_=handlers.check(name,row,verbose=False)
                self.assertEqual([],failures)
                image=handlers.Image(row['exe'])
                dis=Cs(CS_ARCH_X86,CS_MODE_32)
                instruction=next(dis.disasm(image.read(row['opcodeLoad'],4),row['opcodeLoad']))
                self.assertEqual('movzx',instruction.mnemonic)
                self.assertIn('word ptr',instruction.op_str)
                self.assertTrue(instruction.op_str.endswith('+ 4]'))

    def test_old_th13_table_is_anm_not_ecl(self):
        image,table,default=anm.handlers(13)
        self.assertEqual(0x464b46,table[438])
        self.assertNotEqual(table[1],table[2])
        self.assertEqual(default,table[0])
        self.assertNotEqual(0x465af8,handlers.TITLES['th13']['jump'])
        wrong=dict(handlers.TITLES['th13'],jump=0x465af8,group=0x465bec,
                   first=301,bound=207,targets=61)
        failures,_=handlers.check('th13',wrong,verbose=False)
        self.assertIn('opcode load is not connected to the recorded indirect dispatch',failures)

    def test_original_th13_1003_actually_writes_enemy_flags(self):
        # Execute the original handler up to its epilogue. Its helper's result is
        # an explicit input; this is not an emulation of that helper or full ECL.
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
        from unicorn.x86_const import UC_X86_REG_EDI, UC_X86_REG_EAX, UC_X86_REG_ECX
        image=handlers.Image(handlers.TITLES['th13']['exe'])
        for initial in (0,2,0xa5a5a5a5,0xffffffff):
            for helper_result in (0,1,2,0xffffffff):
                with self.subTest(initial=initial,result=helper_result):
                    machine=Uc(UC_ARCH_X86,UC_MODE_32)
                    machine.mem_map(0x410000,0x10000)
                    machine.mem_write(0x41f71d,image.read(0x41f71d,0x1b))
                    machine.mem_map(0x1000000,0x5000)
                    machine.mem_write(0x1004034,initial.to_bytes(4,'little'))
                    machine.reg_write(UC_X86_REG_EDI,0x1000000)
                    machine.reg_write(UC_X86_REG_ECX,0xdeadbeef)
                    machine.emu_start(0x41f71d,0x41f721,count=10)
                    self.assertEqual(0,machine.reg_read(UC_X86_REG_ECX))
                    self.assertEqual(0x1000000,machine.reg_read(UC_X86_REG_EAX))
                    machine.reg_write(UC_X86_REG_EAX,helper_result)
                    machine.emu_start(0x41f726,0x41f738,count=10)
                    actual=int.from_bytes(machine.mem_read(0x1004034,4),'little')
                    self.assertEqual((initial & ~2) | ((helper_result << 1) & 2),actual)

    def test_real_enemy_write_is_not_an_epilogue(self):
        row=handlers.TITLES['th13']
        image=handlers.Image(row['exe'])
        mapping={op:address for op,_,address in handlers.build_map(image,row,handlers.build_targets(image,row))}
        self.assertEqual(0x41f71d,mapping[1003])
        base,sections=audit.sections(image.data)
        md=Cs(CS_ARCH_X86,CS_MODE_32)
        self.assertFalse(audit.is_noop(image.data,base,sections,mapping[1003],md))
        self.assertTrue(audit.is_noop(image.data,base,sections,0x41f738,md))
        self.assertNotEqual(0x41f738,mapping[525])
        self.assertNotEqual(0x41f738,mapping[700])

    def test_classifier_rejects_other_memory_writes_and_calls(self):
        for code in ['33c0310fc3','33c0e800000000c3','33c0b801000000c3','33c058c3','c3']:
            data=bytes.fromhex(code)+b'\xcc'*100
            self.assertFalse(audit.is_noop(data,0x400000,[(0,0,len(data))],0x400000,Cs(CS_ARCH_X86,CS_MODE_32)),code)
        data=bytes.fromhex('33c0c3')+b'\xcc'*100
        self.assertTrue(audit.is_noop(data,0x400000,[(0,0,len(data))],0x400000,Cs(CS_ARCH_X86,CS_MODE_32)))


if __name__=='__main__':
    unittest.main()
