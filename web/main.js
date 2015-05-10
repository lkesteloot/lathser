
'use strict';

require.config({
    urlArgs: "bust=" + (new Date()).getTime(),
    paths: {
        "jquery": "vendor/jquery-2.1.4.min",
        "underscore": "vendor/underscore-min",
        "Hashtable": "vendor/Hashtable"
    }
});

require(["jquery", "log", "Model", "Render", "Vector3", "outliner", "config"], function ($, log, Model, Render, Vector3, outliner, config) {
    var $canvas = $("canvas");

    Model.load("models/new_knight_baseclean_sym.json", function (model) {
        log.info("Successfully loaded model");
        log.info(model);

        var bbox3d = model.getBoundingBox();
        var center = bbox3d.center();

        // Move center to origin.
        model.translate(center.negated());

        // Find scaling factor.
        var size = bbox3d.size();
        var maxSize = Math.max(size.x, size.y);
        var scale = config.MODEL_DIAMETER / maxSize * config.DPI;

        var light = (new Vector3(-1, 1, 1)).normalized();
        var render = Render.make(model, 1024, 1024, 0, null);
        var paths = outliner.findOutlines(render);
        paths.simplify(1);
        paths.draw(render.ctx);
        paths = paths.transformInverse(render.transform, scale,
                                       config.FINAL_X*config.DPI,
                                       config.FINAL_Y*config.DPI);

        $("body").append(render.canvas);
    }, function (error) {
        log.warn("Error loading model: " + error);
    });
});
