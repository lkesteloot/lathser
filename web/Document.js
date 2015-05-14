// Encapsulates a document to be printed to the laser printer.

'use strict';

define([], function () {
    var Document = function (title) {
        this.title = title;
        this.cuts = [];
        this.rasters = [];
    };

    // Add a Cut object.
    Document.prototype.addCut = function (cut) {
        this.cuts.push(cut);
    };

    // Add a Raster object.
    Document.prototype.addRaster = function (raster) {
        this.rasters.push(raster);
    };

    // Whether this doc has engravings (raster).
    Document.prototype.getEnableEngraving = function () {
        return this.rasters.length > 0;
    };

    // Whether this doc has cuts (vector).
    Document.prototype.getEnableCut = function () {
        return this.cuts.length > 0;
    };

    Document.prototype.getCenterEngrave = function () {
        // We never center anything automatically.
        return false;
    };

    Document.prototype.getAirAssist = function () {
        // I assume we always want this on. If this is the air pipe aimed
        // right at the cut, then perhaps we could turn this off to reduce
        // charring.
        return true;
    };

    // Bed size in inches.
    Document.prototype.getWidth = function () {
        return 32;
    };

    // Bed size in inches.
    Document.prototype.getHeight = function () {
        return 20;
    };

    Document.prototype.getAutoFocus = function () {
        // We never want this.
        return false;
    };

    Document.prototype.getTitle = function () {
        return this.title;
    };

    Document.prototype.getCuts = function () {
        return this.cuts;
    };

    Document.prototype.getRasters = function () {
        return this.rasters;
    };

    Document.prototype.eachCut = function (callback) {
        _.each(this.cuts, callback);
    };

    Document.prototype.eachRaster = function (callback) {
        _.each(this.rasters, callback);
    };

    Document.prototype.addPaths = function (paths) {
        _.each(paths, function (path) {
            this.addPath(path);
        }.bind(this));
    };

    /*
    Document.prototype.addPath = function (path) {
        cut = Cut(4, 100, 50)
        # Convert to doc's resolution.
        cut.points = [Vector2(p.x*dpi/DPI, p.y*dpi/DPI) for p in path]
        doc.addCut(cut)
    };
    */

    return Document;
});
