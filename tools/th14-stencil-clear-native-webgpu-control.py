"""Compare the native Python GPU host's Clear path with retained D3D9 controls."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['reference','wgpu-site','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();reference=args.reference.resolve();out=args.output.resolve()
    assert reference.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir()
    context_path=ROOT/'tools/th14-native-webgpu-context.py';spec=importlib.util.spec_from_file_location('graphics',context_path);graphics=importlib.util.module_from_spec(spec);spec.loader.exec_module(graphics)
    raw=(reference/'report.json').read_bytes();native=json.loads(raw)
    assert native['caseCount']==96 and native['allIndependentCpuExpectationsEqual']and native['actualD3d9Hal']
    ctx=graphics.Context(args.wgpu_site,ROOT/'runtimes/th12/portable/sdl/Th14WebGpu.wgsl');rows=[]
    try:
        ctx.upload(1,64,48,bytes(64*48*4));ctx.depth(2,64,48,12)
        shader=ctx.device.create_shader_module(code='''
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0.5,1);}
@fragment fn fs()->@location(0) vec4f{return vec4f(1);}''')
        def pipeline(stencil):
            depth=dict(format='depth24plus-stencil8',depth_write_enabled=False,depth_compare='always'if stencil else'less')
            if stencil:depth.update(stencil_front=dict(compare='equal'),stencil_back=dict(compare='equal'),stencil_read_mask=255,stencil_write_mask=0)
            return ctx.device.create_render_pipeline(layout='auto',vertex=dict(module=shader,entry_point='vs'),fragment=dict(module=shader,entry_point='fs',targets=[dict(format='bgra8unorm')]),depth_stencil=depth)
        stencil_pipeline=pipeline(True);depth_pipeline=pipeline(False)
        def probe(stencil,ref=0):
            render=ctx.commands().begin_render_pass(color_attachments=[dict(view=ctx.target(1).create_view(),load_op='load',store_op='store')],depth_stencil_attachment=ctx.depth_attachment(2))
            render.set_pipeline(stencil_pipeline if stencil else depth_pipeline)
            if stencil:render.set_stencil_reference(ref)
            render.draw(3);render.end();ctx.resources[1]['dirty']=True
        def clear(flags,color,z,stencil,rects=None):ctx.clear(1,2,flags,color,z,stencil,rects if rects is not None else[(0,0,64,48)])
        for row in native['cases']:
            clear(7,0x7fb13257,.25,17);clear(row['flags'],0x7fa15327,.75,row['stencil'],[tuple(box)for box in row['rectangles']])
            buffers=dict(color=ctx.read(1))
            for ref,label in[(row['stencil']&255,'new-stencil'),(17,'old-stencil')]:
                clear(1,0xff010203,0,0);probe(True,ref);buffers[label]=ctx.read(1)
            clear(1,0xff030507,0,0);probe(False);buffers['depth']=ctx.read(1)
            comparisons=[]
            for label,actual in buffers.items():
                expected=(reference/row['buffers'][label]['file']).read_bytes();assert SHA(expected)==row['buffers'][label]['sha256']
                assert len(actual)==len(expected)==64*48*4
                different=sum(left!=right for left,right in zip(actual,expected))
                (out/f"case-{row['index']:03d}-{label}.bgra").write_bytes(actual)
                comparisons.append(dict(label=label,bytes=len(actual),differentBytes=different,sha256=SHA(actual),halSha256=SHA(expected)))
            rows.append(dict(index=row['index'],flags=row['flags'],stencil=row['stencil'],comparisons=comparisons))
        ctx.depth(3,64,48,10);ctx.depth(4,64,48,11);rejected=[]
        for handle in[0,3,4]:
            try:ctx.clear(1,handle,4,0,.5,7,[(1,1,4,4)])
            except AssertionError as error:assert 'Stencil clear requires stencil storage'in str(error);rejected.append(handle)
            else:raise AssertionError('Invalid stencil storage was accepted')
        result=dict(schema='th14/native-webgpu-stencil-clear/1',caseCount=len(rows),rows=rows,comparedBuffers=384,comparedBytes=384*64*48*4,
            differentBytes=sum(c['differentBytes']for r in rows for c in r['comparisons']),invalidDepthFormatsRejected=rejected,
            actualNativeGpu=True,actualCppRenderer=False,physicalAudioDevicesOpened=0,browserRun=False,browserAcceptance=False,
            contextSha256=SHA(context_path.read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),halReportSha256=SHA(raw),completeGame=False,nativeEquivalent=False,
            scope='Native Python GPU host Clear with independent stencil-equal/depth-less probes against96 actual D3D9 HAL controls; this route has no C++/Asyncify or browser claim.')
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({key:result[key]for key in['caseCount','comparedBuffers','comparedBytes','differentBytes','invalidDepthFormatsRejected']}))
        assert result['differentBytes']==0
    finally:ctx.close()


if __name__=='__main__':main()
