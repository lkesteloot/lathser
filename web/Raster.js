// A raster image to print.

'use strict';

define(function () {
    // imageData is an https://developer.mozilla.org/en-US/docs/Web/API/ImageData
    // which you can get from a Canvas 2D context. Position is in inches.
    var Raster = function (imageData, x, y, speed, power) {
        this.imageData = imageData;
        this.x = x;
        this.y = y;
        this.speed = speed;
        this.power = power;
    };

    return Raster;
});
