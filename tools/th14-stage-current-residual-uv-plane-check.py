"""Independent residual strip UV-plane fits, never runtime correction inputs.

Native/portable rounded RGBA32F words imply only indirect coordinates. Fits use
the same common pixels and frozen submitted vertex UVs in both paths.
"""
import hashlib,json,struct
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
NATIVE='artifacts/th14/stage-current-residual-native-uv-fe406-oct14/'
CANDIDATE='artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'
native=read(NATIVE+'native.json');receipt=read('docs/porting/th14-stage-current-residual-native-full-observed-oct14.json')
prepared=read('artifacts/th14/stage-gpu-stream-replay/prepared.json')
capture=read(CANDIDATE+'uv/capture/report.json')
read(CANDIDATE+'uv/build.json');read(CANDIDATE+'sources.json')
height,width=480,640;yy,xx=np.indices((height,width));rows=[]

def extract(frame,di):
    state={};i=0
    for c in frame['initialState']+frame['commands']:
        if c['kind']=='draw':
            if i==di:return c,state
            i+=1
        elif c['kind']=='transform':state[c['key']]=np.frombuffer(struct.pack('<16I',*c['words']),dtype='<f4').reshape(4,4).T.copy()
        elif c['kind']=='viewport':state['viewport']=c['words']
    raise AssertionError('Draw not found')
def multiply(a,b):
    result=np.empty((4,4),np.float32)
    for row in range(4):
        for col in range(4):
            s=np.float32(a[row,0]*b[0,col])
            for k in range(1,4):s=np.float32(s+np.float32(a[row,k]*b[k,col]))
            result[row,col]=s
    return result
def clip_vertices(matrix,positions):
    # Offline sequential binary32 vector model, not actual GPU position readback.
    result=[]
    for pos in positions:
        value=[]
        for r in range(4):
            s=np.float32(matrix[r,0]*pos[0])
            for k in range(1,4):s=np.float32(s+np.float32(matrix[r,k]*pos[k]))
            value.append(s)
        result.append(value)
    return np.array(result,np.float32)
def fit(p,mask,uv_corners):
    x=xx[mask].astype(float)/width;y=yy[mask].astype(float)/height
    u=p[:,:,0][mask].astype(float);v=p[:,:,1][mask].astype(float)
    # Scale texture coordinates by the actual submitted segment interval.
    du=uv_corners[1,0]-uv_corners[0,0];dv=uv_corners[2,1]-uv_corners[0,1]
    u=(u-uv_corners[0,0])/du;v=(v-uv_corners[0,1])/dv
    one=np.ones_like(x);zero=np.zeros_like(x)
    matrix=np.vstack((np.column_stack((x,y,one,zero,zero,zero,-u*x,-u*y)),np.column_stack((zero,zero,zero,x,y,one,-v*x,-v*y))))
    coefficients,_,rank,svals=np.linalg.lstsq(matrix,np.concatenate((u,v)),rcond=None)
    assert rank==8
    a,b,c,d,e,f,g,h=coefficients;den=g*x+h*y+1
    residual=max(abs((a*x+b*y+c)/den-u).max(),abs((d*x+e*y+f)/den-v).max())
    vertices=[]
    for cu,cv in [(0,0),(1,0),(0,1),(1,1)]:
        position=np.linalg.solve([[a-cu*g,b-cu*h],[d-cv*g,e-cv*h]],[cu-c,cv-f])*[width,height]
        vertices.append({'estimatedXY':position.tolist(),'nearestSnap8XY':(np.rint(position*256)/256).tolist(),'distanceToSnap8':(position-np.rint(position*256)/256).tolist()})
    return {'samples':len(x),'conditionNumber':float(svals[0]/svals[-1]),'maxNormalizedUVResidual':float(residual),'vertices':vertices}

for ni,n in enumerate(native['frames']):
    receipt_row=receipt['rows'][ni];ci=receipt_row['candidateIndex']
    frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(n['stage'],n['frame']))
    draw,state=extract(frame,n['originalDrawIndex']);assert draw['topology']==5 and draw['stride']==24
    vertex=np.frombuffer(struct.pack('<%dI'%len(draw['words']),*draw['words']),dtype='<f4').reshape(-1,6)
    # The existing HAL fixture initializes COUNT2 texture transformation; all
    # selected draw streams retain it. A separate binary32 vector model computes
    # submitted texcoord values, including the real stage4 texture offsets.
    texture_input=np.column_stack((vertex[:,4:6],np.ones(len(vertex),np.float32),np.zeros(len(vertex),np.float32)))
    texture_uv=clip_vertices(state[16],texture_input)[:,:2]
    nb=track(NATIVE+f'frame-{ni:03d}.rgba32f');pb=track(CANDIDATE+'uv/capture/'+f'frame-{ci:03d}.rgba32f')
    assert sha(nb)==n['fullFloatFrameSha256']==receipt_row['nativeSha256']
    assert sha(pb)==capture['reports'][ci]['portableSha256']==receipt_row['portableSha256']
    arrays={'Native':np.frombuffer(nb,dtype='<f4').reshape(height,width,4),'candidate':np.frombuffer(pb,dtype='<f4').reshape(height,width,4)}
    a,b=arrays.values();common=(a[:,:,3]==1)&(b[:,:,3]==1);diffwords=a.view('<u4')!=b.view('<u4');diffpixel=diffwords.any(axis=2)
    assert int(diffwords.sum())==receipt_row['differentFloatWords'] and (a[:,:,3]==b[:,:,3]).all()
    composed=multiply(state[3],multiply(state[2],state[256]));positions=np.column_stack((vertex[:,:3],np.ones(len(vertex),np.float32)));clips=clip_vertices(composed,positions)
    screen=np.column_stack(((clips[:,0].astype(float)/clips[:,3]+1)*320,(-clips[:,1].astype(float)/clips[:,3]+1)*240))
    segments=[];all_classified=np.zeros((height,width),bool)
    for segment in range(len(vertex)//2-1):
        ids=[2*segment,2*segment+1,2*segment+2,2*segment+3];uv=texture_uv[ids].astype(float);u0,u1=uv[0,0],uv[1,0];v0,v1=uv[0,1],uv[2,1]
        normalized_u=(a[:,:,0]-u0)/(u1-u0);normalized_v=(a[:,:,1]-v0)/(v1-v0)
        in_band=common&(normalized_v>1e-4)&(normalized_v<1-1e-4)
        triang=[]
        for corners,selector in [([0,1,2],normalized_u+normalized_v<1-1e-4),([2,1,3],normalized_u+normalized_v>1+1e-4)]:
            mask=in_band&selector;all_classified|=mask;count=int(mask.sum());diffcount=int((mask&diffpixel).sum());fits={}
            if count>=12:
                fits={key:fit(value,mask,uv) for key,value in arrays.items()}
            triang.append({'corners':corners,'samples':count,'differentPixels':diffcount,'differentWords':int(diffwords[mask].sum()),'fits':fits})
        segments.append({'segment':segment,'submittedVertices':ids,'submittedUVs':uv.tolist(),'offlineClipValues':clips[ids].astype(float).tolist(),'offlineIdealScreen':screen[ids].tolist(),'triangles':triang})
    rows.append({'nativeIndex':ni,'candidateIndex':ci,'stage':n['stage'],'frame':n['frame'],'draw':n['originalDrawIndex'],'vertices':len(vertex),'differentWords':int(diffwords.sum()),'differentPixels':int(diffpixel.sum()),'unclassifiedDifferentPixels':int((diffpixel&~all_classified).sum()),'segments':segments})
out={'diagnosticEvidenceVerified':True,'productionChanged':False,'completeGame':False,'nativeEquivalent':False,'rows':rows,'evidence':evidence,'numpyVersion':np.__version__,'toolSha256':sha(Path(__file__).read_bytes()),'scope':'Indirect noise-conditioned rational UV-plane fits on identical common-covered pixels. Submitted original strip UVs identify triangles. Coordinates and offline sequential binary32 clip models are analysis only, not actual GPU position observations or runtime corrections. All full-buffer differences remain failures.'}
(ROOT/'docs/porting/th14-stage-current-residual-uv-plane-observed-oct14.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
for row in rows:
    print('CASE',row['stage'],row['frame'],row['draw'],'words',row['differentWords'],'pixels',row['differentPixels'],'unclassified',row['unclassifiedDifferentPixels'])
    for segment in row['segments']:
        for triangle in segment['triangles']:
            if triangle['differentPixels']:
                fits=triangle['fits'];print('segment',segment['segment'],'triangle',triangle['corners'],'pixels',triangle['samples'],'differences',triangle['differentPixels'])
                if fits:
                    print('estimates',[(i,fits['Native']['vertices'][i]['nearestSnap8XY'],fits['candidate']['vertices'][i]['nearestSnap8XY']) for i in triangle['corners']]);print('fit',[(key,value['conditionNumber'],value['maxNormalizedUVResidual']) for key,value in fits.items()])
