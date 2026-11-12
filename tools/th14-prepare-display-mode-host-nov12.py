"""Derive a sized, silent offscreen host and ordinary Title/Quit driver."""
from pathlib import Path
import hashlib, json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12'
bindings={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def derive(parent,target,changes):
    path=R/'tools'/parent;source=path.read_text(encoding='utf8');bindings[path.relative_to(R).as_posix()]=sha(path)
    for old,new,count in changes:
        assert source.count(old)==count,(parent,old,source.count(old));source=source.replace(old,new)
    out=R/'tools'/target;assert not out.exists();out.write_text(source,encoding='utf8',newline='\n');bindings[out.relative_to(R).as_posix()]=sha(out)
derive('th14-node-angle-context-nov08.mjs','th14-node-sized-angle-context-nov12.mjs',[
 ('createTh14AngleContext(directory){','createTh14AngleContext(directory,width=640,height=480){\n assert([[640,480],[960,720],[1280,960]].some(s=>s[0]===width&&s[1]===height));',1),
 ('new Int32Array([0x3057,640,0x3056,480,0x3038])','new Int32Array([0x3057,width,0x3056,height,0x3038])',1),
 ('egl:[major[0],minor[0]],extensions:', 'offscreenWidth:width,offscreenHeight:height,egl:[major[0],minor[0]],extensions:',1),
 ('Buffer.alloc(640*480*4)','Buffer.alloc(width*height*4)',1),
 ('(0,0,640,480,0x1908,0x1401,rgba)','(0,0,width,height,0x1908,0x1401,rgba)',1),
 ('for(let y=0;y<480;y++)for(let x=0;x<640;x++)','for(let y=0;y<height;y++)for(let x=0;x<width;x++)',1),
 ('((479-y)*640+x)*4,b=(y*640+x)*4','((height-1-y)*width+x)*4,b=(y*width+x)*4',1)])
derive('th14-full-application-gles-transition-type0-nov09.mjs','th14-full-application-sized-gles-nov12.mjs',[
 ("'./th14-node-angle-context-nov08.mjs'","'./th14-node-sized-angle-context-nov12.mjs'",1),
 ('const context=createTh14AngleContext(options.angleDirectory);',
  '''const context=createTh14AngleContext(options.angleDirectory,options.renderWidth,options.renderHeight);
 const windowSizes=[];const originalSize=base.env.SDL_SetWindowSize;
 base.env.SDL_SetWindowSize=(id,width,height)=>{originalSize(id,width,height);windowSizes.push([width,height]);return 1;};''',1),
 ('originalSdlWindowIsDeclaredBoundary:true,audibleOutput:false','originalSdlWindowIsDeclaredBoundary:true,requestedWindowSizes:windowSizes,audibleOutput:false',1)])
derive('th14-run-ascii-queue-title-quit-nov12.mjs','th14-run-display-mode-title-quit-nov12.mjs',[
 ("'./th14-full-application-gles-transition-type0-nov09.mjs'","'./th14-full-application-sized-gles-nov12.mjs'",1),
 ("const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/ascii-queue-layout-nov12/title-quit');",
  "const mode=Number(process.argv[process.argv.indexOf('--mode')+1]);assert([3,4,5].includes(mode));\nconst root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/display-mode-entry-nov12/application');",1),
 ("const out=resolve(home,'run');", "const out=resolve(home,`run-mode${mode}`);",1),
 ("copyFileSync(resolve(nativeHome,'initial-config.bin'),resolve(out,'save/th14.cfg'));",
  "const config=Buffer.from(read(resolve(nativeHome,'initial-config.bin')));assert(config[0x22]===0&&config[0x23]===0);config[0x1f]=mode;writeFileSync(resolve(out,'save/th14.cfg'),config);",1),
 ("const platform=fullApplicationGlesPlatform(module,memory,{clockInput:profile.actualInitialTimeGetTimeInput,",
  "const nativeModes=load(resolve(root,'artifacts/th14/display-mode-entry-nov12/native.json'));const nativeMode=nativeModes.rows.find(r=>r.mode===mode);assert(nativeMode);\nconst nativeContext=load(resolve(root,'artifacts/th14/display-mode-entry-nov12/context-native-v2/report.json')).rows.find(r=>r.mode===mode&&r.resource===1).stages[1];\nconst platform=fullApplicationGlesPlatform(module,memory,{renderWidth:nativeMode.width,renderHeight:nativeMode.height,clockInput:profile.actualInitialTimeGetTimeInput,",1),
 ("initialConfigSha256:sha(read(resolve(nativeHome,'initial-config.bin')))","initialConfigSha256:sha(config),changedConfigByte:0x1f,selectedDisplayMode:mode",1),
 ("let created=false,closed=false,saved=false,exception=null,stage='wait-title'", "let created=false,closed=false,saved=false,displayCaptured=false,exception=null,stage='wait-title'",1),
 ("function input(held,label){assert.equal(c.held_input(held),1);inputAt=frames;actions.push({label,held,frame:frames,state:state()});}",
  '''function input(held,label){assert.equal(c.held_input(held),1);inputAt=frames;actions.push({label,held,frame:frames,state:state()});}
function captureDisplay(){
 const actual=Array.from(new Uint32Array(memory.buffer,c.display_state(),37));
 const {width,height}=nativeMode;
 assert.deepEqual(actual.slice(0,11),[mode,width,height,width,height,width*4,width,height,width*2,width,height]);
 assert.deepEqual(actual.slice(11,16),nativeContext.slice(0,5));
 for(let i=0;i<4;i++)assert.deepEqual(actual.slice(16+i*4,20+i*4),nativeContext.slice(5+i*8,9+i*8));
 assert.equal(actual[36],37);
 const pixels=platform.readBGRA();assert.equal(pixels.length,width*height*4);
 let varied=0;for(let i=4;i<pixels.length;i+=4)if(!pixels.subarray(i,i+4).equals(pixels.subarray(0,4)))++varied;
 assert(varied>100,'Title frame must contain visible geometry');
 writeFileSync(resolve(out,'title.bgra'),pixels);
 put('display.json',{mode,width,height,actualWords:actual,frame:frames,pixelsBytes:pixels.length,pixelsSha256:sha(pixels),pixelsDifferentFromTopLeft:varied,
  nativeContextWordsCompared:21,nativeWholeFramePixelComparison:false,completeGame:false});displayCaptured=true;
}''',1),
 ("{assert.equal(s[4],0);input(2,'escape-select-Quit');", "{assert.equal(s[4],0);captureDisplay();input(2,'escape-select-Quit');",1),
 ("assert(saved&&stage==='finished','Ordinary Quit did not finish within declared bounds');", "assert(saved&&displayCaptured&&stage==='finished','Ordinary Quit/display did not finish within declared bounds');",1),
 ('const report={pid:process.pid,terminal:true,closed,stage,frames,exception,errors,exitSaveExecuted:saved,',
  'const report={selectedDisplayMode:mode,displayCaptured,pid:process.pid,terminal:true,closed,stage,frames,exception,errors,exitSaveExecuted:saved,',1)])
(H/'host-derivation.json').write_text(json.dumps(dict(bindings=bindings,newGameRuns=0,canonicalEngineChanged=False),indent=2)+'\n')
print(json.dumps(dict(derivedFiles=3,canonicalEngineChanged=False)))
