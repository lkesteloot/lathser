// A list of Vector2 points.

'use strict';

define(["underscore"], function (_) {
    var Path = function (vertices) {
        this.vertices = vertices || [];
    };

    Path.prototype.addVertex = function (v) {
        this.vertices.push(v);
    };

    Path.prototype.addPath = function (other) {
        Array.prototype.push.apply(this.vertices, other.vertices);
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

    Path.prototype.deleteLastVertex = function () {
        this.vertices.splice(this.vertices.length - 1, 1);
    };

    // Returns a new Path with the vertices from first to last inclusive.
    Path.prototype.subPath = function (first, last) {
        return new Path(this.vertices.slice(first, last + 1));
    };

    // Returns a new path with the vertices transformed.
    Path.prototype.transform = function (transform) {
        return new Path(_.map(this.vertices, function (v) {
            return transform.transform(v);
        }));
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

    // Given points v1 and v2 and point v, returns the distance from v to the line v1,v2.
    var distanceToLine = function (v, v1, v2) {
        var segment = v1.minus(v2);
        var n = segment.reciprocal().normalized();
        return Math.abs(v.minus(v1).dot(n));
    };

    // Given a distance, returns a new Path with vertices removed if they add
    // less than epsilon of detail.
    Path.prototype.simplify = function (epsilon) {
        // http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm

        // Find the point with the maximum distance
        var maxDist = 0;
        var maxIndex = 0;
        var first = 0;
        var last = this.vertices.length - 1;

        for (var i = first + 1; i <= last - 1; i++) {
            var dist;

            if (this.vertices[first].equals(this.vertices[last])) {
                // If this is a closed path, then we can't compute the line between the
                // first and last vertex. Just check the distance to the vertex.
                dist = this.vertices[i].minus(this.vertices[first]).length();
            } else {
                dist = distanceToLine(this.vertices[i], this.vertices[first], this.vertices[last]);
            }

            if (dist > maxDist) {
                maxIndex = i;
                maxDist = dist;
            };
        }

        // Create the new simplified path.
        var path = new Path();

        // If max distance is greater than epsilon, recursively simplify.
        if (maxDist > epsilon) {
            // Recursive call
            var firstHalf = this.subPath(first, maxIndex).simplify(epsilon);
            var secondHalf = this.subPath(maxIndex, last).simplify(epsilon);

            // Skip the duplicate middle vertex.
            firstHalf.deleteLastVertex();

            // Add the two sub-problems together.
            path.addPath(firstHalf);
            path.addPath(secondHalf);
        } else {
            // None are far enough, just keep the ends.
            path.addVertex(this.vertices[first]);
            path.addVertex(this.vertices[last]);
        };

        return path;
    };

    // Useful for mapping.
    Path.pathLength = function (path) {
        return path.getLength();
    };

    return Path;
});
