
'use strict';

require.config({
    urlArgs: "bust=" + (new Date()).getTime(),
    paths: {
        "jquery": "vendor/jquery-2.1.4.min",
        "underscore": "vendor/underscore-min",
        "Hashtable": "vendor/Hashtable",
        "sprintf": "vendor/sprintf"
    }
});

require(["jquery", "log", "Model", "Render", "Vector3", "outliner", "config", "Document", "Cut", "epilog", "Buffer"], function ($, log, Model, Render, Vector3, outliner, config, Document, Cut, epilog, Buffer) {

    // Return "count" angles (in radians) going around the circle.
    var angles = function (count) {
        return _.times(count, function (angle) {
            return angle*Math.PI*2/count;
        });
    };

    // Return the first half of the list.
    var halfList = function (list) {
        return list.slice(0, list.length/2);
    };

    var generatePasses = function (callback) {
        _.each(config.PASS_SHADES, function (shadePercent) {
            _.each(halfList(angles(config.ANGLE_COUNT)), function (angle) {
                callback(shadePercent, angle);
            });
        });
    };

    Model.load("models/new_knight_baseclean_sym.json", function (model) {
        log.info("Successfully loaded model");

        var bbox3d = model.getBoundingBox();
        var center = bbox3d.center();

        // Move center to origin.
        model.translate(center.negated());

        // Find scaling factor.
        var size = bbox3d.size();
        var maxSize = Math.max(size.x, size.y);
        var scale = config.MODEL_DIAMETER / maxSize * config.DPI;

        var light = (new Vector3(-1, 1, 1)).normalized();
        var doc = new Document("untitled");
        var dpi = doc.getResolution();
        var angle = 0; // Use 0.73 to make a hole.

        generatePasses(function (shadePercent, angle) {
            var render = Render.make(model, 1024, 1024, angle, null);
            render.addBase();

            // Add the shade (for spiraling). The "transform" converts from
            // model units to raster coordinates. "scale" converts from
            // model units to dots. DPI converts from inches to dots.
            var shadeWidth = config.ROD_DIAMETER*shadePercent/100.0*render.transform.scale/scale*config.DPI;
            var shadeCenterX = render.transform.offx;
            render.addShade(shadeWidth, shadeCenterX);

            // Expand to take into account the kerf.
            var kerfRadius = config.KERF_RADIUS_IN*render.transform.scale/scale*config.DPI
            if (shadePercent != 0 && false) {
                // Rough cut, add some spacing so we don't char the wood.
                kerfRadius += config.ROUGH_EXTRA_IN*render.transform.scale/scale*config.DPI
            }
            render.addKerf(kerfRadius);

            // Cut off the sides when we're shading.
            if (shadePercent > 0) {
                render.setTop(2);
            }

            var paths = outliner.findOutlines(render);
            paths.simplify(1);
            paths.draw(render.ctx);
            paths = paths.transformInverse(render.transform, scale,
                                           config.FINAL_X*config.DPI,
                                           config.FINAL_Y*config.DPI);

            $("body").append(render.canvas);

            paths.each(function (path) {
                var cut = new Cut(path, 4, 100, 50);
                doc.addCut(cut);
            });
        });

        var buf = new Buffer();
        epilog.generatePrn(buf, doc);
        var $a = $("<a>").attr("download", "out.prn").attr("href", buf.toDataUri("application/octet-stream")).text("Click to download PRN file");
        $("body").append($a);
    }, function (error) {
        log.warn("Error loading model: " + error);
    });
});
