// Configuration parameters.

'use strict';

define([], function () {
    var LASER_OFFSET_X = -0.031;

    var config = {
        // Dots per inch in the SVG file. Don't change this.
        DPI: 72,

        // Diameter of rod in inches.
        ROD_DIAMETER: 0.8,

        // Total margin within rod as a fraction of the diameter.
        MARGIN: 0.1,

        // Final position of model in inches. The rig centers
        // the rod at 1.25 inches from the left.
        FINAL_X: 1.25 - LASER_OFFSET_X,
        FINAL_Y: 1
    };

    config.MODEL_DIAMETER = config.ROD_DIAMETER*(1 - config.MARGIN);

    return config;
});
