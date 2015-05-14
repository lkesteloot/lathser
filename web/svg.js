// Generate an SVG file for importing into Illustrator.

'use strict';

define(["sprintf", "log"], function (sprintf, log) {
    // "Hairline" in AI.
    var STROKE_WIDTH = 0.001;
    var FOREGROUND_COLOR = "black";
    var BACKGROUND_COLOR = "white";

    // Dots per inch in the SVG file. Don't change this.
    var DPI = 72;

    var generateSvg = function (out, doc) {
        var width = doc.getWidth()*DPI;
        var height = doc.getHeight()*DPI;

        out.write(sprintf.sprintf('<?xml version="1.0" encoding="utf-8"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd" [<!ENTITY ns_svg "http://www.w3.org/2000/svg">]><svg xmlns="&ns_svg;" width="%d" height="%d" overflow="visible" style="background: %s">\n', width, height, BACKGROUND_COLOR));

        doc.eachCut(function (cut) {
            out.write(sprintf.sprintf('<polyline fill="none" stroke="%s" stroke-width="%g" points="', FOREGROUND_COLOR, STROKE_WIDTH));
            _.each(cut.path.vertices, function (v) {
                out.write(sprintf.sprintf(" %.1f,%.1f", v.x*DPI, v.y*DPI));
            });
            out.write('"/>\n')
        });
        out.write('</svg>');
    }

    return {
        generateSvg: generateSvg
    };
});

