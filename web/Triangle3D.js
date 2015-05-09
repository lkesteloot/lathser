// Stores a 3D triangle.

'use strict';

define([], function () {
    var Triangle3D = function (v0, v1, v2) {
        this.vertices = [v0, v1, v2];

        // Compute normal.
        var e0 = v0.minus(v2);
        var e1 = v0.minus(v1);
        this.normal = e0.cross(e1);
        if (this.normal.length() != 0) {
            this.normal = this.normal.normalized();
        }
    };

    return Triangle3D;
});
