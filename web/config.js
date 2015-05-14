// Configuration parameters.

'use strict';

define([], function () {
    // Make this negative if the zero point is off the bed, positive
    // if it's inside the bed.
    var LASER_OFFSET_X = -0.034;
    var LASER_OFFSET_Y = 0.041;

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
        FINAL_Y: 1 - LASER_OFFSET_Y,

        // The radius of the laser kerf, in inches.
        KERF_RADIUS_IN: 0.002,

        // Extra spacing for rough cuts, in inches.
        ROUGH_EXTRA_IN: 1/16.0,

        PASS_SHADES: [80, 40, 0],

        // Number of cuts around the circle.
        ANGLE_COUNT: 16
    };

    config.MODEL_DIAMETER = config.ROD_DIAMETER*(1 - config.MARGIN);

    return config;
});
