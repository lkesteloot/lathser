// Encapsulates a single continuous cut to be printed to the laser printer.

'use strict';

define([], function () {
    var Cut = function (path, speed, power, frequency) {
        this.path = path;
        this.speed = speed;
        this.power = power;
        this.frequency = frequency;
    };

    return Cut;
});
