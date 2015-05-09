// Stores a 3D triangle.

'use strict';

define(["underscore", "Triangle2D"], function (_, Triangle2D) {
    var Triangle3D = function (vertices) {
        this.vertices = vertices;

        // Compute normal.
        var v0 = vertices[0];
        var v1 = vertices[1];
        var v2 = vertices[2];
        var e0 = v0.minus(v2);
        var e1 = v0.minus(v1);
        this.normal = e0.cross(e1);
        if (this.normal.length() != 0) {
            this.normal = this.normal.normalized();
        }
    };

    // Rotate this 3D triangle by angle, transform it, project it onto 2D, and return
    // a 2D triangle.
    Triangle3D.prototype.project = function (transform, angle) {
        return new Triangle2D(_.map(this.vertices, function (vertex) {
            return vertex.project(transform, angle);
        }));
    };

    // Return a copy of the triangle rotated 90 degrees around the X axis. This
    // is for converting models from around-Y to around-Z.
    Triangle3D.prototype.rotateX90 = function () {
        return new Triangle3D(_.map(this.vertices, function (vertex) {
            return vertex.rotateX90();
        }));
    };

    return Triangle3D;
});
