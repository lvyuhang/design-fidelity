// Minimal Cocoa filesystem adapter; no npm runtime is required in Sketch.
exports.existsSync=function(path){return !!NSFileManager.defaultManager().fileExistsAtPath(path);};
exports.mkdirSync=function(path){
  if(!NSFileManager.defaultManager().createDirectoryAtPath_withIntermediateDirectories_attributes_error(path,true,null,null))throw new Error('无法创建文件夹：'+path);
};
exports.statSync=function(path){
  var attributes=NSFileManager.defaultManager().attributesOfItemAtPath_error(path,null);
  if(!attributes)throw new Error('无法读取文件：'+path);
  return {size:Number(attributes.objectForKey('NSFileSize'))};
};
exports.writeFileSync=function(path,text){
  if(!NSString.stringWithString(String(text)).writeToFile_atomically_encoding_error(path,true,NSUTF8StringEncoding,null))throw new Error('无法保存文件：'+path);
};
