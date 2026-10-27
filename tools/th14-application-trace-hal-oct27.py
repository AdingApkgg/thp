"""Replay the observed Application frame through an independent D3D9 HAL.

Consumes actual semantic C++ vertices/state and retained initial color images.
Initial depth is required to be cleared before it can affect drawing. No game
process, GUI input, visible window or audio device is used.
"""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import importlib.util
import json
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SDK = Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')
P, U, I, F = C.c_void_p, C.c_uint32, C.c_int32, C.c_float
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


class Present(C.Structure):
    _fields_ = [(n, U) for n in ['width', 'height', 'format', 'count', 'multisample', 'quality', 'swap']] + [('window', P), ('windowed', I), ('depth', I)] + [(n, U) for n in ['depth_format', 'flags', 'refresh', 'interval']]


class Lock(C.Structure):
    _fields_ = [('pitch', I), ('bits', P)]


class Viewport(C.Structure):
    _fields_ = [(n, U) for n in ['x', 'y', 'width', 'height']] + [('minimum', F), ('maximum', F)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--expected-frame', type=int, default=2264, help='Explicit Application frame represented by this trace')
    parser.add_argument('--baseline', type=Path, help='Captured complete Application buffer; defaults to the legacy demo-1-ready filename')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wgpu-site', type=Path, help='Replay identical packets on the current native WebGPU host and compare after every draw')
    parser.add_argument('--process-vertices', type=int, nargs='*', default=[], help='Capture D3D9 ProcessVertices output before these one-based actual draws')
    parser.add_argument('--float-source-probes', type=int, nargs='*', default=[], help='Observe these draws without blending/depth on float color targets, then restore actual state')
    parser.add_argument('--uv-probes', type=int, nargs='*', default=[], help='Observe interpolated UV before sampling with own pass-through pixel shaders')
    parser.add_argument('--final-only', action='store_true', help='Skip intermediate full-color readbacks; still require exact complete WebGPU replay at the end')
    parser.add_argument('--shader-variant', choices=['baseline','viewport-global'], default='baseline', help='Private experiment only; never changes production sources')
    parser.add_argument('--require-native-equality', action='store_true', help='Require the current production replay to equal the independent native buffer after a source fix')
    args = parser.parse_args()
    assert not (args.require_native_equality or args.float_source_probes or args.uv_probes) or args.wgpu_site
    source = args.trace.resolve(strict=True)
    out = args.output.resolve()
    assert source.is_relative_to(ROOT / 'artifacts/th14') and out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    tool_raw = Path(__file__).read_bytes(); (out / 'run-tool.py').write_bytes(tool_raw)
    trace_raw = source.read_bytes(); trace = json.loads(trace_raw)
    assert 1<=args.expected_frame<=240000 and trace['frame'] == args.expected_frame and trace['semanticInputsObservedBeforeBackend'] and not trace['nativeValuesProvidedToEngine']
    assert all(row['sequence'] == index for index, row in enumerate(trace['events']))
    expected_draws=sum(row['kind']==101 for row in trace['events'])
    expected_clears=sum(row['kind']==110 for row in trace['events'])
    assert expected_draws>0 and expected_clears>0
    header = SDK.read_bytes(); tables = {}
    for name in ['IDirect3D9', 'IDirect3DDevice9', 'IDirect3DSurface9', 'IDirect3DTexture9', 'IDirect3DVertexBuffer9', 'IDirect3DPixelShader9']:
        body = header.decode().split('DECLARE_INTERFACE_(' + name + ',', 1)[1].split('};', 1)[0]
        tables[name] = {a.strip() or b.strip(): index for index, (a, b) in enumerate(re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)', body))}

    def method(obj, interface, name, signature):
        address = C.cast(obj, C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
        return C.WINFUNCTYPE(I, P, *signature)(address)

    def call(obj, interface, name, signature, values):
        result = method(obj, interface, name, signature)(obj, *values)
        assert result >= 0, (name, hex(result & 0xffffffff))

    blobs = {}
    def blob(row):
        if row['sha256'] not in blobs:
            path = source.parent / row['file']; assert path.resolve().is_relative_to(source.parent)
            raw = path.read_bytes(); assert len(raw) == row['bytes'] and SHA(raw) == row['sha256']
            blobs[row['sha256']] = raw
        return blobs[row['sha256']]

    initial = {r['handle']: r for r in trace['initial']['resources']}
    metadata = {}; targets = set()
    for row in trace['events']:
        w = row['words']
        if row['kind'] == 1: targets.add(w[1])
        elif row['kind'] == 10: targets.add(w[0])
    assert targets == {1, 9, 10}
    color_formats = {0: 20, 1: 21, 2: 22, 3: 23, 4: 24, 5: 25, 6: 26, 7: 28, 8: 50, 9: 51}
    textures = {}; surfaces = {}; depths = {}; depth_cleared = set(); readbacks = {}; retained = []
    device = P(); d3d = P(); window = None; scene_open = False
    draws = 0; clears = 0; last_event = None; error = ''; completed = False
    replay = None; steps = []; first_targets = set(); first_critical = set(); last_colors = {}
    processed_vertices = []
    float_sources = []
    probes = [(361,211),(384,215),(358,219),(365,219),(383,219),(364,220),(386,312),(343,327),(135,371),(285,394),(387,394),(268,438),(342,442),(230,443)]
    user = C.WinDLL('user32'); user.CreateWindowExW.restype = P
    user.CreateWindowExW.argtypes = [U, C.c_wchar_p, C.c_wchar_p, U, I, I, I, I, P, P, P, P]
    user.DestroyWindow.argtypes = [P]
    dll = C.WinDLL('d3d9'); dll.Direct3DCreate9.restype = P; dll.Direct3DCreate9.argtypes = [U]
    float_value = lambda word: struct.unpack('<f', struct.pack('<I', word))[0]
    rs = lambda key, value: call(device, 'IDirect3DDevice9', 'SetRenderState', [U, U], [key, value])
    ts = lambda stage, key, value: call(device, 'IDirect3DDevice9', 'SetTextureStageState', [U, U, U], [stage, key, value])
    ss = lambda key, value: call(device, 'IDirect3DDevice9', 'SetSamplerState', [U, U, U], [0, key, value])

    def texture(handle):
        if handle in textures: return textures[handle]
        row = metadata.get(handle); start = initial.get(handle)
        assert row or start, ('Missing observed resource', handle)
        width, height = row['words'][1:3] if row else (start['width'], start['height'])
        fmt = row['words'][3] if row else 1
        obj = P()
        native_format = color_formats[fmt]
        is_target = handle in targets
        if is_target: assert fmt == 1, 'This actual-frame oracle requires observed ARGB8 render targets'
        call(device, 'IDirect3DDevice9', 'CreateTexture', [U, U, U, U, U, U, C.POINTER(P), P],
             [width, height, 1, 1 if is_target else 0, native_format, 0 if is_target else 1, C.byref(obj), None])
        textures[handle] = obj
        lock = Lock()
        if is_target:
            surface = P(); call(obj, 'IDirect3DTexture9', 'GetSurfaceLevel', [U, C.POINTER(P)], [0, C.byref(surface)])
            surfaces[handle] = surface
            assert start, ('Missing initial GPU color', handle)
            raw = blob(start['pixels']); assert len(raw) == width * height * 4
            system = P(); call(device, 'IDirect3DDevice9', 'CreateOffscreenPlainSurface', [U, U, U, U, C.POINTER(P), P], [width, height, 21, 2, C.byref(system), None])
            try:
                call(system, 'IDirect3DSurface9', 'LockRect', [P, P, U], [C.byref(lock), None, 0])
                for y in range(height): C.memmove(lock.bits + y * lock.pitch, raw[y * width * 4:(y + 1) * width * 4], width * 4)
                call(system, 'IDirect3DSurface9', 'UnlockRect', [], [])
                call(device, 'IDirect3DDevice9', 'UpdateSurface', [P, P, P, P], [system, None, surface, None])
            finally: method(system, 'IDirect3DSurface9', 'Release', [])(system)
        else:
            if row and row.get('blob'):
                raw = blob(row['blob']); pitch = row['words'][4]
                assert len(raw) == row['words'][5] == pitch * height
            else:
                assert fmt == 1 and start
                raw = blob(start['pixels']); pitch = width * 4
            call(obj, 'IDirect3DTexture9', 'LockRect', [U, P, P, U], [0, C.byref(lock), None, 0])
            for y in range(height): C.memmove(lock.bits + y * lock.pitch, raw[y * pitch:(y + 1) * pitch], pitch)
            call(obj, 'IDirect3DTexture9', 'UnlockRect', [U], [0])
        return obj

    def target(handle, depth):
        texture(handle)
        call(device, 'IDirect3DDevice9', 'SetDepthStencilSurface', [P], [None])
        call(device, 'IDirect3DDevice9', 'SetRenderTarget', [U, P], [0, surfaces[handle]])
        if depth:
            if depth not in depths:
                w = metadata[depth]['words']; obj = P(); assert w[3] in [10, 11, 12]
                call(device, 'IDirect3DDevice9', 'CreateDepthStencilSurface', [U, U, U, U, U, I, C.POINTER(P), P],
                     [w[1], w[2], {10: 80, 11: 77, 12: 75}[w[3]], 0, 0, 0, C.byref(obj), None])
                depths[depth] = obj
            call(device, 'IDirect3DDevice9', 'SetDepthStencilSurface', [P], [depths[depth]])

    def viewport(words):
        vp = Viewport(*words[:4], float_value(words[4]), float_value(words[5]))
        call(device, 'IDirect3DDevice9', 'SetViewport', [P], [C.byref(vp)])

    def pixels(handle):
        nonlocal scene_open
        if scene_open:
            call(device, 'IDirect3DDevice9', 'EndScene', [], []); scene_open = False
        width, height = metadata[handle]['words'][1:3]
        if handle not in readbacks:
            obj = P(); call(device, 'IDirect3DDevice9', 'CreateOffscreenPlainSurface', [U, U, U, U, C.POINTER(P), P], [width, height, 21, 2, C.byref(obj), None])
            readbacks[handle] = obj
        obj = readbacks[handle]
        call(device, 'IDirect3DDevice9', 'GetRenderTargetData', [P, P], [surfaces[handle], obj])
        lock = Lock(); call(obj, 'IDirect3DSurface9', 'LockRect', [P, P, U], [C.byref(lock), None, 16])
        raw = b''.join(C.string_at(lock.bits + y * lock.pitch, width * 4) for y in range(height))
        call(obj, 'IDirect3DSurface9', 'UnlockRect', [], [])
        call(device, 'IDirect3DDevice9', 'BeginScene', [], []); scene_open = True
        return raw

    def compare_step(handle, state=None, draw_input=None):
        if replay is None or args.final_only: return
        a, b = pixels(handle), replay.read(handle)
        assert len(a) == len(b)
        different = [] if a == b else [i for i, (left, right) in enumerate(zip(a, b)) if left != right]
        width = metadata[handle]['words'][1]
        first = different[0] if different else None
        row = dict(event=last_event, completedDraws=draws, target=handle, nativeSha256=SHA(a), webgpuSha256=SHA(b),
            differentBytes=len(different), differentPixels=len({i // 4 for i in different}),
            first=None if first is None else dict(x=first // 4 % width, y=first // 4 // width,
                channel='BGRA'[first % 4], native=a[first], webgpu=b[first]))
        critical=[]
        for probe,(x,y) in enumerate(probes):
            sx=x+(96 if handle in [9,10] else 0);at=(y*width+sx)*4
            if a[at:at+4]!=b[at:at+4]:critical.append(dict(probe=probe,x=sx,y=y,native=list(a[at:at+4]),webgpu=list(b[at:at+4])))
        row['criticalDifferences']=critical
        if any(item['probe']==0 for item in critical)and handle not in first_critical:
            first_critical.add(handle);stem='first-critical-'+str(handle)
            (out/(stem+'-native.bgra')).write_bytes(a);(out/(stem+'-webgpu.bgra')).write_bytes(b)
            before=last_colors[handle]
            (out/(stem+'-before-native.bgra')).write_bytes(before[0]);(out/(stem+'-before-webgpu.bgra')).write_bytes(before[1])
            (out/(stem+'-state.json')).write_text(json.dumps(dict(step=row,stateWords=state,drawInput=draw_input),indent=2)+'\n')
        if different and handle not in first_targets:
            first_targets.add(handle); stem='first-target-'+str(handle)
            (out/(stem+'-native.bgra')).write_bytes(a);(out/(stem+'-webgpu.bgra')).write_bytes(b)
            before=last_colors.get(handle)
            if before:
                (out/(stem+'-before-native.bgra')).write_bytes(before[0]);(out/(stem+'-before-webgpu.bgra')).write_bytes(before[1])
                row['beforeBuffersEqual']=before[0]==before[1]
            if state and state[3]in last_colors:
                color=last_colors[state[3]]
                (out/(stem+'-source-native.bgra')).write_bytes(color[0]);(out/(stem+'-source-webgpu.bgra')).write_bytes(color[1])
            (out/(stem+'-state.json')).write_text(json.dumps(dict(step=row,stateWords=state,drawInput=draw_input),indent=2)+'\n')
            print(json.dumps(dict(firstTargetDifference=row)),flush=True)
        steps.append(row);last_colors[handle]=(a,b)

    def float_source(state, data, packet, uv=False):
        nonlocal scene_open
        assert replay is not None and len(data) // state[10] == 4 and state[119:121] == [4, 2]
        native_rt, system, pixel_shader = P(), P(), P()
        try:
            if uv:
                # COUNT2 supplies only UV. Define Z/W explicitly so the real
                # alpha-test state does not discard an undefined W component.
                # Shader Model 3 cannot be paired with the fixed-function
                # vertex pipeline. ps_2_0 uses its defined t0 output register.
                assembly = b'ps_2_0\ndcl t0.xy\ndef c0, 0, 0, 0, 1\nmov r0, c0\nmov r0.xy, t0\nmov oC0, r0\n'
                d3dx = C.WinDLL('C:/Windows/System32/d3dx9_43.dll')
                assemble = d3dx.D3DXAssembleShader
                assemble.argtypes = [C.c_char_p, U, P, P, U, C.POINTER(P), C.POINTER(P)]; assemble.restype = I
                code, messages = P(), P(); result = assemble(assembly,len(assembly),None,None,0,C.byref(code),C.byref(messages))
                def buffer_method(obj,index,restype):
                    address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[index]
                    return C.WINFUNCTYPE(restype,P)(address)(obj)
                try:
                    assert result >= 0, ('D3DXAssembleShader',hex(result&0xffffffff),C.string_at(buffer_method(messages,3,P)) if messages.value else None)
                    bytecode = C.string_at(buffer_method(code,3,P),buffer_method(code,4,U))
                    (out/'uv-probe-native-ps.bin').write_bytes(bytecode)
                    code_data = C.create_string_buffer(bytecode)
                    call(device,'IDirect3DDevice9','CreatePixelShader',[P,C.POINTER(P)],[code_data,C.byref(pixel_shader)])
                finally:
                    for obj in (code,messages):
                        if obj.value: buffer_method(obj,2,U)
            call(device, 'IDirect3DDevice9', 'CreateRenderTarget', [U, U, U, U, U, I, C.POINTER(P), P],
                [640, 480, 116, 0, 0, 0, C.byref(native_rt), None])
            call(device, 'IDirect3DDevice9', 'CreateOffscreenPlainSurface', [U, U, U, U, C.POINTER(P), P],
                [640, 480, 116, 2, C.byref(system), None])
            call(device, 'IDirect3DDevice9', 'SetDepthStencilSurface', [P], [None])
            call(device, 'IDirect3DDevice9', 'SetRenderTarget', [U, P], [0, native_rt]); viewport([0,0,640,480,0,0x3f800000])
            rs(7, 0); rs(14, 0); rs(27, 0)
            if uv: rs(28,0)  # Legacy post-pixel-shader fog must not alter the UV observation.
            call(device, 'IDirect3DDevice9', 'Clear', [U, P, U, U, F, U], [0, None, 1, 0, 1, 0])
            viewport(state[4:10])
            if uv: call(device,'IDirect3DDevice9','SetPixelShader',[P],[pixel_shader])
            vertices = C.create_string_buffer(data)
            call(device, 'IDirect3DDevice9', 'DrawPrimitiveUP', [U, U, P, U], [5, 2, vertices, state[10]])
            call(device, 'IDirect3DDevice9', 'EndScene', [], []); scene_open = False
            call(device, 'IDirect3DDevice9', 'GetRenderTargetData', [P, P], [native_rt, system])
            lock = Lock(); call(system, 'IDirect3DSurface9', 'LockRect', [P, P, U], [C.byref(lock), None, 16])
            native_raw = b''.join(C.string_at(lock.bits + y * lock.pitch, 640 * 16) for y in range(480))
            call(system, 'IDirect3DSurface9', 'UnlockRect', [], [])
        finally:
            if uv: call(device,'IDirect3DDevice9','SetPixelShader',[P],[None])
            target(state[1], state[2]); viewport(state[4:10])
            rs(7, state[15]); rs(14, state[16]); rs(27, state[17])
            if uv: rs(28,state[19])
            if not scene_open:
                call(device, 'IDirect3DDevice9', 'BeginScene', [], []); scene_open = True
            for obj in (system, native_rt):
                if obj.value: method(obj, 'IDirect3DSurface9', 'Release', [])(obj)
            if pixel_shader.value: method(pixel_shader,'IDirect3DPixelShader9','Release',[])(pixel_shader)
        # Identical production shader, uniforms, expanded vertices and texture;
        # only blend/depth storage are removed to observe the source fragment.
        w = replay.wgpu; d = replay.device; replay.flush()
        p = struct.unpack_from('<20I', packet); gpu_vertices = packet[448:]
        shader = replay.shader
        if uv:
            shader = d.create_shader_module(code=replay.shader_source+'\n@fragment fn fsProbe(v:Output)->@location(0) vec4f{return vec4f(v.uv,0,1);}\n')
        pipeline = d.create_render_pipeline(layout='auto', vertex=dict(module=shader, entry_point='vs', buffers=[dict(
            array_stride=40, attributes=[dict(shader_location=0, offset=0, format='float32x4'),
                dict(shader_location=1, offset=16, format='unorm8x4'), dict(shader_location=2, offset=20, format='float32x2'),
                dict(shader_location=3, offset=28, format='float32'), dict(shader_location=4, offset=32, format='float32'),
                dict(shader_location=5, offset=36, format='unorm8x4')])]),
            fragment=dict(module=shader, entry_point='fsProbe' if uv else 'fsColor', targets=[dict(format='rgba32float')]),
            primitive=dict(topology='triangle-list', cull_mode='none'))
        color = d.create_texture(size=(641,481,1), format='rgba32float', usage=w.TextureUsage.COPY_SRC | w.TextureUsage.RENDER_ATTACHMENT)
        ub = d.create_buffer_with_data(data=packet[80:448], usage=w.BufferUsage.UNIFORM)
        vb = d.create_buffer_with_data(data=gpu_vertices, usage=w.BufferUsage.VERTEX)
        sampler = d.create_sampler(address_mode_u=['repeat','mirror-repeat','clamp-to-edge'][p[15]],
            address_mode_v=['repeat','mirror-repeat','clamp-to-edge'][p[16]],
            min_filter=['nearest','linear'][p[13]], mag_filter=['nearest','linear'][p[14]])
        group0 = d.create_bind_group(layout=pipeline.get_bind_group_layout(0), entries=[dict(binding=0, resource=dict(buffer=ub, size=368))])
        if not uv: group1 = d.create_bind_group(layout=pipeline.get_bind_group_layout(1), entries=[dict(binding=0, resource=replay.sample(p[2]).create_view()), dict(binding=1, resource=sampler)])
        encoder = d.create_command_encoder(); render = encoder.begin_render_pass(color_attachments=[dict(view=color.create_view(), clear_value=(0,0,0,0),load_op='clear',store_op='store')])
        render.set_scissor_rect(0,0,640,480); render.set_viewport(state[4]+.5,state[5]+.5,state[6],state[7],float_value(state[8]),float_value(state[9]))
        render.set_pipeline(pipeline); render.set_bind_group(0,group0)
        if not uv: render.set_bind_group(1,group1)
        render.set_vertex_buffer(0,vb)
        render.draw(len(gpu_vertices)//40); render.end(); d.queue.submit([encoder.finish()])
        gpu_raw = bytes(d.queue.read_texture(dict(texture=color),dict(bytes_per_row=640*16),(640,480,1)))
        assert len(native_raw) == len(gpu_raw) == 640*480*16
        stem = 'draw-' + str(draws+1) + ('-uv-' if uv else '-source-')
        (out/(stem+'native.rgba32f')).write_bytes(native_raw); (out/(stem+'webgpu.rgba32f')).write_bytes(gpu_raw)
        rows=[]
        for x,y in [(385,5),(457,211),(480,215),(454,219),(461,219),(479,219),(460,220)]:
            at=(y*640+x)*16
            rows.append(dict(x=x,y=y,native=list(struct.unpack_from('<4f',native_raw,at)),webgpu=list(struct.unpack_from('<4f',gpu_raw,at))))
        float_sources.append(dict(draw=draws+1,event=last_event,kind='uv' if uv else 'source',nativeSha256=SHA(native_raw),webgpuSha256=SHA(gpu_raw),probes=rows,
            originalColorPipelineRestored=True,diagnosticBlendDisabled=True,diagnosticDepthDisabled=True,completeGame=False))
        print(json.dumps(float_sources[-1]),flush=True)
        color.destroy();ub.destroy();vb.destroy()

    def draw(state, data, index, instances, repetition, packet):
        nonlocal draws
        assert len(state) == 125 and state[0] == 0x54524331 and len(packet) >= 448
        gpu = struct.unpack_from('<20I', packet)
        assert gpu[:3] == tuple(state[1:4])
        target(state[1], state[2]); viewport(state[4:10])
        assert not state[15] or state[22] == 7 or state[2] in depth_cleared, 'Unknown initial depth could affect this draw'
        assert state[27] == 0, 'Unobserved culling mode'
        for key, value in [(7, state[15]), (14, state[16]), (15, state[18]), (19, state[24] + 1), (20, state[25] + 1),
            (22, 1), (23, state[22] + 1), (24, state[29]), (25, state[23] + 1), (26, state[21]), (27, state[17]),
            (28, state[19]), (29, 0), (34, state[30]), (35, 0), (36, state[33]), (37, state[34]), (38, state[35]),
            (48, state[20]), (52, 0), (137, 0), (140, state[32]), (161, 0), (168, state[28]), (171, state[26] + 1), (194, 0), (206, 0)]: rs(key, value)
        factor = state[31]; matrices = state[55:119]
        if instances:
            assert len(instances) % 68 == 0
            words = struct.unpack_from('<17I', instances, repetition * 68)
            matrices = list(words[:16]) + matrices[16:]; factor = words[16]
        rs(60, factor)
        for key, offset in [(256, 0), (2, 16), (3, 32), (16, 48)]:
            values = (U * 16)(*matrices[offset:offset + 16]); call(device, 'IDirect3DDevice9', 'SetTransform', [U, P], [key, C.byref(values)])
        argument = lambda a: {0: 0, 1: 2, 2: 3, 3: 4}[a[0]] | (16 if a[1] else 0) | (32 if a[2] else 0)
        for key, value in [(1, state[36] + 1), (2, argument(state[37:40])), (3, argument(state[40:43])),
            (4, state[43] + 1), (5, argument(state[44:47])), (6, argument(state[47:50])), (11, 0), (24, 2 if state[50] else 0)]: ts(0, key, value)
        ts(1, 1, 1)
        for key, value in [(1, state[53] + 1), (2, state[54] + 1), (5, state[52] + 1), (6, state[51] + 1), (7, 0), (11, 0)]: ss(key, value)
        call(device, 'IDirect3DDevice9', 'SetTexture', [U, P], [0, texture(state[3]) if state[3] else None])
        offset = 16 if state[11] else 12; fvf = 4 if state[11] else 2
        for field, flag, size in [(12, 0x40, 4), (13, 0x80, 4), (14, 0x100, 8)]:
            if state[field] != 0xffffffff: assert state[field] == offset; offset += size; fvf |= flag
        assert offset == state[10]
        call(device, 'IDirect3DDevice9', 'SetFVF', [U], [fvf])
        if draws + 1 in args.float_source_probes:
            assert not index
            float_source(state, data, packet)
        if draws + 1 in args.uv_probes:
            assert not index
            float_source(state, data, packet, uv=True)
        if draws + 1 in args.process_vertices:
            assert not state[11] and not index and state[14] != 0xffffffff
            source_buffer, target_buffer = P(), P()
            count = len(data) // state[10]; output_stride = 28
            try:
                call(device, 'IDirect3DDevice9', 'CreateVertexBuffer', [U, U, U, U, C.POINTER(P), P],
                    [len(data), 0, fvf, 1, C.byref(source_buffer), None])
                call(device, 'IDirect3DDevice9', 'CreateVertexBuffer', [U, U, U, U, C.POINTER(P), P],
                    [count * output_stride, 0, 0x144, 1, C.byref(target_buffer), None])
                ptr = P()
                call(source_buffer, 'IDirect3DVertexBuffer9', 'Lock', [U, U, C.POINTER(P), U], [0, len(data), C.byref(ptr), 0])
                C.memmove(ptr, data, len(data)); call(source_buffer, 'IDirect3DVertexBuffer9', 'Unlock', [], [])
                call(device, 'IDirect3DDevice9', 'SetStreamSource', [U, P, U, U], [0, source_buffer, 0, state[10]])
                call(device, 'IDirect3DDevice9', 'ProcessVertices', [U, U, U, P, P, U], [0, 0, count, target_buffer, None, 0])
                call(target_buffer, 'IDirect3DVertexBuffer9', 'Lock', [U, U, C.POINTER(P), U], [0, count * output_stride, C.byref(ptr), 16])
                processed = C.string_at(ptr, count * output_stride)
                call(target_buffer, 'IDirect3DVertexBuffer9', 'Unlock', [], [])
                file = 'draw-' + str(draws + 1) + '-processed.bin'; (out / file).write_bytes(processed)
                processed_vertices.append(dict(draw=draws + 1, event=last_event, file=file, sha256=SHA(processed),
                    vertexCount=count, stride=output_stride, fvf=0x144, words=list(struct.unpack('<' + 'I' * (len(processed) // 4), processed)),
                    originalFvf=fvf, stateWords=state, actualWorldWords=list(matrices[:16]),
                    originalVerticesSha256=SHA(data), packetSha256=SHA(packet)))
            finally:
                call(device, 'IDirect3DDevice9', 'SetStreamSource', [U, P, U, U], [0, None, 0, 0])
                for obj in (target_buffer, source_buffer):
                    if obj.value: method(obj, 'IDirect3DVertexBuffer9', 'Release', [])(obj)
        vertices = C.create_string_buffer(data)
        if index:
            indices = C.create_string_buffer(index)
            call(device, 'IDirect3DDevice9', 'DrawIndexedPrimitiveUP', [U, U, U, U, P, U, P, U],
                 [state[119] + 1, 0, len(data) // state[10], state[120], indices, 101 if state[122] == 0 else 102, vertices, state[10]])
        else:
            call(device, 'IDirect3DDevice9', 'DrawPrimitiveUP', [U, U, P, U], [state[119] + 1, state[120], vertices, state[10]])
        draws += 1
        if replay is not None:
            count=(len(packet)-448)//40;assert len(packet)==448+count*40
            replay.draw(packet[:448],packet[448:],count)
            compare_step(state[1],state,dict(instanceRepetition=repetition,worldWords=list(matrices[:16]),factor=factor,
                originalVerticesSha256=SHA(data),originalIndicesSha256=SHA(index),originalInstancesSha256=SHA(instances),packetSha256=SHA(packet)))

    try:
        window = user.CreateWindowExW(0, 'STATIC', 'TH14 actual Application stream control', 0, 0, 0, 640, 480, None, None, None, None); assert window
        d3d = P(dll.Direct3DCreate9(32)); assert d3d
        pp = Present(640, 480, 21, 1, 0, 0, 1, window, 1, 0, 0, 0, 0, 0x80000000)
        call(d3d, 'IDirect3D9', 'CreateDevice', [U, U, P, U, P, C.POINTER(P)], [0, 1, window, 0x40, C.byref(pp), C.byref(device)])
        if args.wgpu_site:
            frozen = out / 'frozen-host'; frozen.mkdir()
            for name, path in [('context.py', ROOT/'tools/th14-native-webgpu-context.py'),
                ('Th14WebGpu.wgsl', ROOT/'runtimes/th12/portable/sdl/Th14WebGpu.wgsl'),
                ('Th14WebGpuResample.wgsl', ROOT/'runtimes/th12/portable/sdl/Th14WebGpuResample.wgsl')]:
                (frozen/name).write_bytes(path.read_bytes())
            if args.shader_variant == 'viewport-global':
                path=frozen/'Th14WebGpu.wgsl'; original=path.read_text()
                old='let pixel=round_even(((vec2f(o.position.x,-o.position.y)*half_viewport)/o.position.w+half_viewport)*256.0)/256.0;'
                new='let pixel=round_even((((vec2f(o.position.x,-o.position.y)*half_viewport)/o.position.w+half_viewport)+u.viewport.xy)*256.0)/256.0-u.viewport.xy;'
                assert original.count(old)==1 or original.count(new)==1
                if old in original:path.write_text(original.replace(old,new))
            spec=importlib.util.spec_from_file_location('actual_gpu_replay',frozen/'context.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            replay=module.Context(args.wgpu_site,frozen/'Th14WebGpu.wgsl')
            for handle,row in initial.items():replay.upload(handle,row['width'],row['height'],blob(row['pixels']))
            for handle,row in trace['initial']['depths'].items():replay.depth(int(handle),*row['size'])
            for handle in targets:
                raw=blob(initial[handle]['pixels']);last_colors[handle]=(raw,raw)
        call(device, 'IDirect3DDevice9', 'BeginScene', [], []); scene_open = True
        pending = None; index = b''; instances = b''; repetition = 0; semantic_clear = None; final = None
        for row in trace['events']:
            last_event = row['sequence']; kind = row['kind']; w = [value & 0xffffffff for value in row['words']]
            if kind == 4:
                if w[0] in metadata: assert metadata[w[0]]['words'] == w and metadata[w[0]].get('blob') == row.get('blob'), 'Unmodelled in-frame surface update'
                metadata[w[0]] = row
            elif kind == 1:
                if pending is not None: assert repetition == (len(instances) // 68 if instances else 1)
                pending = row; index = b''; instances = b''; repetition = 0
            elif kind == 2: index = blob(row['blob'])
            elif kind == 3: instances = blob(row['blob'])
            elif kind == 101:
                assert pending is not None
                draw(pending['words'], blob(pending['blob']), index, instances, repetition, blob(row['blob'])); repetition += 1
            elif kind == 10: semantic_clear = row
            elif kind == 110:
                assert semantic_clear and w[:4] == semantic_clear['words'][:4]
                target(w[0], w[1]); q = semantic_clear['words']; viewport(q[6:10] + [0, 0x3f800000])
                rects = (U * len(row['rectangles']))(*row['rectangles'])
                call(device, 'IDirect3DDevice9', 'Clear', [U, P, U, U, F, U], [w[6], C.byref(rects), w[2], w[3], float_value(w[4]), w[5]])
                if w[2] & 2 and q[6:10] == [0, 0, 640, 480] and row['rectangles'] == [0, 0, 640, 480]: depth_cleared.add(w[1])
                clears += 1
                if replay is not None:
                    rects=row['rectangles'];replay.clear(w[0],w[1],w[2],w[3],float_value(w[4]),w[5],[tuple(rects[i:i+4])for i in range(0,len(rects),4)])
                    compare_step(w[0])
            elif kind == 20: final = w[0]
            elif kind == 120: assert final == w[0]
            else: raise AssertionError(('Unimplemented observed command', kind))
        assert pending is not None and repetition == (len(instances) // 68 if instances else 1)
        assert draws == expected_draws and clears == expected_clears and final == 1
        call(device, 'IDirect3DDevice9', 'EndScene', [], []); scene_open = False
        readback = readbacks.get(1)
        if readback is None:
            readback = P(); call(device, 'IDirect3DDevice9', 'CreateOffscreenPlainSurface', [U, U, U, U, C.POINTER(P), P], [640, 480, 21, 2, C.byref(readback), None])
            readbacks[1] = readback
        call(device, 'IDirect3DDevice9', 'GetRenderTargetData', [P, P], [surfaces[1], readback])
        lock = Lock(); call(readback, 'IDirect3DSurface9', 'LockRect', [P, P, U], [C.byref(lock), None, 16])
        raw = b''.join(C.string_at(lock.bits + y * lock.pitch, 640 * 4) for y in range(480))
        call(readback, 'IDirect3DSurface9', 'UnlockRect', [], [])
        (out / 'frame.bgra').write_bytes(raw); completed = True
        if replay is not None:
            gpu_raw=replay.read(final);(out/'webgpu-frame.bgra').write_bytes(gpu_raw)
            baseline=(args.baseline or(source.parent/'demo-1-ready.bgra')).read_bytes()
            if args.shader_variant == 'baseline' and not args.require_native_equality:assert gpu_raw==baseline,'Packet replay must exactly reproduce the observed C++ Application frame'
            different=[i for i,(a,b)in enumerate(zip(raw,gpu_raw))if a!=b]
            final_differences=[dict(x=i//4%640,y=i//4//640,channel='BGRA'[i%4],native=raw[i],webgpu=gpu_raw[i])for i in different]
            (out/'draw-comparisons.json').write_text(json.dumps(dict(steps=steps,webgpuReplayBaselineExact=gpu_raw==baseline,
                shaderVariant=args.shader_variant,perDrawComparisonsEnabled=not args.final_only,firstDifferingTargets=sorted(first_targets),
                nativeDifferentBytes=len(different),nativeDifferentPixels=len({i//4 for i in different}),nativeDifferences=final_differences),indent=2)+'\n')
            print(json.dumps(dict(finalNativeDifferences=final_differences,shaderVariant=args.shader_variant)),flush=True)
            if args.require_native_equality:assert gpu_raw==raw,'Current production replay must equal every independent D3D9 color byte'
    except BaseException as failure:
        error = repr(failure); raise
    finally:
        if scene_open: method(device, 'IDirect3DDevice9', 'EndScene', [])(device)
        for collection, interface in [(readbacks, 'IDirect3DSurface9'), (depths, 'IDirect3DSurface9'), (surfaces, 'IDirect3DSurface9'), (textures, 'IDirect3DTexture9')]:
            for obj in collection.values(): method(obj, interface, 'Release', [])(obj)
        if device.value: method(device, 'IDirect3DDevice9', 'Release', [])(device)
        if d3d.value: method(d3d, 'IDirect3D9', 'Release', [])(d3d)
        if window: user.DestroyWindow(window)
        if replay is not None:replay.close()
        report = dict(completed=completed, error=error, lastEvent=last_event, actualHalDraws=draws, actualClears=clears,
            sourceTraceSha256=SHA(trace_raw), toolSha256=SHA(tool_raw), sdkSha256=SHA(header),
            d3d9Sha256=SHA(Path('C:/Windows/System32/d3d9.dll').read_bytes()),
            initialColorContentsFromObservedGpu=True, unknownInitialDepthNeverUsed=bool(depth_cleared),
            hiddenOwnDeviceOnly=True, originalProcessLaunched=False, browserAcceptance=False, completeGame=False, nativeEquivalent=False)
        if completed: report['frameSha256'] = SHA(raw)
        if processed_vertices:
            (out / 'processed-vertices.json').write_text(json.dumps(processed_vertices, indent=2) + '\n')
        report['processedVertexDraws'] = [row['draw'] for row in processed_vertices]
        if float_sources:
            (out / 'float-sources.json').write_text(json.dumps(float_sources, indent=2) + '\n')
        report['floatSourceDraws'] = [row['draw'] for row in float_sources]
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
