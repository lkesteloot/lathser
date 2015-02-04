
#   Copyright 2015 Lawrence Kesteloot
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import sys
import json
import math
import collections

# pip install Pillow (https://python-pillow.github.io/)
from PIL import Image, ImageDraw
from PIL.GifImagePlugin import getheader, getdata

# https://raw.githubusercontent.com/python-pillow/Pillow/master/Scripts/gifmaker.py
import gifmaker

# What kind of image to make. Use "L" for GIF compatibility.
RASTER_MODE = "L"
RASTER_WHITE = 255

# Diameter in inches.
ROD_DIAMETER = 0.8
# Total margin within rod as a fraction of the diameter.
MARGIN = 0.1
MODEL_DIAMETER = ROD_DIAMETER*(1 - MARGIN)

# Number of cuts.
ANGLE_COUNT = 1

# What we're targeting (viewing in Chrome or cutting on the laser cutter).
TARGET_VIEW, TARGET_CUT = range(2)
TARGET = TARGET_VIEW

# Final position of model in inches. The rig centers
# the rod at 1.25 inches from the left, and the laser
# cutter itself considers "0" to be about 0.045 inches
# from the left.
FINAL_X = 1.25 - 0.045
FINAL_Y = 1

# Number of times to scale up the rendering. 1 will be fast
# but low-res, 5 is slower but high-res.
RENDER_SCALE = 5

# The various passes we want to make to spiral into the center, in
# percentages of the whole. Make sure that the last entry is 0.
PASS_SHADES = [80, 60, 40, 20, 0]
PASS_SHADES = [0]

# The radius of the kerf, in inches.
KERF_RADIUS_IN = 0.002

# Size of the laser bed.
DPI = 72
SVG_WIDTH = 32*DPI
SVG_HEIGHT = 20*DPI

if TARGET == TARGET_CUT:
    # "Hairline" in AI.
    STROKE_WIDTH = 0.001
    FOREGROUND_COLOR = "black"
    BACKGROUND_COLOR = "white"
else:
    STROKE_WIDTH = 1
    FOREGROUND_COLOR = "white"
    BACKGROUND_COLOR = "black"

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

    # Component-wise min.
    def min(self, other):
        return Vector3(min(self.x, other.x), min(self.y, other.y), min(self.z, other.z))

    # Component-wise max.
    def max(self, other):
        return Vector3(max(self.x, other.x), max(self.y, other.y), max(self.z, other.z))

    def project(self, transform, angle):
        # Rotate around Z axis.
        rx = math.cos(angle)*self.x - math.sin(angle)*self.y
        ry = math.sin(angle)*self.x + math.cos(angle)*self.y
        rz = self.z

        x, y = transform.transform(ry, rz)

        return Vector2(x, y)

# Represents a 2D transformation.
class Transform(object):
    # The transform takes model coordinate (x,y) and computes (x*scale + offx,
    # y*scale+offy).
    def __init__(self, scale, offx, offy):
        self.scale = scale
        self.offx = offx
        self.offy = offy

    def __str__(self):
        return "Trans[%g,(%g,%g)]" % (self.scale, self.offx, self.offy)

    def transform(self, x, y):
        return x*self.scale + self.offx, y*self.scale + self.offy

    def transformVertex2D(self, v):
        x, y = self.transform(v.x, v.y)
        return Vector2(x, y)

    def invert(self):
        # x' = x*scale + offx
        # x' - offx = x*scale
        # x = (x' - offx)/scale
        # x = x'/scale - offx/scale
        return Transform(1.0/self.scale, -self.offx/self.scale, -self.offy/self.scale)

    def scaled(self, scale):
        return Transform(self.scale*scale, self.offx*scale, self.offy*scale)

    def translated(self, dx, dy):
        return Transform(self.scale, self.offx + dx, self.offy + dy)

    @staticmethod
    def makeMap(bbox, width, height):
        size = bbox.size()

        if size.x/size.y < float(width)/height:
            # Left/right margins. Fit height.
            scale = height/size.y
        else:
            # Bottom/top margins. Fit width.
            scale = width/size.x

        offset = Vector2(width, height)/2.0 - bbox.center()*scale

        return Transform(scale, offset.x, offset.y)

    @staticmethod
    def makeIdentity():
        return Transform(1, 0, 0)

# 2D bounding box.
class BoundingBox2D(object):
    def __init__(self):
        self.min = Vector2(sys.float_info.max, sys.float_info.max)
        self.max = Vector2(-sys.float_info.max, -sys.float_info.max)

    def addPoint(self, v):
        self.min = self.min.min(v)
        self.max = self.max.max(v)

    def addTriangle(self, triangle):
        for vertex in triangle.vertices:
            self.addPoint(vertex)

    def addMargin(self, margin):
        self.min.x -= margin
        self.min.y -= margin
        self.max.x += margin
        self.max.y += margin

    def size(self):
        return self.max - self.min

    def center(self):
        return self.min + self.size()/2

    def __str__(self):
        return "BBOX([%g,%g,%g] - [%g,%g,%g])" % (self.min.x, self.min.y, self.max.x, self.max.y)

# 3D bounding box.
class BoundingBox3D(object):
    def __init__(self):
        self.min = Vector3(sys.float_info.max, sys.float_info.max, sys.float_info.max)
        self.max = Vector3(-sys.float_info.max, -sys.float_info.max, -sys.float_info.max)

    def addPoint(self, v):
        self.min = self.min.min(v)
        self.max = self.max.max(v)

    def addTriangle(self, triangle):
        for vertex in triangle.vertices:
            self.addPoint(vertex)

    def addMargin(self, margin):
        self.min.x -= margin
        self.min.y -= margin
        self.min.z -= margin
        self.max.x += margin
        self.max.y += margin
        self.max.z += margin

    def size(self):
        return self.max - self.min

    def center(self):
        return self.min + self.size()/2

    def __str__(self):
        return "BBOX([%g,%g,%g] - [%g,%g,%g])" % (self.min.x, self.min.y, self.min.z, self.max.x, self.max.y, self.max.z)

# A 2-dimensional triangle.
class Triangle2D(object):
    # Vertices is a list of Vector2.
    def __init__(self, vertices):
        self.vertices = vertices

# A 3-dimensional triangle.
class Triangle3D(object):
    # Vertices is a list of Vector3.
    def __init__(self, vertices):
        self.vertices = vertices

    def project(self, transform, angle):
        return Triangle2D([vertex.project(transform, angle) for vertex in self.vertices])

    def __add__(self, vector3):
        return Triangle3D([v + vector3 for v in self.vertices])

    def __sub__(self, vector3):
        return Triangle3D([v - vector3 for v in self.vertices])

# Two 2D vertices representing an edge of the object0.
class Edge(object):
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
        self.used = False

    def __hash__(self):
        return hash((self.v1, self.v2))

    def __eq__(self, other):
        return (self.v1, self.v2) == (other.v1, other.v2)

# Return an image of the 3D triangles in an image of the width and height
# specified.  The triangles are rotated by angle around the Z axis.
def render(triangles, width, height, angle):
    print "Rendering at angle %g" % int(angle*180/math.pi)

    bbox = BoundingBox2D()

    transform = Transform.makeIdentity()

    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)
        bbox.addTriangle(triangle2d)

    # print "Model bounding box:", bbox

    # Pad so we don't run into the edge of the image.
    bbox.addMargin(bbox.size().x/20)

    transform = Transform.makeMap(bbox, width, height)

    # Render.
    img = Image.new(RASTER_MODE, (width, height))
    draw = ImageDraw.Draw(img)

    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)
        tbbox = BoundingBox2D()
        tbbox.addTriangle(triangle2d)
        draw.polygon([(v.x, v.y) for v in triangle2d.vertices], fill=RASTER_WHITE, outline=RASTER_WHITE)

    return img, transform

# Return the height below the object where there are no on pixels.
def get_base_height(image):
    width, height = image.size

    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, height - 1 - y))
            if pixel != 0:
                return y

    raise Exception("base not found")

# Modify the image in-place to add a base to the bottom of it.
def add_base(image):
    width, height = image.size
    base_height = get_base_height(image)

    for y in range(base_height):
        for x in range(width):
            image.putpixel((x, height - 1 - y), RASTER_WHITE)

def add_shade(image, shade_percent):
    width, height = image.size
    shade_width = width*shade_percent/100
    start_x = (width - shade_width)/2

    for y in range(height):
        for x in range(shade_width):
            image.putpixel((start_x + x, y), RASTER_WHITE)

# Extend the shape in the image by the radius and return the new image.
def add_kerf(image, radius):
    print "Adding kerf of radius %.2f" % radius

    width, height = image.size
    new_image = Image.new(RASTER_MODE, (width, height))
    draw = ImageDraw.Draw(new_image)

    for y in range(height):
        for x in range(width):
            p = image.getpixel((x, y))
            if p == RASTER_WHITE:
                draw.arc([x - radius, y - radius, x + radius, y + radius], 0, 360, RASTER_WHITE)

    return new_image

def loadFile(filename):
    print "Loading model..."
    data = json.load(open(filename))

    vertices = []
    triangles = []

    for mesh in data["meshes"]:
        rawVertices = mesh["vertices"]
        rawNormals = mesh["normals"]
        rawFaces = mesh["faces"]

        vertexOffset = len(vertices)

        vertices.extend([
            Vector3(rawVertices[i*3 + 0], rawVertices[i*3 + 1], rawVertices[i*3 + 2])
            for i in range(len(rawVertices)/3)])

        triangles.extend([Triangle3D([
            vertices[vertexOffset + face[0]],
            vertices[vertexOffset + face[1]],
            vertices[vertexOffset + face[2]]]) for face in rawFaces])

    return triangles

# Return "count" angles (in radians) going around the circle.
def angles(count):
    return [angle*math.pi*2/count for angle in range(count)]

# Return a list of paths of Vector2().
def get_outlines(image):
    edges = []

    # Generate edges for each pixel.
    print "Generating edges..."
    width, height = image.size
    for y in range(height - 1):
        for x in range(width - 1):
            this = image.getpixel((x, y))
            right = image.getpixel((x + 1, y))
            down = image.getpixel((x, y + 1))

            if this != right:
                edges.append(Edge(Vector2(x + 1, y), Vector2(x + 1, y + 1)))
            if this != down:
                edges.append(Edge(Vector2(x, y + 1), Vector2(x + 1, y + 1)))
    print "Made %d edges." % len(edges)

    # Put into a hash by the edges.
    print "Hashing edges..."
    edgemap = collections.defaultdict(list)
    for edge in edges:
        edgemap[edge.v1].append(edge)
        edgemap[edge.v2].append(edge)
    print "Found %d unique vertices." % len(edgemap)

    # Walk around, starting at any edge.
    print "Making sequence of vertices..."
    paths = []
    vertices = []
    paths.append(vertices)
    edge = edges[0]
    vertices.append(edge.v1)
    vertex = edge.v2
    while True:
        edge.used = True
        vertices.append(vertex)
        connected_edges = [edge for edge in edgemap[vertex] if not edge.used]
        if not connected_edges:
            edges = [edge for edge in edges if not edge.used]
            if not edges:
                # No more vertices to add.
                break
            # Done on this end. See if we can continue on the other end, in case
            # it's not a closed path.
            vertices.reverse()
            vertex = vertices[-1]
            connected_edges = [edge for edge in edgemap[vertex] if not edge.used]
        if not connected_edges:
            # Start new path.
            vertices = []
            paths.append(vertices)
            edge = edges[0]
            vertices.append(edge.v1)
            vertex = edge.v2
        else:
            # Extend current path.
            edge = connected_edges[0]
            if edge.v1 == vertex:
                vertex = edge.v2
            else:
                vertex = edge.v1
    edges = [edge for edge in edges if not edge.used]
    print "Sequence has %d vertices, with %d edges unused." % (len(vertices), len(edges))

    return paths

# Given vectors v1 and v2 and point v, returns the distance from v to the line v1..v2.
def distance_to_line(v, v1, v2):
    segment = v1 - v2
    n = segment.reciprocal().normalized()
    return math.fabs((v - v1).dot(n))

# Given a list of vertices and a distance, returns a new list with vertices
# removed if they add less than epsilon of detail.
def simplify_vertices(vertices, epsilon):
    # http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm

    # Find the point with the maximum distance
    max_dist = 0
    index = 0
    first = 0
    last = len(vertices) - 1
    for i in range(first + 1, last):
        # print vertices[i], vertices[first], vertices[last]
        if vertices[first] == vertices[last]:
            dist = (vertices[i] - vertices[first]).length()
        else:
            dist = distance_to_line(vertices[i], vertices[first], vertices[last])
        if dist > max_dist:
            index = i
            max_dist = dist

    # If max distance is greater than epsilon, recursively simplify
    if max_dist > epsilon:
        # Recursive call
        first_half = simplify_vertices(vertices[first:index+1], epsilon)
        second_half = simplify_vertices(vertices[index:last+1], epsilon)

        # Skip the duplicate middle vertex.
        return first_half[:-1] + second_half
    else:
        # None are far enough, just keep the ends.
        return [vertices[first], vertices[last]]

# Return the vertices transformed by the inverse of the transform.
def transform_vertices(vertices, transform, scale):
    # Compute the inverse transform.
    transform = transform.invert()

    # Scale to final size.
    transform = transform.scaled(scale)

    # Move to right position.
    transform = transform.translated(FINAL_X*DPI, FINAL_Y*DPI)

    return [transform.transformVertex2D(v) for v in vertices]

def generate_svg(filename, paths):
    out = open(filename, "w")
    out.write("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
"http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd" [
<!ENTITY ns_svg "http://www.w3.org/2000/svg">
]>
<svg xmlns="&ns_svg;" width="%d" height="%d" overflow="visible" style="background: %s">
""" % (SVG_WIDTH, SVG_HEIGHT, BACKGROUND_COLOR))
    for vertices in paths:
        out.write("""<polyline fill="none" stroke="%s" stroke-width="%g" points=" """ % (FOREGROUND_COLOR, STROKE_WIDTH))
        for vertex in vertices:
            out.write(" %g,%g" % (vertex.x, vertex.y))
        out.write(""" "/>\n""")
    out.write("""</svg>
""")
    out.close()
    print "Generated \"%s\"." % filename

def main():
    filename = "data/LargeKnight.json"
    filename = "data/My_Scan_1.json"
    filename = "data/knight.json"

    triangles = loadFile(filename)
    print "The model has %d triangles." % len(triangles)

    # Single image.
    if False:
        img, _ = render(triangles, 1024, 1024, 0)
        add_base(img)
        img.save("out.png")

    # Animated GIF.
    if False:
        images = [render(triangles, 256, 256, angle)[0] for angle in angles(ANGLE_COUNT)]

        fp = open("out.gif", "wb")
        gifmaker.makedelta(fp, images)
        fp.close()

    # Single SVG.
    if False:
        image, _ = render(triangles, 256*5, 256*5, 0)
        paths = get_outlines(image)
        paths = [simplify_vertices(vertices, 1) for vertices in paths]
        generate_svg("out.svg", paths)

    # All SVGs.
    if True:
        bbox3d = BoundingBox3D()
        for triangle in triangles:
            bbox3d.addTriangle(triangle)

        center = bbox3d.center()
        print "Center of bbox3d:", center

        # Move center to origin.
        triangles = [triangle - center for triangle in triangles]

        # Find scaling factor.
        size = bbox3d.size()
        max_size = max(size.x, size.y)
        scale = MODEL_DIAMETER / max_size * DPI

        index = 0
        for pass_number, shade_percent in enumerate(PASS_SHADES):
            print "Making pass %d (%d%%)" % (pass_number, shade_percent)

            for angle in angles(ANGLE_COUNT):
                image, transform = render(triangles, 256*RENDER_SCALE, 256*RENDER_SCALE, angle)
                add_base(image)
                add_shade(image, shade_percent)
                kerf_radius = KERF_RADIUS_IN*transform.scale/scale*DPI
                image = add_kerf(image, kerf_radius)
                paths = get_outlines(image)
                paths = [simplify_vertices(vertices, 1) for vertices in paths]
                paths = [transform_vertices(vertices, transform, scale) for vertices in paths]
                generate_svg("out%02d.svg" % index, paths)
                index += 1

if __name__ == "__main__":
    main()
