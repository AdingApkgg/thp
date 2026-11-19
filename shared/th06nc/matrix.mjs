const F=Math.fround;
export const identityMatrix=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
// Row-major, row vectors, and native 566d0's sequential float32 sums.
export function multiplyMatrix(a,b){const out=new Float32Array(16);for(let row=0;row<4;row++)for(let col=0;col<4;col++){let value=0;for(let k=0;k<4;k++)value=F(value+F(a[row*4+k]*b[k*4+col]));out[row*4+col]=value;}return out;}
// Native 565b0 keeps unnormalized coordinates when |w| <= 1e-6.
export function transformCoordinate(point,matrix){const [x,y,z]=point,components=Array.from({length:4},(_,c)=>F(F(F(F(y*matrix[4+c])+F(x*matrix[c]))+F(z*matrix[8+c]))+matrix[12+c])),w=components[3];if(!(Math.abs(w)<=F(1e-6))){const inverse=F(1/w);for(let c=0;c<3;c++)components[c]=F(components[c]*inverse);}return components.slice(0,3);}
