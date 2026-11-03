"""Keep ANM camera references synchronized with the currently published word prefix."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
 parent=R/'tools/th14-prepare-camera-word-publication-nov04.py'
 subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
 prior=(out/'prepared.json').read_bytes();prep=json.loads(prior);(out/'parent-prepared.json').write_bytes(prior)
 source=Path(prep['sourceRoot'])/'th12_web/cpp/game/Stage.cpp';before=source.read_bytes();text=before.decode().replace('\r\n','\n')
 start=text.index('bool Stage::publish_camera(');end=text.index('bool Stage::update_deformation()',start);fn=text[start:end]
 post=fn.index('#if PORT_TITLE == 14\n    // Retail46f921..46f95c');old_body=fn[post:]
 assert old_body.endswith('return true;\n}\n')
 references=old_body.removesuffix('return true;\n}\n')
 fn=fn[:post]+'    refresh_camera_references();return true;\n}\n'
 marker='    if(!active_camera)return true;\n';assert fn.count(marker)==1
 fn=fn.replace(marker,marker+'    const auto refresh_camera_references=[this](){\n'+references+'    };\n')
 marker='    if(camera_word_boundary){\n';assert fn.count(marker)==1;fn=fn.replace(marker,marker+'        refresh_camera_references();\n')
 marker='                reinterpret_cast<const u8*>(&state.camera)+i*sizeof(u32),sizeof(u32));\n';assert fn.count(marker)==1;fn=fn.replace(marker,marker+'            refresh_camera_references();\n')
 text=text[:start]+fn+text[end:];ending='\r\n'if before.count(b'\r\n')==before.count(b'\n')and b'\r\n'in before else'\n';after=text.replace('\n',ending).encode();source.write_bytes(after)
 change=next(x for x in prep['changes']if x['path']=='th12_web/cpp/game/Stage.cpp');assert change['afterSha256']==SHA(before);change['afterSha256']=SHA(after)
 prep.update(preparerSha256=SHA(Path(__file__).read_bytes()),cameraWordParentPreparerSha256=SHA(parent.read_bytes()),cameraWordParentPreparationSha256=SHA(prior),liveAnmCameraReferencesDuringPublication=True,nativeReferenceBlocks=[0x46f921,0x46f935,0x46f949,0x46f95d,0x46f969,0x46f975],rootProductionSourcesModified=False,productionIntegrated=False,oldFailureClosed=False)
 (out/'prepared.json').write_bytes((json.dumps(prep,indent=2)+'\n').encode());print(json.dumps(prep),flush=True)
if __name__=='__main__':main()
