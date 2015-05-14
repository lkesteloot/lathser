// A list of Path objects.

'use strict';

define(["underscore", "log", "Path"], function (_, log, Path) {
    var Paths = function (paths) {
        this.paths = paths || [];
    };

    Paths.prototype.addPath = function (path) {
        this.paths.push(path);
    };

    Paths.prototype.each = function (callback) {
        _.each(this.paths, callback);
    };

    Paths.prototype.getLength = function () {
        return this.paths.length;
    };

    Paths.prototype.pathLengths = function () {
        return _.map(this.paths, Path.pathLength).join(", ");
    };

    Paths.prototype.simplify = function (epsilon) {
        this.paths = _.map(this.paths, function (path) {
            return path.simplify(epsilon);
        });
        log.info("Number of vertices after simplification: " + this.pathLengths());
    };

    // Return a new Paths transformed by the inverse of the transform.
    Paths.prototype.transformInverse = function (transform, scale, x, y) {
        // Compute the inverse transform.
        var transform = transform.invert();

        // Scale to final size.
        var transform = transform.scaled(scale);

        // Move to right position.
        var transform = transform.translated(x, y);

        return new Paths(_.map(this.paths, function (path) {
            return path.transform(transform);
        }));
    };

    Paths.prototype.draw = function (ctx) {
        ctx.save();
        ctx.strokeStyle = "red";
        ctx.lineWidth = 5;
        _.each(this.paths, function (path) {
            ctx.beginPath();
            path.draw(ctx);
            ctx.stroke();
        });
        ctx.restore();
    };

    return Paths;
});
