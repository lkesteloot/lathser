
'use strict';

require.config({
    urlArgs: "bust=" + (new Date()).getTime(),
    paths: {
        "jquery": "vendor/jquery-2.1.4.min",
        "underscore": "vendor/underscore-min"
    }
});

require(["jquery", "log", "Model", "Render", "Vector3"], function ($, log, Model, Render, Vector3) {
    var $canvas = $("canvas");

    Model.load("models/new_knight_baseclean_sym.json", function (model) {
        log.info("Successfully loaded model");
        log.info(model);

        var light = (new Vector3(-1, 1, 1)).normalized();
        var render = Render.make(model, 1024, 1024, 0, light);
        $("body").append(render.canvas);
    }, function (error) {
        log.warn("Error loading model:", error);
    });
});