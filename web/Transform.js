// Represents a 2D transformation (scale and translation).

'use strict';

define(["Vector2"], function (Vector2) {
    // The transform takes model coordinate (x,y) and computes (x*scale + offx,
    // y*scale+offy).
    var Transform = function (scale, offx, offy) {
        this.scale = scale;
        this.offx = offx;
        this.offy = offy;
    };

    Transform.prototype.toString = function () {
        return "Trans[" + this.scale + ",(" + this.offx + "," + this.offy + ")]";
    };

    // Transform a Vector2 to another Vector2.
    Transform.prototype.transform = function (v) {
        return new Vector2(v.x*this.scale + this.offx, v.y*this.scale + this.offy);
    };

    // Create a new transformation that's the inverse of this one.
    Transform.prototype.invert = function () {
        // x' = x*scale + offx
        // x' - offx = x*scale
        // x = (x' - offx)/scale
        // x = x'/scale - offx/scale
        return new Transform(1.0/this.scale, -this.offx/this.scale, -this.offy/this.scale);
    };

    // Create a new transformation that's scaled.
    Transform.prototype.scaled = function (scale) {
        return new Transform(this.scale*scale, this.offx*scale, this.offy*scale);
    };

    // Create a new transformation that's translated.
    Transform.prototype.translated = function (dx, dy) {
        return new Transform(this.scale, this.offx + dx, this.offy + dy)
    };

    // Create a Transform that maps from the bbox to the width and height.
    Transform.makeMap = function (bbox, width, height) {
        var size = bbox.size();

        var scale;
        if (size.x/size.y < width/height) {
            // Left/right margins. Fit height.
            scale = height/size.y;
        } else {
            // Bottom/top margins. Fit width.
            scale = width/size.x;
        }

        var offset = (new Vector2(width, height)).dividedBy(2).minus(bbox.center().times(scale));

        return new Transform(scale, offset.x, offset.y);
    };

    // Create a no-op transformation.
    Transform.makeIdentity = function () {
        return new Transform(1, 0, 0);
    };

    return Transform;
});
