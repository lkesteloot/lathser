
import math

# A 2D vector.
class Vector2(object):
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __str__(self):
        return "Vector2[%g,%g]" % (self.x, self.y)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector2(self.x*other, self.y*other)

    def __div__(self, other):
        return Vector2(self.x/other, self.y/other)

    def dot(self, other):
        return self.x*other.x + self.y*other.y

    def length(self):
        return math.sqrt(self.dot(self))

    def normalized(self):
        return self/self.length()

    # Component-wise min.
    def min(self, other):
        return Vector2(min(self.x, other.x), min(self.y, other.y))

    # Component-wise max.
    def max(self, other):
        return Vector2(max(self.x, other.x), max(self.y, other.y))

    # Rotated 90 counter-clockwise.
    def reciprocal(self):
        return Vector2(-self.y, self.x)

    # Returns angle in radians.
    def angle(self):
        return math.atan2(self.y, self.x)

    def flipX(self):
        return Vector2(-self.x, self.y)

    def flipY(self):
        return Vector2(self.x, -self.y)

# A 3D vector.
class Vector3(object):
    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __str__(self):
        return "Vector3[%g,%g,%g]" % (self.x, self.y, self.z)

    def __repr__(self):
        return str(self)

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return Vector3(self.x*other, self.y*other, self.z*other)

    def __div__(self, other):
        return Vector3(self.x/other, self.y/other, self.z/other)

    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z

    def length(self):
        return math.sqrt(self.dot(self))

    def normalized(self):
        return self/self.length()

    # Right-handed cross product.
    def cross(self, other):
        a = self
        b = other
        return Vector3(a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x)

    # Component-wise min.
    def min(self, other):
        return Vector3(min(self.x, other.x), min(self.y, other.y), min(self.z, other.z))

    # Component-wise max.
    def max(self, other):
        return Vector3(max(self.x, other.x), max(self.y, other.y), max(self.z, other.z))

    # Rotate the 3D vector around the Z axis by "angle", then project on the X
    # plane.
    def project(self, transform, angle):
        # Rotate around Z axis.
        rx = math.cos(angle)*self.x - math.sin(angle)*self.y
        ry = math.sin(angle)*self.x + math.cos(angle)*self.y
        rz = self.z

        x, y = transform.transform(ry, rz)

        return Vector2(x, y)
