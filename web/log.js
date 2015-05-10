// Logging facilities.

'use strict';

define([], function () {
    var info = function (message) {
        if (console.info) {
            console.info(message);
        } else {
            console.log(message);
        }
    };

    var warn = function (message) {
        if (console.warn) {
            console.warn(message);
        } else {
            console.log(message);
        }
    };

    return {
        info: info,
        warn: warn
    };
});
