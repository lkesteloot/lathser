// A list of Path objects.

'use strict';

define(["underscore", "log", "Path"], function (_, log, Path) {
    var Paths = function () {
        this.paths = [];
    };

    Paths.prototype.addPath = function (path) {
        this.paths.push(path);
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
