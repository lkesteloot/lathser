// Generate an Epilog PRN file for raw printing.
//
// Based on code from Ctrl-Cut by Amir Hassan <amir@viel-zu.org> and Marius
// kintel <kintel@kintel.net>.

'use strict';

define(["sprintf", "log"], function (sprintf, log) {
    // Output for the Epilog Fusion. If false then it's the Epilog Helix, which has not
    // been tested.
    var FUSION = true;

    // Match Fusion default. Max is 1200, which would give us more resolution since
    // the points are integers.
    var DPI = 600;

    var SEP = ";";

    // PJL COMMANDS

    // Printer job language header. Switch to PCL.
    var PJL_HEADER = "\x1B%%-12345X@PJL JOB NAME=%s\r\n\x1B\x45@PJL ENTER LANGUAGE=PCL \r\n";

    // End job -> go back to PJL.
    var PJL_FOOTER = "\x1B%-12345X@PJL EOJ \r\n";


    // PCL COMMANDS
    // http://en.wikipedia.org/wiki/Printer_Command_Language
    // http://h20565.www2.hp.com/hpsc/doc/public/display?docId=emr_na-bpl13210
    // http://h20565.www2.hp.com/hpsc/doc/public/display?docId=emr_na-bpl13211

    // Set color component one.
    var PCL_COLOR_COMPONENT_ONE = "\x1B*v%dA";

    // I don't know what this is. It's not in the PCL manual I found.
    var PCL_MYSTERY1 = "\x1B&y130001300003220S";

    // Probably a date, but also not in the manual. Hard-code the date,
    // not much point in setting it correctly.
    var PCL_DATESTAMP = "\x1B&y20150311204531D";

    // More mysteries.
    var PCL_MYSTERY2 = "\x1B&y0V\x1B&y0L\x1B&y0T\x1B&y0C\x1B&y0Z";
    var PCL_MYSTERY3 = "\x1B&z%dC";
    var PCL_MYSTERY4 = "\x1B&y%dR";

    // Set autofocus on or off.
    var PCL_AUTOFOCUS = "\x1B&y%dA";

    // Left (long-edge) offset registration.  Adjusts the position of the
    // logical page across the width of the page.
    var PCL_OFF_X = "\x1B&l%dU";

    // Top (short-edge) offset registration.  Adjusts the position of the
    // logical page across the length of the page.
    var PCL_OFF_Y = "\x1B&l%dZ";

    // Issued after a center engraving. Don't understand what it exactly does.
    var PCL_UPPERLEFT_X = "\x1B&l%dW";
    var PCL_UPPERLEFT_Y = "\x1B&l%dV";

    // Resolution of the print (DPI).
    var PCL_PRINT_RESOLUTION = "\x1B&u%dD";

    // PCL resolution for raster.
    var PCL_RESOLUTION = "\x1B*t%dR";

    // enable center engraving
    var PCL_CENTER_ENGRAVE = "\x1B&y%dZ";

    // enable global air assist
    var PCL_GLOBAL_AIR_ASSIST = "\x1B&y%dC";

    // Enable air assist for raster
    var PCL_RASTER_AIR_ASSIST = "\x1B&z%dA";

    // Position cursor absolute on the X-axis
    var PCL_POS_X = "\x1B*p%dX";

    // Position cursor absolute on the Y-axis
    var PCL_POS_Y = "\x1B*p%dY";

    // PCL section end
    var HPGL_START = "\x1B%1B";

    // Reset PCL
    var PCL_RESET = "\x1BE";


    // PCL RASTER COMMANDS

    // Raster Orientation
    var R_ORIENTATION = "\x1B*r%dF";

    // Raster power
    var R_POWER = "\x1B&y%dP";

    // Raster speed
    var R_SPEED = "\x1B&z%dS";

    // Bed height
    var R_BED_HEIGHT = "\x1B*r%dT";

    // Bed width
    var R_BED_WIDTH = "\x1B*r%dS";

    // Raster compression. 0 = unencoded, 1 = run length, 2 = TIFF.
    var R_COMPRESSION = "\x1B*b%dM";

    // Raster direction (0 = top-down, 1 = bottom-up)
    var R_DIRECTION = "\x1B&y%dO";

    // Start raster job
    var R_START = "\x1B*r1A";

    // End raster job
    var R_END = "\x1B*rC";

    // The number of unpacked bytes in the raster row
    var R_ROW_UNPACKED_BYTES = "\x1B*b%dA";

    // The number of packed bytes in the raster row
    var R_ROW_PACKED_BYTES = "\x1B*b%dW";


    // PCL VECTOR COMMANDS

    // Initialize vector mode
    var V_INIT = "IN";

    // Set laser pulse frequency
    if (FUSION) {
        var V_FREQUENCY = "XR%02d";
    } else {
        var V_FREQUENCY = "XR%04d";
    }

    // Set laser power
    var V_POWER = "YP%03d";

    // Set laser speed
    var V_SPEED = "ZS%03d";

    // Unknown.
    var V_UNKNOWN1 = "XS0";
    var V_UNKNOWN2 = "XP1";

    // HPGL COMMANDS
    // http://en.wikipedia.org/wiki/HPGL

    // Line Type
    // NB! The Windows driver inserts a Line Type without a parameter or
    // command terminator before the first Pen Up command. This doesn't
    // conform to PCL/HPGL and is only used on the first issue of PU in a
    // job. There seems to be no difference to using the standard command
    // also for the first issue, so I use it only because the Windows
    // driver does.

    var HPGL_LINE_TYPE = "LT";

    // Pen up
    var HPGL_PEN_UP = "PU";

    // Pen down
    var HPGL_PEN_DOWN = "PD";

    // HPGL section end
    var HPGL_END = "\x1B%0B";

    var generatePrn = function (out, doc) {
        var enableEngraving = doc.getEnableEngraving();
        var enableCut = doc.getEnableCut();
        var centerEngrave = doc.getCenterEngrave();
        var airAssist = doc.getAirAssist();

        // Match my sample output. Doesn't matter right now anyway.
        var rasterPower = 50;
        var rasterSpeed = 50;
        var width = doc.getWidth()*DPI;
        var height = doc.getHeight()*DPI;

        // Printer job language header.
        out.write(sprintf.sprintf(PJL_HEADER, doc.getTitle()));

        if (FUSION) {
            out.write(sprintf.sprintf(PCL_COLOR_COMPONENT_ONE, 1536));
            out.write(PCL_MYSTERY1);
            out.write(PCL_DATESTAMP);
            out.write(PCL_MYSTERY2);
        } else {
            // Set autofocus on or off. For some reason off is -1. I don't
            // know what on is, but we're not supposed to use it anyway.
            out.write(sprintf.sprintf(PCL_AUTOFOCUS, -1));

            // Unknown purpose.
            out.write(sprintf.sprintf(PCL_GLOBAL_AIR_ASSIST, airAssist));

            // Enable or disable center engraving.
            out.write(sprintf.sprintf(PCL_CENTER_ENGRAVE, centerEngrave));
        }

        // Left (long-edge) offset registration.  Adjusts the position of the
        // logical page across the width of the page.
        out.write(sprintf.sprintf(PCL_OFF_X, 0));

        // Top (short-edge) offset registration.  Adjusts the position of the
        // logical page across the length of the page.
        out.write(sprintf.sprintf(PCL_OFF_Y, 0));

        // Resolution of the print.
        out.write(sprintf.sprintf(PCL_PRINT_RESOLUTION, DPI));

        // X position = 0
        out.write(sprintf.sprintf(PCL_POS_X, 0));

        // Y position = 0
        out.write(sprintf.sprintf(PCL_POS_Y, 0));

        // PCL resolution.
        out.write(sprintf.sprintf(PCL_RESOLUTION, DPI));

        // Raster Orientation. 0 = logical page, 3 = physical page.
        out.write(sprintf.sprintf(R_ORIENTATION, 0));

        if (FUSION) {
            out.write(sprintf.sprintf(PCL_MYSTERY3, 0));
        }

        // Raster power
        out.write(sprintf.sprintf(R_POWER, rasterPower));

        // Raster speed
        out.write(sprintf.sprintf(R_SPEED, rasterSpeed));

        if (FUSION) {
            out.write(sprintf.sprintf(PCL_MYSTERY4, 50));

            // Set autofocus on or off. For some reason off is -1. I don't
            // know what on is, but we're not supposed to use it anyway.
            out.write(sprintf.sprintf(PCL_AUTOFOCUS, -1));
        }

        // Raster air assist.
        out.write(sprintf.sprintf(PCL_RASTER_AIR_ASSIST, airAssist ? 2 : 0));

        // Size of the bed.
        out.write(sprintf.sprintf(R_BED_HEIGHT, height));
        out.write(sprintf.sprintf(R_BED_WIDTH, width));

        // Raster compression.
        out.write(sprintf.sprintf(R_COMPRESSION, 2));

        // Do the raster passes.
        if (enableEngraving) {
            doc.eachRaster(function (raster) {
                generateRaster(out, raster);
            });
        }

        // Do the vector passes.
        if (enableCut) {
            // Header for the cut.
            out.write(HPGL_START);
            out.write(V_INIT);
            out.write(SEP);

            doc.eachCut(function (cut) {
                generateCut(out, doc, cut);
            });

            // Footer for the cut.
            out.write(HPGL_END);
        }

        out.write(HPGL_START);
        out.write(HPGL_PEN_UP);
        out.write(PCL_RESET);
        out.write(PJL_FOOTER);

        // Pad out the remainder of the file with spaces and footer.
        if (FUSION) {
            for (var i = 0; i < 4090; i++) {
                out.write(" ");
            }
            out.write("FusionKYMC");
        } else {
            for (var i = 0; i < 4092; i++) {
                out.write(" ");
            }
            out.write("Mini]\n");
        }
    };

    var generateRaster = function (out, raster) {
        // Raster direction.
        out.write(sprintf.sprintf(R_DIRECTION, 0));

        // Start this raster.
        out.write(R_START);

        // Grab raw data.
        var imageData = raster.imageData;
        var data = imageData.data;

        // Size of image.
        var width = imageData.width;
        var height = imageData.height;

        // Upper-left of image, in pixels.
        var xPixels = Math.floor(raster.x*DPI);
        var yPixels = Math.floor(raster.y*DPI);

        // Width of output image in bytes.
        var stride = Math.floor((width + 7) / 8);

        // Start left-to-right, then switch every row.
        var leftToRight = true;

        for (var row = 0; row < height; row++) {
            // We're always doing the top-down direction.
            var y = yPixels + row;

            out.write(sprintf.sprintf(PCL_POS_Y, y));
            out.write(sprintf.sprintf(PCL_POS_X, yPixels));

            // XXX Restart (R_END - DIR - START) every 388 scanlines.

            var buf = "";
            for (var byteIndex = 0; byteIndex < stride; byteIndex++) {
                var beginColumn = byteIndex*8;
                var endColumn = Math.min((byteIndex + 1)*8, width);

                var bit = 128;
                var ch = 0;
                var dataIndex = (row*width + beginColumn)*4;
                for (var column = beginColumn; column < endColumn; column++) {
                    // Just look at red for now.
                    var p = data[dataIndex];
                    if (p > 128) {
                        ch |= bit;
                    }
                    bit /= 2;
                    dataIndex += 4;
                }
                buf += String.fromCharCode(ch)
            }

            // Prepend literal length.
            buf = String.fromCharCode(buf.length - 1) + buf;

            // Pad to multiple of 8.
            while (buf.length % 8 !== 0) {
                buf += String.fromCharCode(0x80);
            }

            out.write(sprintf.sprintf(R_ROW_UNPACKED_BYTES, leftToRight ? stride : -stride));
            out.write(sprintf.sprintf(R_ROW_PACKED_BYTES, buf.length));
            out.write(buf)

            // Switch direction.
            leftToRight = !leftToRight;
        }

        // End this raster.
        out.write(R_END)
    };

    var generateCut = function (out, doc, cut) {
        // We cut the points into spans of at most 100 points.
        _.each(cut.path.breakIntoSections(100), function (path) {
            out.write(sprintf.sprintf(V_POWER, cut.power));
            out.write(SEP);
            out.write(sprintf.sprintf(V_SPEED, cut.speed));
            out.write(SEP);
            out.write(sprintf.sprintf(V_FREQUENCY, cut.frequency));
            out.write(SEP);
            out.write(V_UNKNOWN1);
            out.write(SEP);
            out.write(V_UNKNOWN2);
            out.write(SEP);
            out.write(HPGL_LINE_TYPE);

            // Move to the first point.
            var firstVertex = path.vertices[0];
            out.write(HPGL_PEN_UP);
            out.write(sprintf.sprintf("%d,%d", firstVertex.x*DPI, firstVertex.y*DPI));
            out.write(SEP);

            // Draw the rest of the points.
            out.write(HPGL_PEN_DOWN);
            var pairs = _.map(path.vertices.slice(1), function (v) {
                return sprintf.sprintf("%d,%d", v.x*DPI, v.y*DPI);
            });
            out.write(pairs.join(","));
            out.write(SEP);
        });
    };

    return {
        generatePrn: generatePrn
    };
});
