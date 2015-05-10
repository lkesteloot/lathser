// Computes and stores a rendered image.

'use strict';

define(["log", "BoundingBox2D", "Transform"], function (log, BoundingBox2D, Transform) {
    var Render = function (canvas, ctx, transform) {
        this.canvas = canvas;
        this.ctx = ctx;
        this.transform = transform;
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
