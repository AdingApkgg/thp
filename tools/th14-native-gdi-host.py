"""Real local GDI for original TH14 glyph code; atlas upload is a logical boundary.

Only our own DC/bitmap/fonts are used. Captured process handles are opaque keys,
never passed to host GDI. The original scratch processing continues executing.
"""
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP


def install(m,root,log):
    source_bytes = Path(__file__).read_bytes()
    get = lambda p: struct.unpack('<I',m.mem_read(p,4))[0]
    put = lambda p,v: m.mem_write(p,struct.pack('<I',v & 0xffffffff))
    width,height,size = [get(p) for p in (0x4d9aec,0x4d9af0,0x4d9af4)]
    assert (width,height,size,get(0x4d9ae8)) == (1024,128,262144,26)
    pixels,guest_dc = get(0x4d9b08),get(0x4d9afc)
    gdi = C.WinDLL('gdi32',use_last_error=True)
    def function(name,result,args):
        value = getattr(gdi,name);value.restype = result;value.argtypes = args;return value
    ptr,integer,u32 = C.c_void_p,C.c_int,C.c_uint32
    create_dc = function('CreateCompatibleDC',ptr,[ptr])
    create_dib = function('CreateDIBSection',ptr,[ptr,ptr,u32,C.POINTER(ptr),ptr,u32])
    select = function('SelectObject',ptr,[ptr,ptr])
    create_font = function('CreateFontA',ptr,[integer]*5+[u32]*8+[C.c_char_p])
    text_color = function('SetTextColor',u32,[ptr,u32])
    background = function('SetBkMode',integer,[ptr,integer])
    text_out = function('TextOutA',integer,[ptr,integer,integer,C.c_char_p,integer])
    flush = function('GdiFlush',integer,[])
    delete_object = function('DeleteObject',integer,[ptr])
    delete_dc = function('DeleteDC',integer,[ptr])
    info = bytearray(108)
    struct.pack_into('<IiiHHII',info,0,108,width,-height,1,16,3,size)
    struct.pack_into('<IIII',info,40,0xf00,0xf0,0xf,0xf000)
    info_buffer,bits = C.create_string_buffer(bytes(info)),ptr()
    bitmap = create_dib(None,info_buffer,0,C.byref(bits),None,0)
    dc = create_dc(None)
    if not bitmap or not dc or not bits.value:raise C.WinError(C.get_last_error())
    old_bitmap = select(dc,bitmap)
    font_path = root/'artifacts/th14/font-initialization-native.json'
    font_bytes = font_path.read_bytes()
    descriptors = json.loads(font_bytes)['rows'][0]['fonts']
    fonts = [create_font(*row['args'],bytes.fromhex(row['face'])) for row in descriptors]
    if not all(fonts):raise C.WinError(C.get_last_error())
    handles = [get(address) for address in (0x4fd61c,0x4fd62c,0x4fd620,0x4fd630,0x4fd624,0x4fd628,0x4fd634,0x4fd638)]
    if len(set(handles)) != 8 or not all(handles):raise ValueError('Captured font handles not distinct.')
    font_map = dict(zip(handles,fonts))
    old_font = select(dc,fonts[0])
    selected = handles[0]
    textures,surfaces,uploads = set(),{},[]
    screen_sources,screen_copies = set(),[]
    arena = 0x41000000
    m.mem_map(arena,0x10000)
    release_address,table = arena,arena+0x100
    put(table+8,release_address)
    def ret(result,argc):
        sp = m.reg_read(UC_X86_REG_ESP)
        m.reg_write(UC_X86_REG_EAX,result & 0xffffffff)
        m.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
        m.reg_write(UC_X86_REG_EIP,get(sp))
    def observe(uc,address,length,user):
        sp = uc.reg_read(UC_X86_REG_ESP)
        texture = get(sp+20)
        textures.add(texture)
        log.append(dict(name='TH14.originalGlyphRasterEntry',texture=hex(texture),font=get(sp+24),height=get(sp+4)))
    m.hook_add(UC_HOOK_CODE,observe,begin=0x467ba0,end=0x467ba0)
    def observe_screen_copy(uc,address,length,user):
        source = get(uc.reg_read(UC_X86_REG_ESP)+12)
        if source:
            if not get(source) or not get(get(source)+8):raise ValueError('Original screen-copy source has no COM surface table.')
            screen_sources.add(source)
    m.hook_add(UC_HOOK_CODE,observe_screen_copy,begin=0x47e070,end=0x47e070)
    def observe_screen_texture(uc,address,length,user):
        texture = uc.reg_read(UC_X86_REG_EAX)
        if not texture or not get(texture):raise ValueError('Invalid texture at original screen-copy GetSurfaceLevel call.')
        textures.add(texture)
    m.hook_add(UC_HOOK_CODE,observe_screen_texture,begin=0x47e0b7,end=0x47e0b7)
    def release(uc,address,length,user):
        surface = get(uc.reg_read(UC_X86_REG_ESP)+4)
        if surface not in surfaces:raise ValueError('Unknown logical atlas surface release.')
        del surfaces[surface]
        log.append(dict(name='IDirect3DSurface9.Release',surface=hex(surface),logical=True))
        ret(0,1)
    m.hook_add(UC_HOOK_CODE,release,begin=release_address,end=release_address)
    def upload(uc,address,length,user):
        sp = uc.reg_read(UC_X86_REG_ESP)
        arguments = [get(sp+4+index*4) for index in range(10)]
        if arguments[0] not in surfaces or arguments[1] or arguments[6]:raise ValueError('Unknown glyph upload surface/palette.')
        source_rect = struct.unpack('<4i',uc.mem_read(arguments[7],16))
        left,top,right,bottom = source_rect
        if not 0 <= left <= right <= 4096 or not 0 <= top <= bottom <= 4096 or arguments[4] not in (21,26):raise ValueError('Invalid glyph source rectangle/format.')
        amount = arguments[5]*bottom
        if amount > 0x1000000:raise ValueError('Unbounded glyph upload.')
        digest = hashlib.sha256(bytes(uc.mem_read(arguments[3],amount))).hexdigest()
        record = dict(name='D3DXLoadSurfaceFromMemory.glyph',texture=hex(surfaces[arguments[0]]),sourceRect=list(source_rect),
                      format=arguments[4],pitch=arguments[5],sourceSha256=digest,logicalUpload=True)
        uploads.append(record);log.append(record);ret(0,10)
    upload_address = get(0x4b12e0)
    m.hook_add(UC_HOOK_CODE,upload,begin=upload_address,end=upload_address)
    def copy_surface(uc,address,length,user):
        sp = uc.reg_read(UC_X86_REG_ESP)
        arguments = [get(sp+4+index*4) for index in range(8)]
        if arguments[0] not in surfaces or arguments[3] not in screen_sources or arguments[1] or arguments[4] or arguments[6:] != [2,0]:
            raise ValueError('Unobserved logical screen-copy surface/palette/filter.')
        rectangles = []
        for pointer in (arguments[2],arguments[5]):
            rectangle = list(struct.unpack('<4i',uc.mem_read(pointer,16))) if pointer else None
            if rectangle and not 0 <= rectangle[0] <= rectangle[2] <= 4096 or rectangle and not 0 <= rectangle[1] <= rectangle[3] <= 4096:
                raise ValueError('Unbounded screen-copy rectangle.')
            rectangles.append(rectangle)
        record = dict(name='D3DXLoadSurfaceFromSurface.screen',texture=hex(surfaces[arguments[0]]),source=hex(arguments[3]),
                      rectangles=rectangles,filter=2,logicalCopy=True,renderedPixelsCertified=False)
        screen_copies.append(record);log.append(record);ret(0,8)
    m.hook_add(UC_HOOK_CODE,copy_surface,begin=get(0x4b12bc),end=get(0x4b12bc))
    def handle(address,names):
        nonlocal selected
        sp = m.reg_read(UC_X86_REG_ESP)
        if names in (['GDI32.dll!SelectObject'],['GDI32.dll!SetTextColor'],['GDI32.dll!SetBkMode'],['GDI32.dll!TextOutA']):
            if get(sp+4) != guest_dc:raise ValueError('Unobserved GDI DC.')
            name = names[0].split('!')[1]
            if name == 'SelectObject':
                requested = get(sp+8)
                if requested not in font_map:raise ValueError('Unobserved font handle.')
                previous = selected
                if not select(dc,font_map[requested]):raise C.WinError(C.get_last_error())
                selected = requested;result,argc = previous,2
            elif name == 'SetTextColor':result,argc = text_color(dc,get(sp+8)),2
            elif name == 'SetBkMode':result,argc = background(dc,C.c_int32(get(sp+8)).value),2
            else:
                count = get(sp+20)
                if count > 4096:raise ValueError('Unbounded glyph text.')
                raw = bytes(m.mem_read(pixels,size));C.memmove(bits,raw,size)
                text = bytes(m.mem_read(get(sp+16),count))
                result = text_out(dc,C.c_int32(get(sp+8)).value,C.c_int32(get(sp+12)).value,text,count)
                if not result or not flush():raise C.WinError(C.get_last_error())
                m.mem_write(pixels,C.string_at(bits,size));argc = 5
            log.append(dict(name='GDI32.'+name,font=hex(selected),realLocalGdi=True))
            ret(result,argc);return True
        texture = get(sp+4)
        if texture in textures and address == get(get(texture)+0x48):
            if get(sp+8):raise ValueError('Glyph atlas level is not zero.')
            surface = arena+0x1000+(len(uploads)+len(screen_copies))*16
            if surface >= arena+0xf000:raise ValueError('Logical surface address budget exhausted.')
            put(surface,table);surfaces[surface] = texture;put(get(sp+12),surface)
            log.append(dict(name='IDirect3DTexture9.GetSurfaceLevel.glyph',texture=hex(texture),level=0,logical=True))
            ret(0,3);return True
        return False
    def close():
        select(dc,old_font)
        for font in fonts:delete_object(font)
        select(dc,old_bitmap);delete_object(bitmap);delete_dc(dc)
    return dict(handle=handle,close=close,sourceBytes=source_bytes,summary=lambda:dict(realLocalGdi=True,fontInitializationSha256=hashlib.sha256(font_bytes).hexdigest(),
                toolSha256=hashlib.sha256(source_bytes).hexdigest(),uploads=len(uploads),screenCopies=len(screen_copies),logicalAtlasOnly=True,
                renderedPixelsCertified=False))
