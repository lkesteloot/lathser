
'use strict';

require.config({
    urlArgs: "bust=" + (new Date()).getTime(),
    shim: {
        "three": {
            exports: "THREE"
        }
    },
    paths: {
        "jquery": "vendor/jquery-2.1.4.min",
        "underscore": "vendor/underscore-min",
        "Hashtable": "vendor/Hashtable",
        "sprintf": "vendor/sprintf",
        "three": "vendor/three.min"
    }
});

require(["jquery", "underscore", "log", "Model", "Render", "Vector3", "outliner", "config", "Document", "Cut", "epilog", "Buffer", "svg", "Path", "Vector2", "three", "Raster"], function ($, _, log, Model, Render, Vector3, outliner, config, Document, Cut, epilog, Buffer, svg, Path, Vector2, THREE, Raster) {

    var start = function (svgOutput) {
        // Return "count" angles (in radians) going around the circle.
        var angles = function (count) {
            return _.times(count, function (angle) {
                return angle*Math.PI*2/count;
            });
        };

        // Return the first half of the list.
        var halfList = function (list) {
            return list.slice(0, list.length/2);
        };

        // Return a list of {value, isLast} objects; isLast is true only for the last item.
        var identifyLast = function (list) {
            return _.map(list, function (value, index) {
                return {
                    value: value,
                    isLast: index === list.length - 1
                };
            });
        };

        var generatePasses = function (callback) {
            if (svgOutput) {
                // Left and right face only.
                callback(0, 0, false);
                callback(0, Math.PI, false);
            } else {
                // Whole thing.
                _.each(config.PASS_SHADES, function (shadePercent) {
                    _.each(identifyLast(halfList(angles(config.ANGLE_COUNT))), function (data) {
                        callback(shadePercent, data.value, data.isLast);
                    });
                });
            }
        };

        // Go to the spot that indicates to the hardware that it should advance to
        // the next step.
        var makeHeatSensorCut = function () {
            var x = 3.0;
            var y = 2.5;

            var path = new Path([
                new Vector2(x, y - 2/72.),
                new Vector2(x, y)
            ]);

            return new Cut(path, 4, 100, 50);
        };

        var makeTimeWasterCut = function (longDelay) {
            var cx = 10;
            var cy = 2.5;
            var radius = 0.125;
            var pointCount = 10;
            var speed = longDelay ? 2 : 4;

            var path = new Path();

            _.times(pointCount + 1, function (i) {
                var t = i/pointCount*Math.PI*2;
                var x = cx + Math.cos(t)*radius;
                var y = cy + Math.sin(t)*radius;
                path.addVertex(new Vector2(x, y));
            });

            return new Cut(path, speed, 1, 50);
        };

        var filename;
        var rotationCount;

        filename = "DNA.json"; rotationCount = 2;
        filename = "new_knight_baseclean_sym.json"; rotationCount = 3;

        Model.load("models/" + filename, rotationCount, function (model) {
            log.info("Successfully loaded model (" + model.getTriangleCount() + " triangles)");

            var bbox3d = model.getBoundingBox();
            var center = bbox3d.center();

            // Move center to origin.
            model.translate(center.negated());

            // Find scaling factor.
            var size = bbox3d.size();
            var maxSize = Math.max(size.x, size.y);
            var scale = config.MODEL_DIAMETER / maxSize;

            var light = (new Vector3(-1, 1, 1)).normalized();
            var doc = new Document("untitled");
            var angle = 0; // Use 0.73 to make a hole.

            generatePasses(function (shadePercent, angle, lastBeforeLongTurn) {
                var render = Render.make(model, 1024, 1024, angle, null);
                render.addBase();

                // Add the shade (for spiraling). The "transform" converts from
                // model units to raster coordinates. "scale" converts from
                // model units to dots. DPI converts from inches to dots.
                var shadeWidth = config.ROD_DIAMETER*shadePercent/100.0*render.transform.scale/scale;
                var shadeCenterX = render.transform.offx;
                render.addShade(shadeWidth, shadeCenterX);

                // Expand to take into account the kerf.
                var kerfRadius = config.KERF_RADIUS_IN*render.transform.scale/scale;

                // Add some spacing so we don't char the wood.
                var roughExtraIn;
                if (svgOutput) {
                    roughExtraIn = 0;
                } else {
                    var profileAngle = angle % Math.PI;
                    if (profileAngle < Math.PI/6 || profileAngle > Math.PI*5/6) {
                        roughExtraIn = 0;
                    } else if (shadePercent === 0) {
                        roughExtraIn = config.ROUGH_EXTRA_LAST_IN;
                    } else {
                        roughExtraIn = config.ROUGH_EXTRA_IN;
                    }
                }
                kerfRadius += roughExtraIn*render.transform.scale/scale;
                render.addKerf(kerfRadius);

                if (shadePercent === 0) {
                    // Make sure top is cut off when not shading.
                    render.setTop(2, "black");
                } else {
                    // Cut off the sides when we're shading.
                    render.setTop(2, "white");
                }

                var paths = outliner.findOutlines(render);
                paths.simplify(1);
                paths.draw(render.ctx);
                paths = paths.transformInverse(render.transform, scale, config.FINAL_X, config.FINAL_Y);

                $("body").append(render.canvas);

                paths.each(function (path) {
                    var cut = new Cut(path, 4, 100, 50);
                    doc.addCut(cut);
                });
                doc.addCut(makeHeatSensorCut())
                doc.addCut(makeTimeWasterCut(lastBeforeLongTurn))
            });

            var buf = new Buffer();
            var $a;
            if (svgOutput) {
                svg.generateSvg(buf, doc);
                $a = $("<a>").attr("download", "out.svg").attr("href", buf.toDataUri("image/svg+xml")).text("Click to download SVG file");
            } else {
                epilog.generatePrn(buf, doc);
                $a = $("<a>").attr("download", "out.prn").attr("href", buf.toDataUri("application/octet-stream")).text("Click to download PRN file");
            }
            $("body").append($a);
        }, function (error) {
            log.warn("Error loading model: " + error);
        });
    };

    var rasterTest = function () {
        var doc = new Document("untitled");

        var canvas = document.createElement("canvas");
        canvas.width = 200;
        canvas.height = 200;
        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "black";
        ctx.fillRect(0, 0, 200, 200);
        ctx.fillStyle = "white";
        ctx.beginPath();
        ctx.arc(100, 100, 80, 0, 2*Math.PI);
        ctx.fill();

        var raster = new Raster(ctx.getImageData(0, 0, 200, 200), 3, 3, 100, 100);
        doc.addRaster(raster);

        var buf = new Buffer();
        epilog.generatePrn(buf, doc);
        var $a = $("<a>").attr("download", "out.prn").attr("href", buf.toDataUri("application/octet-stream")).text("Click to download PRN file");
        $("body").append($a);
    };

    var threeTest = function () {
        var width = 600;
        var height = 600;
        var renderer = new THREE.WebGLRenderer();
        renderer.setSize(width, height);
        document.body.appendChild(renderer.domElement);

        var centerOfScene = new THREE.Vector3(0, 0, 0);
        var camera = new THREE.PerspectiveCamera(45, width/height, 10, 10000);
        camera.position.x = centerOfScene.x + 1300;
        camera.position.y = centerOfScene.y + 1300;
        camera.position.z = centerOfScene.z + 1300;
        camera.lookAt(centerOfScene);

        var pathname = "models/new_knight_baseclean_sym.json";
        $.ajax(pathname, {
            dataType: "json",
            success: function (data) {
                var scene = new THREE.Scene();

                var objs = [];

                _.each(data.meshes, function (mesh) {
                    var geometry = new THREE.Geometry();
                    var scale = 40;
                    for (var i = 0; i < mesh.vertices.length; i += 3) {
                        geometry.vertices.push(new THREE.Vector3(
                            mesh.vertices[i + 0]*scale,
                            mesh.vertices[i + 1]*scale,
                            mesh.vertices[i + 2]*scale));
                    }
                    for (var i = 0; i < mesh.faces.length; i++) {
                        geometry.faces.push(new THREE.Face3(
                            mesh.faces[i][0],
                            mesh.faces[i][1],
                            mesh.faces[i][2]));
                    }
                    geometry.computeFaceNormals();
                    geometry.computeBoundingSphere();
                    geometry.computeBoundingBox();

                    var material = new THREE.MeshLambertMaterial({
                        color: 0xffffff,
                        shading: THREE.FlatShading
                    });

                    var obj = new THREE.Mesh(geometry, material);
                    objs.push(obj);
                    scene.add(obj);
                });

                var light = new THREE.DirectionalLight(0xffffff);
                light.position.set(0, 0, 300);
                // light.target = mesh;
                scene.add(light);

                light = new THREE.DirectionalLight(0xffffff);
                light.position.set(0, 0, -300);
                // light.target = mesh;
                scene.add(light);

                var render = function () {
                    requestAnimationFrame(render);
                    objs[0].rotation.x += 0.01;
                    objs[0].rotation.z += 0.02;
                    renderer.render(scene, camera);
                };
                render();
            }
        });
    };

    var loadModel = function () {
        var filename;
        var rotationCount;

        filename = "DNA.json"; rotationCount = 2;
        filename = "new_knight_baseclean_sym.json"; rotationCount = 3;

        Model.load("models/" + filename, rotationCount, function (model) {
        });
    };

    var main = function () {
        $("#startPrnButton").click(function () { start(false); });
        $("#startSvgButton").click(function () { start(true); });
        $("#rasterTestButton").click(rasterTest);
        $("#threeTestButton").click(threeTest);

        loadModel();
    };

    main();
});
