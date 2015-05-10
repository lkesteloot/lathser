// A list of Vector2 points.

'use strict';

define(["underscore"], function (_) {
    var Path = function () {
        this.vertices = [];
    };

    Path.prototype.addVertex = function (v) {
        this.vertices.push(v);
    };

    // Reverse the path in-place.
    Path.prototype.reverse = function () {
        var len = this.vertices.length;

        for (var i = 0; i < len/2; i++) {
            var tmp = this.vertices[i];
            this.vertices[i] = this.vertices[len - 1 - i];
            this.vertices[len - 1 - i] = tmp;
        }
    };

    // Return the last vertex in the path, or null if the path is empty.
    Path.prototype.getLastVertex = function () {
        if (this.vertices.length === 0) {
            return null;
        } else {
            return this.vertices[this.vertices.length - 1];
        }
    };

    Path.prototype.getLength = function () {
        return this.vertices.length;
    };

    Path.prototype.draw = function (ctx) {
        _.each(this.vertices, function (v, index) {
            if (index === 0) {
                ctx.moveTo(v.x, v.y);
            } else {
                ctx.lineTo(v.x, v.y);
            }
        });
    };

    return Path;
});
