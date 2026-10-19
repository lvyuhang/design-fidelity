'use strict';
// Decode only the uncompressed, interleaved 8-bit RGB(A) TIFF that AppKit
// produces. All other layouts fail closed. No external runtime is required.
function decode(b){
  var view=new DataView(b.buffer,b.byteOffset,b.byteLength);
  var le=b[0]===73&&b[1]===73;
  if(!le&&!(b[0]===77&&b[1]===77))throw new Error('TIFF byte order');
  function u16(o){return view.getUint16(o,le);}
  function u32(o){return view.getUint32(o,le);}
  if(u16(2)!==42)throw new Error('TIFF format');
  var offset=u32(4),tags={},count=u16(offset);
  for(var i=0;i<count;i++){
    var p=offset+2+i*12,tag=u16(p),type=u16(p+2),n=u32(p+4),size=type===3?2:type===4?4:0;
    if(!size)continue;
    var pos=size*n<=4?p+8:u32(p+8),values=[];
    for(var j=0;j<n;j++)values.push(size===2?u16(pos+j*size):u32(pos+j*size));
    tags[tag]=values;
  }
  function first(tag,fallback){return tags[tag]?tags[tag][0]:fallback;}
  var w=first(256),h=first(257),channels=first(277);
  if(first(259)!==1||first(262)!==2||first(284,1)!==1||first(274,1)!==1||[3,4].indexOf(channels)<0||!tags[258]||tags[258].some(function(n){return n!==8;})||first(339,1)!==1)throw new Error('Unsupported TIFF pixels');
  if(channels===4&&[1,2].indexOf(first(338))<0)throw new Error('Unknown alpha');
  var data=new Uint8Array(w*h*channels),written=0;
  tags[273].forEach(function(start,i){var size=tags[279][i];if(start+size>b.length||written+size>data.length)throw new Error('TIFF strip bounds');data.set(b.subarray(start,start+size),written);written+=size;});
  if(written!==data.length)throw new Error('TIFF strips incomplete');
  return {width:w,height:h,channels:channels,alpha:first(338,0),data:data};
}
function compare(a,b,onProgress){
  if(a.width!==b.width||a.height!==b.height||a.channels!==b.channels||a.alpha!==b.alpha)return {ok:false};
  var changed=0,c=a.channels;
  for(var i=0;i<a.data.length;i+=c){if(onProgress&&i%(c*16384)===0)onProgress();var delta=false;
    for(var z=0;z<c;z++){var d=Math.abs(a.data[i+z]-b.data[i+z]);if(d>(z===3?0:1))return {ok:false};if(d)delta=true;}
    if(delta&&++changed>a.width*a.height*.0005)return {ok:false};
  }
  return {ok:true,subtle:changed>0,changed:changed};
}
exports.decode=decode;exports.compare=compare;
