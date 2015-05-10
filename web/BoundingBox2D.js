// Stores a 2D bounding box.

'use strict';

define(["underscore", "Vector2"], function (_, Vector2) {
    var BoundingBox2D = function () {
        this.min = new Vector2(Number.MAX_VALUE, Number.MAX_VALUE);
        this.max = new Vector2(-Number.MAX_VALUE, -Number.MAX_VALUE);
    };

    BoundingBox2D.prototype.addPoint = function (v) {
        this.min = this.min.min(v);
        this.max = this.max.max(v);
    };

    BoundingBox2D.prototype.addTriangle = function (triangle) {
        _.each(triangle.vertices, function (vertex) {
            this.addPoint(vertex);
        }.bind(this));
    };

    BoundingBox2D.prototype.addMargin = function (margin) {
        this.min.x -= margin;
        this.min.y -= margin;
        this.max.x += margin;
        this.max.y += margin;
    };

    BoundingBox2D.prototype.size = function () {
        return this.max.minus(this.min);
    };

    BoundingBox2D.prototype.center = function () {
        return this.min.plus(this.size().dividedBy(2));
    };

    BoundingBox2D.prototype.toString = function () {
        return "BBOX([" + this.min.x + "," + this.min.y + "] - [" + this.max.x + "," + this.max.y + "])";
    };

    return BoundingBox2D;
});
