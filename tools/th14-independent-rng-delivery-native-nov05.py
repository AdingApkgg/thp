"""Replay independently generated synthetic RNG calls through retail x86 code.

Only the main arithmetic body/packing and worker script-seed store execute.
Critical-section entry, Windows scheduling and the whole Application are not
accepted. No original process is started and no original observation is edited.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_ESI,UC_X86_REG_EIP,UC_X86_REG_ESP
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();source=a.input.resolve(strict=True);out=a.output.resolve()
    assert source.is_relative_to(R/'artifacts/th14') and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True)
    raw=source.read_bytes();observed=json.loads(raw)
    assert observed['passed'] and observed['syntheticInputsOnly'] and not observed['producerSuppliesRngWords']
    sys.path.insert(0,str(R/'tools'))
    image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert image.read(0x456123,6).hex()=='66a308b54d00'
    assert image.read(0x403336,3).hex()=='663306'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,start,length in image.sections:
        low=address&~4095;m.mem_map(low,((address+size+4095)&~4095)-low)
        m.mem_write(address,image.data[start:start+length])
    stack=0x70000000;m.mem_map(stack,0x2000);seed_address=0x4db508
    # The C++ production boundary names correspond to these original PCs.
    points={0:0x403336,1:0x403339,2:0x40333d,3:0x403373,4:0x403376}

    def run(seed,calls,entry,boundary):
        m.mem_write(seed_address,struct.pack('<HHI',seed,0xbeef,calls))
        m.mem_write(0x4f5815,b'\0')
        m.mem_write(stack+0x1000,struct.pack('<4I',0,0,0,stack))
        m.reg_write(UC_X86_REG_ESP,stack+0x1000);m.reg_write(UC_X86_REG_ESI,seed_address)
        pc=0x40332f;applied=False;retained=None
        for _ in range(100):
            if boundary is not None and pc==points[boundary] and not applied:
                own=m.context_save();m.reg_write(UC_X86_REG_EAX,entry)
                m.emu_start(0x456123,0x456129,count=1)
                assert m.reg_read(UC_X86_REG_EIP)==0x456129
                assert struct.unpack('<H',m.mem_read(seed_address,2))[0]==entry
                m.context_restore(own);applied=True
            m.emu_start(pc,stack,count=1)
            if pc==0x403336:retained=(m.reg_read(UC_X86_REG_EAX)&0xffff)^0x9630
            pc=m.reg_read(UC_X86_REG_EIP)
            if pc==stack:break
        else:raise AssertionError('Retail body did not return')
        assert applied==(boundary is not None) and retained is not None
        seed,_,calls=struct.unpack('<HHI',m.mem_read(seed_address,8))
        return m.reg_read(UC_X86_REG_EAX),seed,calls,retained

    rows=[];negative=[];worker_cases=0
    for case in observed['cases']:
        value=case['yielded'] if case['name']=='same-thread-timer' else case['observed']
        # Wasm i32 exports arrive as signed JS numbers in the retained first
        # driver. Interpret their bits as u32; never change the captured file.
        value['commitRows']=[[word&0xffffffff for word in row]for row in value['commitRows']]
        groups={}
        for row in value['commitRows']:
            assert len(row)==16 and row[14]==1
            groups.setdefault(row[2],[]).append(row)
        for iteration,group in sorted(groups.items()):
            first=group[0]
            assert all(row[9:16]==first[9:16] for row in group)
            scripts=[row for row in group if row[0]==1];assert len(scripts)<=1
            boundary=scripts[0][1]if scripts else None
            expected=(first[9],first[10],first[11],first[15])
            actual=run(first[12],first[13],value['entry'],boundary)
            if actual!=expected:
                (out/'failure.json').write_text(json.dumps(dict(case=case['name'],iteration=iteration,
                    boundary=boundary,actual=actual,expected=expected,inputRow=first,
                    syntheticInputsOnly=True),indent=2)+'\n')
                raise AssertionError((case['name'],iteration,boundary))
            if case['name'].startswith('worker-'):worker_cases+=1
            rows.append(dict(case=case['name'],iteration=iteration,scriptStoreBoundary=boundary,
                originalPackedReturnSeedCallsAndRetainedInputEqual=True))
            if scripts:
                wrong=1 if boundary==0 else 0
                bad=run(first[12],first[13],value['entry'],wrong)
                different=bad!=expected
                negative.append(dict(case=case['name'],iteration=iteration,originalBoundary=boundary,
                    alteredBoundary=wrong,rejected=different))
    assert rows and worker_cases>=3 and any(row['rejected']for row in negative)
    result=dict(schema='th14/independent-rng-retail-component/1',passed=True,
        actualRetailMainArithmeticAndReturnPacking=True,actualRetailScriptSeedStore=True,
        capturedSyntheticCalls=len(rows),capturedWorkerCalls=worker_cases,
        comparedWordsPerCall=4,allCapturedCallsEqual=True,
        negativeControls=len(negative),negativeRejected=sum(row['rejected']for row in negative),
        rows=rows,negative=negative,inputPath=source.relative_to(R).as_posix(),inputSha256=SHA(raw),
        executableSha256=SHA(image.data),mainBodySha256=SHA(image.read(0x40332f,0x40339b-0x40332f)),
        syntheticInputsOnly=True,controlledCriticalSectionBypassInEmulator=True,
        originalWindowsProcessRun=False,originalSchedulingEquivalent=False,
        ordinaryApplicationIntegrated=False,wholeReplayCompared=False,completeGame=False,
        toolSha256=SHA(Path(__file__).read_bytes()))
    (out/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['passed','capturedSyntheticCalls','capturedWorkerCalls','negativeControls','negativeRejected','ordinaryApplicationIntegrated','completeGame']}))


if __name__=='__main__':main()
