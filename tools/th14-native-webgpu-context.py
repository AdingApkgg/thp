"""Native GPU host for the C++ Renderer command ABI; no game/FFP emulation.

No window, browser, input or audio device is opened. The C++ module supplies
expanded pixels, semantic pipeline state, derived matrices and vertex bytes.
"""
from pathlib import Path
import collections
import hashlib
import os
import struct
import sys


class Context:
    def __init__(self, site, shader_path):
        sys.path.insert(0, str(Path(site).resolve(strict=True)))
        os.environ['WGPU_BACKEND_TYPE'] = 'D3D12'
        import wgpu
        from wgpu.backends.wgpu_native import _ffi
        self.wgpu = wgpu
        self.adapter = wgpu.gpu.request_adapter_sync(power_preference='high-performance')
        assert self.adapter.info['backend_type'] == 'D3D12'
        self.device = self.adapter.request_device_sync()
        library = Path(_ffi.lib_path).resolve(strict=True)
        self.shader_source = Path(shader_path).read_text()
        self.shader = self.device.create_shader_module(code=self.shader_source)
        self.resample_source = Path(shader_path).with_name('Th14WebGpuResample.wgsl').read_text()
        self.resample_shader = self.device.create_shader_module(code=self.resample_source)
        self.resample_pipeline = self.device.create_render_pipeline(layout='auto',
            vertex=dict(module=self.resample_shader, entry_point='vs'),
            fragment=dict(module=self.resample_shader, entry_point='fs', targets=[dict(format='bgra8unorm')]))
        self.clear_shader = self.device.create_shader_module(code='''
struct Uniform{color:vec4f,depth:vec4f};
@group(0) @binding(0) var<uniform> u:Uniform;
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0,1);}
struct Output{@location(0) color:vec4f,@builtin(frag_depth) depth:f32};
@fragment fn fs()->Output{return Output(u.color,u.depth.x);}''')
        self.clear_color_shader = self.device.create_shader_module(code='''
struct Uniform{color:vec4f,depth:vec4f};
@group(0) @binding(0) var<uniform> u:Uniform;
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0,1);}
@fragment fn fs()->@location(0) vec4f{return u.color;}''')
        self.clear_pipelines = {}
        self.resources, self.depths, self.pipelines, self.bindings = {}, {}, {}, {}
        self.calls = collections.Counter()
        self.encoder = None
        self.keep = []
        self.info = dict(adapter=dict(self.adapter.info), requiredFeatures=[],
                         wgpuVersion=wgpu.__version__, nativeLibrary=dict(
                             bytes=library.stat().st_size,
                             sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
                             versionWord=int(_ffi.lib.wgpuGetVersion())),
                         shaderSha256=hashlib.sha256(self.shader_source.encode()).hexdigest())
        self.info['resampleShaderSha256'] = hashlib.sha256(self.resample_source.encode()).hexdigest()
        self.upload(0, 1, 1, b'\xff'*4)

    def commands(self):
        if self.encoder is None:
            self.encoder = self.device.create_command_encoder()
        return self.encoder

    def flush(self):
        if self.encoder is not None:
            self.device.queue.submit([self.encoder.finish()])
            self.encoder = None
            self.keep.clear()

    def upload(self, handle, width, height, raw):
        self.flush()  # CPU updates must follow all already encoded draws.
        w = self.wgpu
        if handle in self.resources:
            self.release(handle)
        texture = self.device.create_texture(size=(width, height, 1), format='bgra8unorm',
            usage=w.TextureUsage.COPY_SRC | w.TextureUsage.COPY_DST | w.TextureUsage.TEXTURE_BINDING)
        self.device.queue.write_texture({'texture': texture}, raw, {'bytes_per_row': width*4}, (width, height, 1))
        self.resources[handle] = dict(width=width, height=height, sample=texture, target=None, dirty=False)

    def target(self, handle):
        item = self.resources[handle]
        if item['target'] is None:
            w = self.wgpu
            item['target'] = self.device.create_texture(size=(item['width']+1, item['height']+1, 1),
                format='bgra8unorm', usage=w.TextureUsage.COPY_SRC | w.TextureUsage.COPY_DST | w.TextureUsage.RENDER_ATTACHMENT)
            self.commands().copy_texture_to_texture({'texture': item['sample']}, {'texture': item['target']},
                (item['width'], item['height'], 1))
        return item['target']

    def sample(self, handle):
        item = self.resources[handle]
        if item['dirty']:
            self.commands().copy_texture_to_texture({'texture': item['target']}, {'texture': item['sample']},
                (item['width'], item['height'], 1))
            item['dirty'] = False
        return item['sample']

    def depth(self, handle, width, height, format_code):
        assert format_code in [10, 11, 12]
        if handle in self.depths:
            assert self.depths[handle]['size'] == (width, height, format_code)
            return
        fmt = {10: 'depth16unorm', 11: 'depth24plus', 12: 'depth24plus-stencil8'}[format_code]
        texture = self.device.create_texture(size=(width+1, height+1, 1), format=fmt,
            usage=self.wgpu.TextureUsage.RENDER_ATTACHMENT)
        self.depths[handle] = dict(texture=texture, format=fmt, size=(width, height, format_code))

    def depth_attachment(self, handle):
        if not handle:
            return None
        item = self.depths[handle]
        result = dict(view=item['texture'].create_view(), depth_load_op='load', depth_store_op='store')
        if item['format'].endswith('stencil8'):
            result.update(stencil_load_op='load', stencil_store_op='store')
        return result

    def pipeline(self, p):
        fmt = self.depths[p[1]]['format'] if p[1] else None
        key = (p[3], *p[4:13], fmt)
        if key in self.pipelines:
            return self.pipelines[key]
        blend_names = ['zero', 'one', 'src', 'one-minus-src', 'src-alpha', 'one-minus-src-alpha',
                       'dst-alpha', 'one-minus-dst-alpha', 'dst', 'one-minus-dst', 'src-alpha-saturated']
        equations = ['add', 'subtract', 'reverse-subtract', 'min', 'max']
        compare = ['never', 'less', 'equal', 'less-equal', 'greater', 'not-equal', 'greater-equal', 'always']
        target = dict(format='bgra8unorm', write_mask=p[12])
        if p[6]:
            # GL/D3D color factors map to scalar alpha factors for the alpha
            # channel; WebGPU rejects color-only names in alpha blend state.
            def factor(value, alpha=False):
                if alpha and value in [2, 3]:
                    return 'src-alpha' if value == 2 else 'one-minus-src-alpha'
                if alpha and value in [8, 9]:
                    return 'dst-alpha' if value == 8 else 'one-minus-dst-alpha'
                if alpha and value == 10:
                    return 'one'
                return blend_names[value]
            def component(alpha):
                # min/max ignore blend factors and require one/one in WebGPU.
                return dict(src_factor='one' if p[9] >= 3 else factor(p[7], alpha),
                            dst_factor='one' if p[9] >= 3 else factor(p[8], alpha), operation=equations[p[9]])
            target['blend'] = dict(color=component(False), alpha=component(True))
        descriptor = dict(layout='auto', vertex=dict(module=self.shader, entry_point='vs', buffers=[dict(
            array_stride=40, attributes=[dict(shader_location=0, offset=0, format='float32x4'),
            dict(shader_location=1, offset=16, format='unorm8x4'), dict(shader_location=2, offset=20, format='float32x2'),
            dict(shader_location=3, offset=28, format='float32'), dict(shader_location=4, offset=32, format='float32'),
            dict(shader_location=5, offset=36, format='unorm8x4')])]),
            fragment=dict(module=self.shader, entry_point='fs' if fmt else 'fsColor', targets=[target]),
            primitive=dict(topology={0: 'point-list', 1: 'line-list', 3: 'triangle-list'}[p[3]],
                           front_face='cw', cull_mode=['none', 'back', 'front'][p[11]]))
        if fmt:
            descriptor['depth_stencil'] = dict(format=fmt, depth_write_enabled=bool(p[4] and p[5]),
                depth_compare=compare[p[10]] if p[4] else 'always')
        pipeline = self.device.create_render_pipeline(**descriptor)
        self.pipelines[key] = pipeline
        return pipeline

    def draw(self, packet, vertices, count):
        assert len(packet) == 448 and len(vertices) == count*40
        p = struct.unpack_from('<20I', packet)
        uniform = packet[80:]
        viewport = struct.unpack_from('<4f', uniform, 320)
        minimum, maximum = struct.unpack('<2f', struct.pack('<2I', *p[17:19]))
        color = self.target(p[0])
        texture = self.sample(p[2])
        pipeline = self.pipeline(p)
        bind_key = (id(pipeline), p[2], *p[13:17])
        if bind_key not in self.bindings:
            address = ['repeat', 'mirror-repeat', 'clamp-to-edge']
            sampler = self.device.create_sampler(address_mode_u=address[p[15]], address_mode_v=address[p[16]],
                min_filter=['nearest', 'linear'][p[13]], mag_filter=['nearest', 'linear'][p[14]])
            self.bindings[bind_key] = self.device.create_bind_group(layout=pipeline.get_bind_group_layout(1),
                entries=[dict(binding=0, resource=texture.create_view()), dict(binding=1, resource=sampler)])
        vb = self.device.create_buffer_with_data(data=vertices, usage=self.wgpu.BufferUsage.VERTEX)
        ub = self.device.create_buffer_with_data(data=uniform, usage=self.wgpu.BufferUsage.UNIFORM)
        binding = self.device.create_bind_group(layout=pipeline.get_bind_group_layout(0),
            entries=[dict(binding=0, resource=dict(buffer=ub, size=368))])
        self.keep.extend([vb, ub, binding])
        render = self.commands().begin_render_pass(color_attachments=[dict(view=color.create_view(), load_op='load', store_op='store')],
            depth_stencil_attachment=self.depth_attachment(p[1]))
        item = self.resources[p[0]]
        render.set_scissor_rect(0, 0, item['width'], item['height'])
        x, y, width, height = viewport
        render.set_viewport(x+.5, y+.5, width, height, minimum, maximum)
        render.set_pipeline(pipeline)
        render.set_bind_group(0, binding)
        render.set_bind_group(1, self.bindings[bind_key])
        render.set_vertex_buffer(0, vb)
        render.draw(count)
        render.end()
        item['dirty'] = True

    def clear(self, target, depth, flags, color, value, stencil, rects):
        item = self.resources[target]
        full = rects == [(0, 0, item['width'], item['height'])]
        if not full:
            assert not flags & 4, 'Partial stencil clear is not implemented'
            fmt = self.depths[depth]['format'] if depth else None
            key = (fmt, flags & 3)
            if key not in self.clear_pipelines:
                shader = self.clear_shader if fmt else self.clear_color_shader
                descriptor = dict(layout='auto', vertex=dict(module=shader, entry_point='vs'),
                    fragment=dict(module=shader, entry_point='fs', targets=[dict(format='bgra8unorm', write_mask=15 if flags & 1 else 0)]))
                if fmt:
                    descriptor['depth_stencil'] = dict(format=fmt, depth_write_enabled=bool(flags & 2), depth_compare='always')
                self.clear_pipelines[key] = self.device.create_render_pipeline(**descriptor)
            pipeline = self.clear_pipelines[key]
            uniform = self.device.create_buffer_with_data(data=struct.pack('<8f',
                *[((color >> shift) & 255)/255 for shift in [16, 8, 0, 24]], value, 0, 0, 0), usage=self.wgpu.BufferUsage.UNIFORM)
            binding = self.device.create_bind_group(layout=pipeline.get_bind_group_layout(0),
                entries=[dict(binding=0, resource=dict(buffer=uniform))])
            self.keep.extend([uniform, binding])
            render = self.commands().begin_render_pass(color_attachments=[dict(view=self.target(target).create_view(), load_op='load', store_op='store')],
                depth_stencil_attachment=self.depth_attachment(depth))
            render.set_pipeline(pipeline); render.set_bind_group(0, binding)
            for left, top, right, bottom in rects:
                left, top = max(0, left), max(0, top)
                right, bottom = min(item['width'], right), min(item['height'], bottom)
                if right > left and bottom > top:
                    render.set_scissor_rect(left, top, right-left, bottom-top)
                    render.draw(3)
            render.end(); item['dirty'] = True
            return
        attachment = dict(view=self.target(target).create_view(), load_op='clear' if flags & 1 else 'load', store_op='store',
            clear_value=tuple(((color >> shift) & 255)/255 for shift in [16, 8, 0, 24]))
        z = self.depth_attachment(depth)
        if z and flags & 2:
            z.update(depth_load_op='clear', depth_clear_value=value)
        if z and flags & 4:
            assert self.depths[depth]['format'].endswith('stencil8')
            z.update(stencil_load_op='clear', stencil_clear_value=stencil)
        self.commands().begin_render_pass(color_attachments=[attachment], depth_stencil_attachment=z).end()
        item['dirty'] = True

    def resample(self, source, rect, target, destination, weights, width, height, source_mask, target_mask):
        left, top, right, bottom = rect
        x, y, x1, y1 = destination
        assert x1 > x and y1 > y
        texture, output = self.sample(source), self.target(target)
        uniform = struct.pack('<8i12I', left, top, right-left, bottom-top, x, y, x1-x, y1-y,
            *source_mask, *target_mask, int(weights is not None), width, 0, 0)
        ub = self.device.create_buffer_with_data(data=uniform, usage=self.wgpu.BufferUsage.UNIFORM)
        wb = self.device.create_buffer_with_data(data=weights if weights is not None else bytes(8), usage=self.wgpu.BufferUsage.STORAGE)
        bind = self.device.create_bind_group(layout=self.resample_pipeline.get_bind_group_layout(0),
            entries=[dict(binding=0, resource=dict(buffer=ub)), dict(binding=1, resource=texture.create_view()), dict(binding=2, resource=dict(buffer=wb))])
        self.keep.extend([ub, wb, bind])
        render = self.commands().begin_render_pass(color_attachments=[dict(view=output.create_view(), load_op='load', store_op='store')])
        render.set_pipeline(self.resample_pipeline); render.set_bind_group(0, bind)
        render.set_viewport(x, y, x1-x, y1-y, 0, 1)
        render.set_scissor_rect(x, y, x1-x, y1-y)
        render.draw(3); render.end(); self.resources[target]['dirty'] = True
        return 1

    def read(self, handle):
        item = self.resources[handle]
        texture = self.target(handle)
        self.flush()
        stride = (item['width']*4+255) & ~255
        raw = bytes(self.device.queue.read_texture({'texture': texture},
            dict(bytes_per_row=stride, rows_per_image=item['height']), (item['width'], item['height'], 1)))
        return b''.join(raw[y*stride:y*stride+item['width']*4] for y in range(item['height']))

    def copy(self, source, rect, target, point):
        left, top, right, bottom = rect
        self.commands().copy_texture_to_texture(dict(texture=self.sample(source), origin=(left, top, 0)),
            dict(texture=self.target(target), origin=(*point, 0)), (right-left, bottom-top, 1))
        self.resources[target]['dirty'] = True

    def release(self, handle):
        self.flush()
        if handle in self.resources:
            item = self.resources.pop(handle)
            for key in ['sample', 'target']:
                if item[key] is not None:
                    item[key].destroy()
        if handle in self.depths:
            self.depths.pop(handle)['texture'].destroy()
        self.bindings.clear()

    def alpha_boundaries(self):
        # Calibrate the GPU's actual RGBA8 conversion, including tie neighbors.
        w = self.wgpu
        shader = self.device.create_shader_module(code='''
@group(0) @binding(0) var<storage,read> values:array<vec4f>;
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0,1);}
@fragment fn fs(@builtin(position) p:vec4f)->@location(0) vec4f{return vec4f(0,0,0,values[u32(p.x)].x);}''')
        pipeline = self.device.create_render_pipeline(layout='auto', vertex=dict(module=shader, entry_point='vs'),
            fragment=dict(module=shader, entry_point='fs', targets=[dict(format='bgra8unorm')]))
        values = self.device.create_buffer(size=4096, usage=w.BufferUsage.STORAGE | w.BufferUsage.COPY_DST)
        bind = self.device.create_bind_group(layout=pipeline.get_bind_group_layout(0), entries=[dict(binding=0, resource=dict(buffer=values))])
        target = self.device.create_texture(size=(256, 1, 1), format='bgra8unorm', usage=w.TextureUsage.RENDER_ATTACHMENT | w.TextureUsage.COPY_SRC)
        def sample(words):
            self.device.queue.write_buffer(values, 0, b''.join(struct.pack('<4I', word, 0, 0, 0) for word in words))
            encoder = self.device.create_command_encoder()
            render = encoder.begin_render_pass(color_attachments=[dict(view=target.create_view(), load_op='clear', store_op='store', clear_value=(0, 0, 0, 0))])
            render.set_pipeline(pipeline); render.set_bind_group(0, bind); render.draw(3); render.end()
            self.device.queue.submit([encoder.finish()])
            return bytes(self.device.queue.read_texture({'texture': target}, dict(bytes_per_row=1024, rows_per_image=1), (256, 1, 1)))[3::4]
        word = lambda value: struct.unpack('<I', struct.pack('<f', value))[0]
        lo = [0]+[word((i-1)/255) for i in range(1, 256)]
        hi = [0]+[word(i/255) for i in range(1, 256)]
        for _ in range(32):
            if all(hi[i]-lo[i] <= 1 for i in range(1, 256)):
                break
            mid = [a+(b-a)//2 for a, b in zip(lo, hi)]
            result = sample(mid)
            for i in range(1, 256):
                if hi[i]-lo[i] > 1:
                    if result[i] >= i: hi[i] = mid[i]
                    else: lo[i] = mid[i]
        lower, upper = sample(lo), sample(hi)
        assert all(hi[i]-lo[i] == 1 and lower[i] < i <= upper[i] for i in range(1, 256))
        target.destroy(); values.destroy()
        return struct.pack('<256I', *hi)

    def invoke(self, name, caller, *args):
        self.calls[name] += 1
        memory = caller['memory']
        read = lambda ptr, size: bytes(memory.read(caller, ptr, ptr+size))
        ints = lambda ptr, count: struct.unpack('<'+'i'*count, read(ptr, count*4))
        if name == 'th14_webgpu_open':
            memory.write(caller, self.alpha_boundaries(), args[0]); return 1
        if name == 'th14_webgpu_upload':
            handle, width, height, ptr = args
            return self.upload(handle, width, height, read(ptr, width*height*4))
        if name == 'th14_webgpu_depth': return self.depth(*args)
        if name == 'th14_webgpu_draw':
            packet, vertices, count = args
            return self.draw(read(packet, 448), read(vertices, count*40), count)
        if name == 'th14_webgpu_clear':
            target, depth, flags, color, value, stencil, ptr, count = args
            rects = ints(ptr, count*4)
            return self.clear(target, depth, flags, color, value, stencil, [tuple(rects[i:i+4]) for i in range(0, len(rects), 4)])
        if name == 'th14_webgpu_copy':
            source, rect, target, point = args
            return self.copy(source, ints(rect, 4), target, ints(point, 2))
        if name == 'th14_webgpu_resample':
            source, rect, target, destination, ptr, width, height, im, om = args
            return self.resample(source, ints(rect, 4), target, ints(destination, 4),
                read(ptr, width*height*8) if ptr else None, width, height, ints(im, 4), ints(om, 4))
        if name == 'th14_webgpu_read':
            handle, ptr, size = args; raw = self.read(handle); assert len(raw) == size
            memory.write(caller, raw, ptr); return
        if name == 'th14_webgpu_release': return self.release(*args)
        if name == 'th14_webgpu_present': self.flush(); return
        if name == 'th14_webgpu_close': return self.close()
        raise AssertionError('Unimplemented GPU import: '+name)

    def close(self):
        self.flush()
        for handle in list(self.resources)+list(self.depths):
            self.release(handle)
        self.device.destroy()
