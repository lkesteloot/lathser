// Stores a 3D bounding box.

'use strict';

define(["underscore", "Vector3"], function (_, Vector3) {
    var BoundingBox3D = function () {
        this.min = new Vector3(Number.MAX_VALUE, Number.MAX_VALUE, Number.MAX_VALUE);
        this.max = new Vector3(-Number.MAX_VALUE, -Number.MAX_VALUE, -Number.MAX_VALUE);
    };

    BoundingBox3D.prototype.addPoint = function (v) {
        this.min = this.min.min(v);
        this.max = this.max.max(v);
    };

    BoundingBox3D.prototype.addTriangle = function (triangle) {
        _.each(triangle.vertices, function (vertex) {
            this.addPoint(vertex);
        }.bind(this));
    };

    BoundingBox3D.prototype.size = function () {
        return this.max.minus(this.min);
    };

    BoundingBox3D.prototype.center = function () {
        return this.min.plus(this.size().dividedBy(2));
    };

    BoundingBox3D.prototype.toString = function () {
        return "BBOX([" + this.min.toStringTerse() + "] - [" + this.max.toStringTerse() + "])";
    };

    return BoundingBox3D;
});
