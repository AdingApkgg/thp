// Native result writer 744c2..74558. The allocation's untouched bytes stay
// untouched; the extent at +10 is assigned later by the complete writer.
// This primitive does not serialize chunks or perform the final encryption.
export function initializeScoreHeader(rng,allocation=new Uint8Array(20)){
 if(!(allocation instanceof Uint8Array)||allocation.length!==20)throw Error('TH06nc score header: expected 20 bytes');
 const header=allocation.slice(),view=new DataView(header.buffer);
 header[1]=rng.next16()&255;view.setUint32(2,0x150000,true);
 header[6]=rng.next16()&255;view.setBigUint64(8,20n,true);
 return header;
}
