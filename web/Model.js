// Stores 3D model.

'use strict';

define(["jquery", "underscore", "log", "Triangle3D", "Vector3", "BoundingBox3D"], function ($, _, log, Triangle3D, Vector3, BoundingBox3D) {
    var Model = function (triangles) {
        this.triangles = triangles;
    };

    Model.prototype.getBoundingBox = function () {
        var bbox3d = new BoundingBox3D();
        _.each(this.triangles, function (triangle) {
            bbox3d.addTriangle(triangle);
        });
        return bbox3d;
    };

    // Translate the model in-place by the Vector3.
    Model.prototype.translate = function (v) {
        this.triangles = _.map(this.triangles, function (triangle) {
            return triangle.translate(v);
        });
    };

    /**
     * The success callback is passed a Model object. The error callback is passed
     * a string.
     */
    Model.load = function (pathname, successCallback, errorCallback) {
        log.info("Loading " + pathname);

        $.ajax(pathname, {
            dataType: "json",
            success: function (data) {
                var model = Model.parseJson(data);
                successCallback(model);
            },
            error: function (xhr, textStatus) {
                errorCallback(textStatus);
            }
        });
    };

    Model.parseJson = function (data) {
        var triangles = [];

        // We don't care about meshes, so we just generate a single
        // list of triangles.
        _.each(data.meshes, function (mesh) {
            var rawVertices = mesh.vertices;
            var rawNormals = mesh.normals; // Not used.
            var rawFaces = mesh.faces;

            var vertices = [];

            for (var i = 0; i < rawVertices.length/3; i++) {
                var v = new Vector3(
                    rawVertices[i*3 + 0],
                    rawVertices[i*3 + 1],
                    rawVertices[i*3 + 2]);
                vertices.push(v);
            }

            Array.prototype.push.apply(triangles, _.map(rawFaces, function (face) {
                return new Triangle3D([
                    vertices[face[0]],
                    vertices[face[1]],
                    vertices[face[2]]]);
            }));
        });

        // XXX Model-dependant. Not sure where to store this.
        var rotationCount = 3;
        // We need the model to be around Z. If it's around Y, transform
        // the initial geometry so that the rest of the program doesn't
        // have to concern itself with it.
        _.times(rotationCount, function () {
            triangles = _.map(triangles, function (triangle) {
                return triangle.rotateX90();
            });
        });

        return new Model(triangles);
    };

    return Model;
});
