'use strict';
exports.wavBlob = function () {
 const bytes=Buffer.alloc(48);
 bytes.write('RIFF',0);bytes.writeUInt32LE(40,4);bytes.write('WAVEfmt ',8);
 bytes.writeUInt32LE(16,16);bytes.writeUInt16LE(1,20);bytes.writeUInt16LE(1,22);
 bytes.writeUInt32LE(24000,24);bytes.writeUInt32LE(48000,28);bytes.writeUInt16LE(2,32);bytes.writeUInt16LE(16,34);
 bytes.write('data',36);bytes.writeUInt32LE(4,40);bytes.writeInt16LE(1234,44);bytes.writeInt16LE(-1234,46);
 return new Blob([bytes],{type:'audio/wav'});
};
