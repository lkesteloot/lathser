// Computes and stores a rendered image.

'use strict';

define(["log", "sprintf", "BoundingBox2D", "Transform"], function (log, sprintf, BoundingBox2D, Transform) {
    var Render = function (canvas, ctx, transform) {
        this.canvas = canvas;
        this.ctx = ctx;
        this.transform = transform;
    };

    // Return the height below the object where there are no on pixels.
    Render.prototype.getBaseHeight = function () {
        var width = this.canvas.width;
        var height = this.canvas.height;
        var data = this.ctx.getImageData(0, 0, width, height).data;
        var bytesPerPixel = 4;
        var stride = width*bytesPerPixel;

        for (var y = 0; y < height; y++) {
            var i = (height - 1 - y)*stride;
            for (var x = 0; x < width; x++) {
                if (data[i] !== 0 || data[i + 1] !== 0 || data[i + 2] !== 0) {
                    return y;
                }
                i += bytesPerPixel;
            }
        }

        throw "Base not found";
    };

    // Modify the image in-place to add a base to the bottom of it.
    Render.prototype.addBase = function () {
        var width = this.canvas.width;
        var height = this.canvas.height;
        var baseHeight = this.getBaseHeight();
        log.info("Base height is " + baseHeight + " pixels.");

        this.ctx.save();
        this.ctx.fillStyle = "white";
        this.ctx.fillRect(0, height - baseHeight, width, baseHeight);
        this.ctx.restore();
    };

    // Draw a rectangle of width "shadeWidth" down the middle of the image
    // so we can spiral into the rod.
    Render.prototype.addShade = function (shadeWidth, shadeCenterX) {
        var height = this.canvas.height;
        var startX = shadeCenterX - shadeWidth/2

        this.ctx.save();
        this.ctx.fillStyle = "white";
        this.ctx.fillRect(startX, 0, shadeWidth, height);
        this.ctx.restore();
    };

    // Set the top "size" pixels of the image to the specified color.
    Render.prototype.setTop = function (size, color) {
        var width = this.canvas.width;

        this.ctx.save();
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, width, size);
        this.ctx.restore();
    };

    // Extend the shape in the image by the radius.
    Render.prototype.addKerf = function (radius) {
        log.info(sprintf.sprintf("Adding kerf of radius %.2f", radius));

        var width = this.canvas.width;
        var height = this.canvas.height;
        var imageData = this.ctx.getImageData(0, 0, width, height);

        // Make a copy of the original image.
        var canvasCopy = document.createElement("canvas");
        canvasCopy.width = width;
        canvasCopy.height = height;
        var ctxCopy = canvasCopy.getContext("2d");
        ctxCopy.putImageData(imageData, 0, 0);

        // Draw the original image in a circle. This won't work
        // for very thin lines or points. We could fill in the
        // circle if we wanted.
        for (var t = 0; t < 2*Math.PI; t += 0.1) {
            var dx = Math.cos(t)*radius;
            var dy = Math.sin(t)*radius;
            this.ctx.drawImage(canvasCopy, dx, dy);
        }

        // Get another dump. This can take a while if the above operations
        // are still queued up and we want to count all that are part of
        // our own time.
        imageData = this.ctx.getImageData(0, 0, width, height);

        log.info("Finished adding kerf");
    };

    // Return a Render object of the model in an image of the width and
    // height specified.  The triangles are rotated by angle around the Z axis.
    // If the "light" 3D vector is not null, the triangles are lit by a light
    // pointed to by that vector.
    Render.make = function (model, width, height, angle, light) {
        log.info("Rendering at angle " + Math.floor(angle*180/Math.PI));

        var bbox = new BoundingBox2D();

        var transform = Transform.makeIdentity();

        _.each(model.triangles, function (triangle) {
            var triangle2d = triangle.project(transform, angle);
            bbox.addTriangle(triangle2d);
        });

        // Pad so we don't run into the edge of the image.
        bbox.addMargin(bbox.size().x/10);

        // Map from object bounding box to raster size.
        transform = Transform.makeMap(bbox, width, height);

        // Create image.
        var canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        var ctx = canvas.getContext("2d");

        // Draw the triangles.
        _.each(model.triangles, function (triangle) {
            var triangle2d = triangle.project(transform, angle);

            var color;
            if (light !== null) {
                // Remove backfacing triangles.
                if (triangle.normal.x > 0) {
                    return;
                }

                // Compute diffuse component of lighting.
                var diffuse = triangle.normal.dot(light);
                if (diffuse < 0) {
                    diffuse = 0;
                }

                // Convert to pixel value.
                color = Math.floor(diffuse*255 + 0.5);
            } else {
                color = 255;
            }

            ctx.fillStyle = "rgb(" + color + ", " + color + ", " + color + ")";
            ctx.strokeStyle = ctx.fillStyle;
            ctx.beginPath();
            ctx.moveTo(triangle2d.vertices[0].x, triangle2d.vertices[0].y);
            ctx.lineTo(triangle2d.vertices[1].x, triangle2d.vertices[1].y);
            ctx.lineTo(triangle2d.vertices[2].x, triangle2d.vertices[2].y);
            ctx.fill();
            ctx.stroke();
        });

        return new Render(canvas, ctx, transform);
    };

    return Render;
});
