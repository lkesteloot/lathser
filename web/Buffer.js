// A growable byte buffer.

'use strict';

define([], function () {
    var Buffer = function () {
        this.parts = [];
    };

    Buffer.prototype.write = function (s) {
        this.parts.push(s);
    };

    Buffer.prototype.toDataUri = function (mimeType) {
        var base64 = btoa(this.parts.join(""));
        return "data:" + mimeType + ";base64," + base64;
    };

    return Buffer;
});
