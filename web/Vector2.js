// Stores a 2D vector.

'use strict';

define([], function () {
    var Vector2 = function (x, y) {
        this.x = x;
        this.y = y;
    };

    Vector2.prototype.toString = function () {
        return "Vector2[" + this.x + "," + this.y + "]";
    };

    Vector2.prototype.negated = function () {
        return new Vector2(-this.x, -this.y);
    };

    Vector2.prototype.plus = function (other) {
        return new Vector2(this.x + other.x, this.y + other.y);
    };

    Vector2.prototype.minus = function (other) {
        return new Vector2(this.x - other.x, this.y - other.y);
    };

    Vector2.prototype.times = function (other) {
        return new Vector2(this.x*other, this.y*other);
    };

    Vector2.prototype.dividedBy = function (other) {
        return new Vector2(this.x/other, this.y/other);
    };

    Vector2.prototype.dot = function (other) {
        return this.x*other.x + this.y*other.y;
    };

    Vector2.prototype.length = function () {
        return Math.sqrt(this.dot(this));
    };

    Vector2.prototype.normalized = function () {
        return this.dividedBy(this.length());
    };

    // Component-wise min.
    Vector2.prototype.min = function (other) {
        return new Vector2(
            Math.min(this.x, other.x),
            Math.min(this.y, other.y));
    };

    // Component-wise max.
    Vector2.prototype.max = function (other) {
        return new Vector2(
            Math.max(this.x, other.x),
            Math.max(this.y, other.y));
    };

    return Vector2;
});
