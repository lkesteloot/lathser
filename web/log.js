// Logging facilities.

'use strict';

define([], function () {
    var startTime = null;
    var lastCall = null;

    var addTimestamp = function (message) {
        var now = new Date().getTime();

        if (startTime === null) {
            startTime = now;
            lastCall = now;
        }

        var elapsed = now - startTime;
        var sinceLast = now - lastCall;
        lastCall = now;

        // Pad to five digits.
        elapsed = "" + elapsed;
        while (elapsed.length < 5) {
            elapsed = " " + elapsed;
        }

        sinceLast = "+" + sinceLast;
        while (sinceLast.length < 5) {
            sinceLast = " " + sinceLast;
        }

        return elapsed + " (" + sinceLast + "): " + message;
    };

    var info = function (message) {
        message = addTimestamp(message);
        if (console.info) {
            console.info(message);
        } else {
            console.log(message);
        }
    };

    var warn = function (message) {
        message = addTimestamp(message);
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
