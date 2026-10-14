"""Read frozen retail surfaces/draw registrations and execute bounded callers.

No native child, production edit, fake GPU service or loader duration is used.
This follow-up preserves every prior report and distinguishes immediate Pause
capture from deferred end-menu capture and their source/destination rectangles.
"""
import gzip
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'tools/th14-loading-lifecycle-evidence-check.py'
SNAPSHOT=ROOT/'artifacts/th14/native-zps-reimua-lunatic-full-oct14'
OUTPUT=ROOT/'docs/porting/th14-staged-loader-host-boundary-verified-oct14.json'
SUP, MANAGER, STACK, RETURN=0x4d8f60,0x2000000,0x7ff000,0x710000
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    spec=importlib.util.spec_from_file_location('host_boundary_image',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    image=helper.Image();md=Cs(CS_ARCH_X86,CS_MODE_32)
    manifest_path=SNAPSHOT/'manifest.json';manifest=json.loads(manifest_path.read_text())
    assert manifest['executableSha256']==helper.EXPECTED_EXE_SHA
    assert SHA(SNAPSHOT/'memory.bin.gz')==manifest['memorySha256']
    assert SHA(SNAPSHOT/'context.bin')==manifest['contextSha256']
    memory={};consumed=0
    with gzip.open(SNAPSHOT/'memory.bin.gz','rb') as stream:
        for region in manifest['regions']:
            assert consumed==region['offset']
            data=stream.read(region['bytes'])
            assert len(data)==region['bytes'] and hashlib.sha256(data).hexdigest()==region['sha256']
            memory[region['base']]=data;consumed+=len(data)
        assert consumed==manifest['uncompressedBytes'] and not stream.read(1)
    def read(address,count):
        region=next(r for r in manifest['regions'] if r['base']<=address and address+count<=r['base']+r['bytes'])
        at=address-region['base'];return memory[region['base']][at:at+count]
    get=lambda address:struct.unpack('<I',read(address,4))[0]
    def string(address):
        out=bytearray()
        for index in range(256):
            value=read(address+index,1)[0]
            if not value:return out.decode('ascii',errors='replace')
            out.append(value)
        raise AssertionError('bounded string')
    modules=[]
    for base in sorted({r['allocation'] for r in manifest['regions'] if r['kind']==0x1000000}):
        if read(base,2)!=b'MZ':continue
        pe=base+get(base+0x3c);magic=struct.unpack('<H',read(pe+0x18,2))[0]
        assert magic in (0x10b,0x20b)
        export=get(pe+(0x78 if magic==0x10b else 0x88))
        name=string(base+get(base+export+12)) if export else ('th14.exe' if base==0x400000 else 'unnamed')
        modules.append(dict(base=base,bytes=get(pe+0x50),name=name))
    device=get(SUP+8);device_table=get(device);get_backbuffer=get(device_table+0x48)
    method_module=next(m for m in modules if m['base']<=get_backbuffer<m['base']+m['bytes'])
    assert method_module['name'].lower()=='d3d9.dll'
    surfaces=[get(SUP+x) for x in (0x1ac,0x1b0,0x1b4)]
    assert all(surfaces) and len(set(surfaces))==3
    resource=get(SUP+0x71c);textures=get(resource+0x124)
    captured_manager=get(0x4f56cc)
    queue=struct.unpack('<4i',b''.join(read(captured_manager+x,4) for x in (0x20,0x48,0x70,0x98)))
    callback_manager=get(0x4db51c);node=get(callback_manager+0x40);seen=set();draw=[]
    while node:
        assert node not in seen and len(seen)<256;seen.add(node)
        callback=get(node)
        draw.append(dict(priority=get(callback),flags=get(callback+4),function=hex(get(callback+8)),owner=hex(get(callback+0x24))))
        node=get(node+4)
    assert [r['priority'] for r in draw]==sorted(r['priority'] for r in draw)
    compositor_path=ROOT/'artifacts/th14/compositor-native.json'
    compositor=json.loads(compositor_path.read_text())
    for row in compositor['callbacks']:
        assert any(d['priority']==row['priority'] and d['function']==row['entry'] and d['owner']==hex(SUP) for d in draw),row
    backbuffer_calls=[e for row in compositor['callbacks'] for e in row['events'] if e['kind']=='target' and e['target']==99]
    assert backbuffer_calls
    frozen=dict(snapshot=SNAPSHOT.relative_to(ROOT).as_posix(),manifestSha256=SHA(manifest_path),
                memorySha256=manifest['memorySha256'],contextSha256=manifest['contextSha256'],
                bytesVerified=consumed,regionsVerified=len(manifest['regions']),
                supervisor=hex(SUP),device=hex(device),getBackBufferMethod=hex(get_backbuffer),methodModule=method_module['name'],
                textResource=hex(resource),texture2=hex(get(textures+2*24)),texture3=hex(get(textures+3*24)),
                surfaces=dict(textTexture2At1ac=hex(surfaces[0]),textTexture3At1b0=hex(surfaces[1]),backbufferAt1b4=hex(surfaces[2])),
                threeSurfaceHandlesDistinct=True,firstPlayerBoundaryQueue=list(queue),registeredDrawCallbacks=draw,
                existingCompositorTraceSha256=SHA(compositor_path),
                scope='Immutable first-Player-boundary memory/context only; no ordinary subsequent transition queue timeline or rendered pixels observed.')
    del memory

    def machine():
        uc=image.machine();uc.mem_map(MANAGER,0x1000000)
        helper.word(uc,0x4f56cc,MANAGER)
        for offset in (0x20,0x48,0x70,0x98):helper.word(uc,MANAGER+offset,0xffffffff)
        uc.mem_write(0x4db510,struct.pack('<HHI',49408,0,66446))
        return uc
    def run(uc,entry,stop,registers=None,allowed_calls=()):
        helper.word(uc,STACK,RETURN);uc.reg_write(UC_X86_REG_ESP,STACK)
        for register,value in (registers or {}).items():uc.reg_write(register,value)
        uc.reg_write(UC_X86_REG_MXCSR,0x1f80)
        calls=[]
        def check(guest,address,size,user):
            if address==stop:guest.emu_stop();return
            ins=next(md.disasm(bytes(guest.mem_read(address,size)),address,count=1))
            if ins.mnemonic=='call':
                assert address in allowed_calls,(hex(address),ins.op_str)
                calls.append(hex(address))
        hook=uc.hook_add(UC_HOOK_CODE,check)
        uc.emu_start(entry,RETURN,count=4000);uc.hook_del(hook)
        assert uc.reg_read(UC_X86_REG_EIP)==stop,hex(uc.reg_read(UC_X86_REG_EIP))
        return dict(entry=hex(entry),stop=hex(stop),originalCallsExecuted=calls,hostCallsExecuted=0)
    uc=machine()
    helper.word(uc,SUP+8,0x640000);helper.word(uc,0x640000,0x650000)
    source_init=run(uc,0x4474e0,0x447513,{UC_X86_REG_ECX:SUP})
    sp=uc.reg_read(UC_X86_REG_ESP)
    assert list(struct.unpack('<5I',uc.mem_read(sp,20)))==[0x640000,0,0,0,SUP+0x1b4]
    source_init.update(boundary='IDirect3DDevice9.GetBackBuffer',arguments=[hex(0x640000),0,0,0,hex(SUP+0x1b4)],outputSupervisorOffset='0x1b4')
    helper.word(uc,SUP+0x71c,0x620000);helper.word(uc,0x620124,0x630000)
    for offset,handle in ((0x30,0x640100),(0x48,0x640200)):
        helper.word(uc,0x630000+offset,handle);helper.word(uc,handle,0x650000)
    target_inits=[]
    for entry,stop,out,texture_index,handle in ((0x447516,0x44752b,0x1ac,2,0x640100),(0x44752e,0x447549,0x1b0,3,0x640200)):
        row=run(uc,entry,stop,{UC_X86_REG_EDI:SUP,UC_X86_REG_ESI:SUP+0x1ac})
        sp=uc.reg_read(UC_X86_REG_ESP)
        assert list(struct.unpack('<3I',uc.mem_read(sp,12)))==[handle,0,SUP+out]
        row.update(textureIndex=texture_index,outputSupervisorOffset=hex(out),arguments=[hex(handle),0,hex(SUP+out)],boundary='IDirect3DTexture9.GetSurfaceLevel')
        target_inits.append(row)
    immediate=[]
    for dialogue in (0,1):
        for scale in (1.0,1.5,2.0):
            uc=machine();vm,sprite,file,gui=0x610000,0x620000,0x630000,0x600000
            for address,value in ((vm+0x2c,sprite),(vm+0x30,file),(file,0),(sprite+4,1),
                                  (0x4db550,gui),(gui+0x194,dialogue),(0x4d9110,0x640010),(0x4d9114,0x640014),
                                  (0x4f7a80,int(320*scale)),(0x4f7a84,int(16*scale))):helper.word(uc,address,value)
            # Distinct dimensions make source/destination argument order observable.
            for offset,value in ((0xc,3.0),(0x10,5.0),(0x34,128.0),(0x38,256.0)):
                uc.mem_write(sprite+offset,struct.pack('<f',value))
            uc.mem_write(0x4f7a6c,struct.pack('<f',scale))
            row=run(uc,0x448c3a,0x448d6a,{UC_X86_REG_EDX:vm})
            sp=uc.reg_read(UC_X86_REG_ESP)
            file_slot,texture_slot,surface,dest,source=struct.unpack('<5I',uc.mem_read(sp,20))
            source_rect=list(struct.unpack('<4i',uc.mem_read(source,16)));dest_rect=list(struct.unpack('<4i',uc.mem_read(dest,16)))
            assert dest_rect==[3,5,259,133]
            expected=[int((128 if dialogue else 32)*scale),int(16*scale),int((512 if dialogue else 416)*scale),int(464*scale)]
            assert source_rect==expected,(dialogue,scale,source_rect,expected)
            assert surface==(0x640010 if dialogue else 0x640014)
            assert list(struct.unpack('<4i',b''.join(uc.mem_read(MANAGER+x,4) for x in (0x20,0x48,0x70,0x98))))==[-1]*4
            row.update(dialoguePointerNonzero=bool(dialogue),declaredScale=scale,fileSlot=file_slot,textureSlot=texture_slot,
                       sourceSurface='textTexture3At1b0' if dialogue else 'backbufferAt1b4',sourceRectangle=source_rect,
                       destinationRectangle=dest_rect,queueUnchanged=True,immediateCopyCallNotExecuted=True)
            immediate.append(row)
    transitions=[]
    for current_stage in range(1,6):
        uc=machine();row=run(uc,0x43726e,0x437296,{UC_X86_REG_EDX:current_stage})
        assert struct.unpack('<I',uc.mem_read(0x4d964c,4))[0]==12
        assert struct.unpack('<I',uc.mem_read(0x4f58a4,4))[0]==current_stage+1
        assert list(struct.unpack('<4i',b''.join(uc.mem_read(MANAGER+x,4) for x in (0x20,0x48,0x70,0x98))))==[-1]*4
        row.update(priorStage=current_stage,nextStage=current_stage+1,requestedScene=12,copyQueueUnchanged=True)
        transitions.append(row)
    # Follow the real next-stage worker call through complete Replay init, then
    # stop before its HUD call. GPU/Stage/ECL/clock functions are never simulated.
    uc=machine();replay,header,gui=0x620000,0x630000,0x600000
    for address,value in ((0x4db688,replay),(replay+0x10,1),(replay+0x128,header),(0x4f58a4,2),(0x4db550,gui)):
        helper.word(uc,address,value)
    uc.mem_write(header+2,struct.pack('<H',49408))
    uc.mem_write(header+0x14,struct.pack('<28I',*range(100,128)))
    writes=[]
    def rng_write(guest,access,address,size,value,user):
        if address in (0x4db510,0x4db508,0x4db514):writes.append(dict(instruction=hex(guest.reg_read(UC_X86_REG_EIP)),address=hex(address),value=value,bytes=size))
    uc.hook_add(UC_HOOK_MEM_WRITE,rng_write)
    initialization=run(uc,0x435f32,0x435f3d,allowed_calls=(0x435f32,))
    assert [r['instruction'] for r in writes]==['0x45610f','0x456123','0x456129']
    assert uc.reg_read(UC_X86_REG_ECX)==gui
    initialization.update(seedWrites=writes,nextBoundary='42eb30 HUD stage refresh',enemyOwnerNotYetPublished=True)
    text_section=image.sections[0];base=image.base+text_section['rva'];code=image.bytes(base,text_section['rawSize'])
    direct_calls={hex(target):[] for target in (0x44bdd0,0x44be40,0x47e070,0x4690d0)}
    for offset in range(len(code)-4):
        if code[offset]!=0xe8:continue
        target=base+offset+5+struct.unpack_from('<i',code,offset+1)[0]
        if hex(target) in direct_calls:direct_calls[hex(target)].append(hex(base+offset))
    assert direct_calls['0x44bdd0']==['0x44be96']
    assert direct_calls['0x44be40']==['0x44a080','0x44b220']
    assert direct_calls['0x47e070']==['0x448d6a']
    assert direct_calls['0x4690d0']==['0x46ab87']
    pointers={hex(target):[] for target in (0x44bdd0,0x44be40)}
    for target in (0x44bdd0,0x44be40):
        needle=struct.pack('<I',target);at=0
        while (at:=image.data.find(needle,at))!=-1:
            pointers[hex(target)].append(at);at+=1
    assert not any(pointers.values())
    addresses=[0x447513,0x447525,0x44752b,0x44753a,0x44753d,0x447549,
               0x448c86,0x448c8b,0x448c92,0x448cfa,0x448d59,0x448d6a,
               0x44a017,0x44a01e,0x44a02d,0x44a080,0x44b1b6,0x44b1cd,0x44b220,
               0x435ba4,0x435bab,0x435ed0,0x435ed7,0x435f32,0x435f3d,0x435f4b,0x435f66,
               0x4228de,0x4228e4,0x4228fa,0x469182,0x469188,0x46918e,0x46919d]
    instructions=[]
    for address in addresses:
        i=next(md.disasm(image.bytes(address,15),address,count=1))
        instructions.append(dict(address=hex(address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str))
    engine_path=ROOT/'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json';engine=json.loads(engine_path.read_text())
    assert len(engine['sourceHashes'])==265
    for name,digest in engine['sourceHashes'].items():assert SHA(ROOT/'runtimes/th12/th12_web'/name)==digest,name
    host_sources=['cpp/sdl/Application.cpp','cpp/sdl/GraphicsDevice.cpp','cpp/sdl/GraphicsDevice.hpp']
    queue_report=ROOT/'docs/porting/th14-staged-loader-capture-queue-verified-oct14.json'
    result=dict(diagnosticOnly=True,hostBoundaryEvidencePassed=True,completeGame=False,nativeEquivalent=False,productionChanged=False,
                actualRetailProcessesStarted=0,frozenSnapshot=frozen,surfaceAcquisitionPrefixes=[source_init,*target_inits],
                immediatePauseSourceCases=immediate,nextStageRequestPrefixes=transitions,realWorkerReplayInitializationPrefix=initialization,
                exactTextDirectCallSites=direct_calls,absoluteFunctionPointerOccurrences=pointers,originalInstructions=instructions,
                captureRoutes=dict(immediatePause='448bf0 -> 47e070, during Pause entry before subsequent draw; dialogue pointer at global4db550+194 chooses textTexture3, otherwise backbuffer.',
                                   deferredEnd='449f20 end-entry normal branch or80-frame end-menu branch ->44be40->44bdd0, then4690d0 after completed draw; always source backbuffer.'),
                sourceObjectCorrespondence='Native Supervisor+1b4 comes from Device.GetBackBuffer, distinct from+1ac texture2 and+1b0 texture3 surfaces. GraphicsDevice::screen is the backend presentation target selected for a null ANM resource and matches the backbuffer role. Texture3 route instead requires graphics.texture(core.text,3).',
                currentPortAssessment='Single PauseMenu.capture_requested is always consumed before session.draw from GraphicsDevice::screen. This matches the normal no-dialogue Pause source role and relative update/draw order, not the dialogue Pause source or deferred-end capture order; no pixel/complete-Pause equivalence claimed.',
                ordinaryNextStageAssessment='The actual43726e request12/next-stage prefix does not enqueue capture, and all direct stock enqueue call sites are two end-menu paths. Ordinary NextStage should not manufacture a capture job; it checks the existing first slot then requests60ms because Supervisor12 clears initialStageFlag. No complete dynamic NextStage capture-queue timeline was recorded.',
                workerOrder='After guard/Sleep60, loading ANM update46fe50 occurs before456050. The next-stage worker branch initializes Replay/live stage header at435f32, refreshes HUD42eb30 at435f3d, loads incoming STD/background through40d8a0 at435f4b, then constructs EnemyManager at435f66. Constructor publishesowner/nextId1 before422340 ECL load.',
                priorQueueReportSha256=SHA(queue_report),
                priorReportFieldLabelCorrection='Prior capture-queue report recordFields reverses source/target rectangle names: words2..5 are SOURCE x/y/width/height; words6..9 are DESTINATION x/y/width/height. 469182 pushes source RECT as D3DX argument6,46918e pushes destination RECT as argument3. Its byte-level enqueue/retirement/wait results remain unchanged; prior report is preserved.',
                hostOrGameCallShims=0,sourceFilesVerified=265,sourceHashes=engine['sourceHashes'],hostSourceHashes={p:SHA(ROOT/'runtimes/th12/th12_web'/p) for p in host_sources},
                verifierSha256=SHA(Path(__file__)),executableSha256=helper.EXPECTED_EXE_SHA,
                scope='Read-only complete frozen snapshot integrity, actual registered draw nodes/surface pointers, bounded original surface-acquisition and immediate-Pause descriptor/request12 prefixes, and actual worker call through complete456050. No GPU/API call is executed or simulated; only original435f32->456050 executes a call. Direct-xref enumeration is static evidence, not every possible dynamic execution. No native child, fabricated timing, framebuffer/audio or whole-game proof.')
    OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(hostBoundaryEvidencePassed=True,snapshotBytes=consumed,drawCallbacks=len(draw),pauseSourceCases=len(immediate),nextStagePrefixes=len(transitions),sourceFilesVerified=265,hostCalls=0)))


if __name__=='__main__':main()
