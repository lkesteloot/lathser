// Stores a 3D vector.

'use strict';

define(["Vector2"], function (Vector2) {
    var Vector3 = function (x, y, z) {
        this.x = x;
        this.y = y;
        this.z = z;
    };

    Vector3.prototype.toString = function () {
        return "Vector3[" + this.toStringTerse() + "]";
    };

    Vector3.prototype.toStringTerse = function () {
        return this.x + "," + this.y + "," + this.z;
    };

    Vector3.prototype.negated = function () {
        return new Vector3(-this.x, -this.y, -this.z);
    };

    Vector3.prototype.plus = function (other) {
        return new Vector3(this.x + other.x, this.y + other.y, this.z + other.z);
    };

    Vector3.prototype.minus = function (other) {
        return new Vector3(this.x - other.x, this.y - other.y, this.z - other.z);
    };

    Vector3.prototype.times = function (other) {
        return new Vector3(this.x*other, this.y*other, this.z*other);
    };

    Vector3.prototype.dividedBy = function (other) {
        return new Vector3(this.x/other, this.y/other, this.z/other);
    };

    Vector3.prototype.dot = function (other) {
        return this.x*other.x + this.y*other.y + this.z*other.z;
    };

    Vector3.prototype.length = function () {
        return Math.sqrt(this.dot(this));
    };

    Vector3.prototype.normalized = function () {
        return this.dividedBy(this.length());
    };

    // Right-handed cross product.
    Vector3.prototype.cross = function (other) {
        var a = this;
        var b = other;
        return new Vector3(a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x);
    };

    // Component-wise min.
    Vector3.prototype.min = function (other) {
        return new Vector3(
            Math.min(this.x, other.x),
            Math.min(this.y, other.y),
            Math.min(this.z, other.z));
    };

    // Component-wise max.
    Vector3.prototype.max = function (other) {
        return new Vector3(
            Math.max(this.x, other.x),
            Math.max(this.y, other.y),
            Math.max(this.z, other.z));
    };

    // Rotate the 3D vector around the Z axis by "angle", then project on the X
    // plane. Returns a Vector2.
    Vector3.prototype.project = function (transform, angle) {
        // Rotate around Z axis.
        var rx = Math.cos(angle)*this.x - Math.sin(angle)*this.y;
        var ry = Math.sin(angle)*this.x + Math.cos(angle)*this.y;
        var rz = this.z;

        return transform.transform(new Vector2(ry, rz));
    };

    // Return a copy of the vertex rotated 90 degrees around the X axis. This is for
    // converting models from around-Y to around-Z.
    Vector3.prototype.rotateX90 = function () {
        return new Vector3(this.x, -this.z, this.y);
    };

    return Vector3;
});
