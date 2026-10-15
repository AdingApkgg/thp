"""Declared CPU-only texture API model for the two st02logo ANM chunks.

The success outputs here are model inputs, not measurements of D3D success.
No filtering, pixel upload, physical COM object, or graphics driver is invoked.
All unknown requests stop through the caller. The original ANM helper alone
writes its resource progress and initializes its templates.
"""
import hashlib
import struct
from unicorn import x86_const as XR


class CpuTextures:
    ARENA = 0x63020000
    TRAPS = 0x63030000

    def __init__(self, uc, get, file, raw_pointer, device):
        self.uc, self.get, self.file, self.device = uc, get, file, device
        self.events, self.objects, self.chunks = [], {}, []
        self.surface_to_texture = {}
        self.raw = raw_pointer
        self.table = get(file + 0x124)
        uc.mem_map(self.ARENA, 0x10000, 3)
        uc.mem_map(self.TRAPS, 0x1000, 5)
        uc.mem_write(self.TRAPS, b'\xcc' * 0x1000)
        for index in range(2):
            at = raw_pointer
            assert get(at) == 8 and uc.mem_read(at + 0x20, 1)[0] == 1
            width, height, format = struct.unpack('<HHH', uc.mem_read(at + 10, 6))
            thtx = at + get(at + 0x1c)
            assert bytes(uc.mem_read(thtx, 4)) == b'THTX'
            pixel_format, pw, ph, size = struct.unpack('<HHHI', uc.mem_read(thtx + 6, 10))
            assert format == pixel_format == 5 and size == pw * ph * 2
            half = uc.mem_read(at + 0x22, 1)[0]
            assert half == 1
            chunk = dict(index=index, raw=at, thtx=thtx, source=thtx + 16,
                         sourceBytes=size, sourceWidth=pw, sourceHeight=ph,
                         width=width // 2, height=height // 2, format=26,
                         sourceSha256=hashlib.sha256(bytes(uc.mem_read(thtx + 16, size))).hexdigest(),
                         record=self.table + index * 24)
            self.chunks.append(chunk)
            offset = get(at + 0x24)
            assert (index == 0 and offset) or (index == 1 and not offset)
            raw_pointer += offset
        assert [(c['width'], c['height']) for c in self.chunks] == [(256, 128), (512, 32)]

    def put(self, address, *values):
        self.uc.mem_write(address, struct.pack('<' + 'I' * len(values), *values))

    def returned(self, sp, caller, argc, result):
        self.uc.reg_write(XR.UC_X86_REG_EAX, result)
        self.uc.reg_write(XR.UC_X86_REG_ESP, sp + 4 * (argc + 1))
        self.uc.reg_write(XR.UC_X86_REG_EIP, caller)

    def service(self, address):
        if address not in {0x7b7458ff, 0x7b744f2a, self.TRAPS, self.TRAPS + 0x10, self.TRAPS + 0x20}:
            return False
        sp = self.uc.reg_read(XR.UC_X86_REG_ESP)
        stack = [self.get(sp + 4 * i) for i in range(12)]
        caller = stack[0]
        assert len(self.events) < 24
        if address == 0x7b7458ff:
            device, width, height, levels, usage, format, pool, output = stack[1:9]
            chunk = next(c for c in self.chunks if c['record'] == output)
            assert caller == 0x47cc6e and device == self.device
            assert (width, height, levels, usage, format, pool) == (chunk['width'], chunk['height'], 1, 0, 26, 1)
            assert output not in self.objects
            texture = self.ARENA + 0x1000 + chunk['index'] * 0x100
            surface = texture + 0x80
            vtable = self.ARENA + chunk['index'] * 0x200
            self.put(texture, vtable)
            self.put(surface, vtable + 0x100)
            self.put(vtable + 17 * 4, self.TRAPS)
            self.put(vtable + 18 * 4, self.TRAPS + 0x10)
            self.put(vtable + 2 * 4, self.TRAPS + 0x20)
            self.put(vtable + 0x100 + 2 * 4, self.TRAPS + 0x20)
            self.put(output, texture)
            chunk.update(texture=texture, surface=surface, surfaceReferences=0, textureReferences=1)
            self.objects[texture] = chunk
            self.surface_to_texture[surface] = texture
            event = dict(kind='DECLARED_CPU_CREATE_TEXTURE', chunk=chunk['index'], width=width,
                         height=height, format=format, pool=pool, levels=levels, result=0)
            argc, result = 8, 0
        elif address == self.TRAPS + 0x10:
            texture, level, output = stack[1:4]
            chunk = self.objects[texture]
            assert caller == 0x47cca3 and level == 0 and not chunk['surfaceReferences']
            assert sp <= output < self.ARENA  # original main scratch stack local
            chunk['surfaceReferences'] += 1
            self.put(output, chunk['surface'])
            event = dict(kind='DECLARED_CPU_GET_SURFACE_LEVEL', chunk=chunk['index'], level=0, result=0)
            argc, result = 3, 0
        elif address == self.TRAPS:
            texture, level, output = stack[1:4]
            chunk = self.objects[texture]
            assert caller == 0x47d51b and level == 0
            assert sp <= output < self.ARENA
            desc = [26, 1, 0, 1, 0, 0, chunk['width'], chunk['height']]
            self.put(output, *desc)
            event = dict(kind='DECLARED_CPU_GET_LEVEL_DESC', chunk=chunk['index'], words=desc, result=0)
            argc, result = 3, 0
        elif address == self.TRAPS + 0x20:
            obj = stack[1]
            assert obj in self.surface_to_texture and caller == 0x47cd18
            chunk = self.objects[self.surface_to_texture[obj]]
            assert chunk['surfaceReferences'] == 1
            chunk['surfaceReferences'] = 0
            event = dict(kind='DECLARED_CPU_SURFACE_RELEASE', chunk=chunk['index'], result=0)
            argc, result = 1, 0
        else:
            surface, palette, rect, source, format, pitch, source_palette, source_rect, filter, color_key = stack[1:11]
            assert caller == 0x47ccfe and surface in self.surface_to_texture
            chunk = self.objects[self.surface_to_texture[surface]]
            dest = list(struct.unpack('<4i', self.uc.mem_read(rect, 16)))
            src = list(struct.unpack('<4i', self.uc.mem_read(source_rect, 16)))
            assert (palette, source_palette, color_key) == (0, 0, 0)
            assert format == 26 and pitch == chunk['sourceWidth'] * 2 and source == chunk['source']
            assert src == [0, 0, chunk['sourceWidth'], chunk['sourceHeight']]
            assert dest == [0, 0, chunk['sourceWidth'] // 2, chunk['sourceHeight'] // 2]
            assert filter == 0x30004 and chunk['surfaceReferences'] == 1
            assert hashlib.sha256(bytes(self.uc.mem_read(source, chunk['sourceBytes']))).hexdigest() == chunk['sourceSha256']
            event = dict(kind='DECLARED_CPU_UPLOAD_REQUEST', chunk=chunk['index'], sourceSha256=chunk['sourceSha256'],
                         sourceBytes=chunk['sourceBytes'], sourceRectangle=src, destinationRectangle=dest,
                         pitch=pitch, filter=filter, format=format, result=0,
                         pixelsFiltered=False, pixelsUploaded=False)
            argc, result = 10, 0
        event.update(caller=hex(caller), actualDeviceInvoked=False, resultIsDeclaredModelInput=True)
        self.events.append(event)
        self.returned(sp, caller, argc, result)
        return True
