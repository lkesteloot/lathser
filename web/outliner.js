// Algorithms for generating outlines from a raster image.

'use strict';

define(["underscore", "log", "Vector2", "Hashtable", "Path", "Paths"], function (_, log, Vector2, Hashtable, Path, Paths) {
    // Two Vector2 objects representing an edge of the object.
    var Edge = function (v1, v2) {
        this.v1 = v1;
        this.v2 = v2;

        // Flag for whether we've used this edge in the path-building algorithm.
        this.used = false;
    };

    Edge.prototype.hashCode = function () {
        // Don't hash "used", that's not part of the value.

        // From Effective Java:
        var result = 17;
        result = 37*result + this.v1.hashCode();
        result = 37*result + this.v2.hashCode();
        return result;
    };

    Edge.prototype.equals = function (other) {
        // Don't compare "used", that's not part of the value.
        return this.v1.equals(other.v1) && this.v2.equals(other.v2);
    };

    Edge.prototype.toString = function () {
        return "Edge[" + this.v1.toString() + "," + this.v2.toString() + "]";
    };

    // Utility functions for filtering.
    var edgeIsNotUsed = function (edge) {
        return !edge.used;
    };

    // Returns a Paths objects.
    var findOutlines = function (render) {
        // Array of Edge objects found in the image.
        var edges = [];

        // Generate edges for each pixel.
        log.info("Generating edges...");
        var width = render.canvas.width;
        var height = render.canvas.height;
        var data = render.ctx.getImageData(0, 0, width, height).data;
        var bytesPerPixel = 4;
        var xxx = width*bytesPerPixel;

        for (var y = 0; y < height - 1; y++) {
            var thisPixel = y*xxx;
            var rightPixel = thisPixel + bytesPerPixel;
            var downPixel = thisPixel + xxx;

            for (var x = 0; x < width - 1; x++) {
                // Don't compare alpha.
                if (data[thisPixel] != data[rightPixel] ||
                    data[thisPixel + 1] != data[rightPixel + 1] ||
                    data[thisPixel + 2] != data[rightPixel + 2]) {

                    edges.push(new Edge(new Vector2(x + 1, y), new Vector2(x + 1, y + 1)));
                }
                if (data[thisPixel] != data[downPixel] ||
                    data[thisPixel + 1] != data[downPixel + 1] ||
                    data[thisPixel + 2] != data[downPixel + 2]) {

                    edges.push(new Edge(new Vector2(x, y + 1), new Vector2(x + 1, y + 1)));
                }

                thisPixel += bytesPerPixel;
                rightPixel += bytesPerPixel;
                downPixel += bytesPerPixel;
            }
        }

        log.info("Made " + edges.length + " edges.")
        if (edges.length === 0) {
            log.warn("Found no pixels in image.");
            return [];
        }

        if (false) {
            render.ctx.save();
            render.ctx.strokeStyle = "red";
            render.ctx.lineWidth = 5;
            _.each(edges, function (edge) {
                render.ctx.beginPath();
                render.ctx.moveTo(edge.v1.x, edge.v1.y);
                render.ctx.lineTo(edge.v2.x, edge.v2.y);
                render.ctx.stroke();
            });
            render.ctx.restore();
        }

        // Put into a hash by the edges.
        log.info("Hashing edges...");

        // Map from Vector2 to list of Edge objects that include that vertex.
        var edgeMap = new Hashtable();

        _.each(edges, function (edge) {
            _.each([edge.v1, edge.v2], function (v) {
                var list = edgeMap.get(v);
                if (list === null) {
                    list = [];
                    edgeMap.put(v, list);
                }

                list.push(edge);
            });
        });
        log.info("Found " + edgeMap.size() + " unique vertices.");

        // Walk around, starting at any edge.
        log.info("Making sequence of vertices...");
        var paths = new Paths();

        // Current path.
        var path = new Path();
        paths.addPath(path);
        var edge = edges[0];
        path.addVertex(edge.v1);

        // Vertex we're following.
        var vertex = edge.v2;
        while (true) {
            edge.used = true;
            path.addVertex(vertex);

            // Include edges connected to this vertex but that we've not used before.
            var connectedEdges = _.filter(edgeMap.get(vertex), edgeIsNotUsed);

            if (connectedEdges.length === 0) {
                // End of this path.

                // Remove used edges from our list.
                edges = _.filter(edges, edgeIsNotUsed);
                if (edges.length === 0) {
                    // No more vertices to add.
                    break;
                }

                // Done on this end. See if we can continue on the other end, in case
                // it's not a closed path.
                path.reverse();

                vertex = path.getLastVertex();
                connectedEdges = _.filter(edgeMap.get(vertex), edgeIsNotUsed);
            }

            if (connectedEdges.length === 0) {
                // Start new path.
                path = new Path();
                paths.addPath(path);
                edge = edges[0];
                path.addVertex(edge.v1);
                vertex = edge.v2;
            } else {
                // Extend current path.
                edge = connectedEdges[0];
                if (edge.v1.equals(vertex)) {
                    vertex = edge.v2;
                } else {
                    vertex = edge.v1;
                }
            }
        }

        // Log results.
        edges = _.filter(edges, edgeIsNotUsed);
        log.info("Sequence has " + paths.getLength() + " paths (" + paths.pathLengths() + "), with " + edges.length + " edges unused.");

        return paths;
    };

    return {
        findOutlines: findOutlines
    };
});
