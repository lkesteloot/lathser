
'use strict';

require.config({
    urlArgs: "bust=" + (new Date()).getTime(),
    paths: {
        "jquery": "vendor/jquery-2.1.4.min",
        "underscore": "vendor/underscore-1.8.2.min"
    }
});

require(["jquery", "log", "Model"], function ($, log, Model) {
    var $canvas = $("canvas");

    Model.load("models/new_knight_baseclean_sym.json", function (model) {
        log.info("Successfully loaded model");
        log.info(model);
    }, function (error) {
        log.warn("Error loading model:", error);
    });
});
