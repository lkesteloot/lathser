
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

from vector import Vector2, Vector3

from document import Document
from cut import Cut
import epilog

# What kind of image to make. Use "L" for GIF compatibility.
RASTER_MODE = "L"
RASTER_BLACK = 0
RASTER_WHITE = 255

# Diameter of rod in inches.
ROD_DIAMETER = 0.8
# Total margin within rod as a fraction of the diameter.
MARGIN = 0.1
MODEL_DIAMETER = ROD_DIAMETER*(1 - MARGIN)

# Number of cuts around the circle.
ANGLE_COUNT = 16

# What we're targeting (viewing in Chrome or cutting on the laser cutter).
TARGET_VIEW, TARGET_CUT = range(2)
TARGET = TARGET_VIEW

# Final position of model in inches. The rig centers
# the rod at 1.25 inches from the left, and the laser
# cutter itself considers "0" to be about 0.045 inches
# from the left.
FINAL_X = 1.25 - 0.045
FINAL_Y = 1

# Base raster image size. Scaled by RENDER_SCALE.
IMAGE_SIZE = 256

# Number of times to scale up the rendering. 1 will be fast
# but low-res, 5 is slower but high-res.
RENDER_SCALE = 2

# Whether to generate a single file (True) or individual files (False).
GENERATE_SINGLE_FILE = True

# If generating a single file, whether to generate a single path.
GENERATE_SINGLE_PATH = False

# Whether to also generate a lit version of the raster.
GENERATE_LIT_VERSION = True

# The various passes we want to make to spiral into the center, in
# percentages of the whole. Make sure that the last entry is 0.
PASS_SHADES = [80, 40, 0]
PASS_SHADES = [40, 20, 0]
# PASS_SHADES = [0]

# The radius of the laser kerf, in inches.
KERF_RADIUS_IN = 0.002

# Extra spacing for rough cuts, in inches.
ROUGH_EXTRA_IN = 1/16.0

# Dots per inch in the SVG file. Don't change this.
DPI = 72

# Size of the laser bed, in dots.
SVG_WIDTH = 32*DPI
SVG_HEIGHT = 20*DPI

# Output file type.
OUTPUT_EXTENSION = "svg"
OUTPUT_EXTENSION = "vector"  # For Ctrl-cut
#OUTPUT_EXTENSION = "prn"     # For direct printing

# We can only output integers, so we translate to a much higher DPI.
VECTOR_DPI = 1200

# Stroke widths and colors.
if TARGET == TARGET_CUT:
    # "Hairline" in AI.
    STROKE_WIDTH = 0.001
    FOREGROUND_COLOR = "black"
    BACKGROUND_COLOR = "white"
else:
    # Width of 1 so we can see it.
    STROKE_WIDTH = 1
    FOREGROUND_COLOR = "white"
    BACKGROUND_COLOR = "black"

# Represents a 2D transformation (scale and translation).
class Transform(object):
    # The transform takes model coordinate (x,y) and computes (x*scale + offx,
    # y*scale+offy).
    def __init__(self, scale, offx, offy):
        self.scale = scale
        self.offx = offx
        self.offy = offy

    def __str__(self):
        return "Trans[%g,(%g,%g)]" % (self.scale, self.offx, self.offy)

    # Transform a coordinate to its new location.
    def transform(self, x, y):
        return x*self.scale + self.offx, y*self.scale + self.offy

    # Transform a Vector2 to another Vector2.
    def transformVector2(self, v):
        x, y = self.transform(v.x, v.y)
        return Vector2(x, y)

    # Create a new transformation that's the inverse of this one.
    def invert(self):
        # x' = x*scale + offx
        # x' - offx = x*scale
        # x = (x' - offx)/scale
        # x = x'/scale - offx/scale
        return Transform(1.0/self.scale, -self.offx/self.scale, -self.offy/self.scale)

    # Create a new transformation that's scaled.
    def scaled(self, scale):
        return Transform(self.scale*scale, self.offx*scale, self.offy*scale)

    # Create a new transformation that's translated.
    def translated(self, dx, dy):
        return Transform(self.scale, self.offx + dx, self.offy + dy)

    # Create a transformation that maps from the bbox to the width and height.
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

    # Create a no-op transformation.
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

        # Compute normal.
        v1 = vertices[0] - vertices[2]
        v2 = vertices[0] - vertices[1]
        self.normal = v1.cross(v2)
        if self.normal.length() != 0:
            self.normal = self.normal.normalized()

    # Rotate this 3D triangle by angle, transform it, project it onto 2D, and return
    # a 2D triangle.
    def project(self, transform, angle):
        return Triangle2D([vertex.project(transform, angle) for vertex in self.vertices])

    # Return a copy of the triangle rotated 90 degrees around the X axis. This is for
    # converting models from around-Y to around-Z.
    def rotatex90(self):
        return Triangle3D([v.rotatex90() for v in self.vertices])

    # Translate this triangle by the vector.
    def __add__(self, vector3):
        return Triangle3D([v + vector3 for v in self.vertices])

    # Translate this triangle by the negative of the vector.
    def __sub__(self, vector3):
        return Triangle3D([v - vector3 for v in self.vertices])

# Two 2D vectors representing an edge of the object.
class Edge(object):
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2

        # Flag for whether we've used this edge in the path-building algorithm.
        self.used = False

    def __hash__(self):
        # Don't hash "used", that's not part of the value.
        return hash((self.v1, self.v2))

    def __eq__(self, other):
        return (self.v1, self.v2) == (other.v1, other.v2)

# Return an image of the 3D triangles in an image of the width and height
# specified.  The triangles are rotated by angle around the Z axis. If
# the "light" 3D vector is not None, the triangles are lit by a light
# pointed to by that vector.
def render(triangles, width, height, angle, light):
    print "Rendering at angle %g" % int(angle*180/math.pi)

    bbox = BoundingBox2D()

    transform = Transform.makeIdentity()

    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)
        bbox.addTriangle(triangle2d)

    # Pad so we don't run into the edge of the image.
    bbox.addMargin(bbox.size().x/10)

    # Map from object bounding box to raster size.
    transform = Transform.makeMap(bbox, width, height)

    # Create image.
    img = Image.new(RASTER_MODE, (width, height))
    draw = ImageDraw.Draw(img)

    # Draw the triangles.
    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)

        if light:
            # Remove backfacing triangles.
            if triangle.normal.x > 0:
                continue

            # Compute diffuse component of lighting.
            diffuse = triangle.normal.dot(light)
            if diffuse < 0:
                diffuse = 0

            # Convert to pixel value.
            color = int(diffuse*255 + 0.5)
        else:
            color = RASTER_WHITE

        draw.polygon([(v.x, v.y) for v in triangle2d.vertices], fill=color, outline=color)

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

# Draw a rectangle of width "shade_width" down the middle of the image
# so we can spiral into the rod.
def add_shade(image, shade_width, shade_center_x):
    width, height = image.size
    start_x = shade_center_x - shade_width/2

    # Start at 2 so that the path can trace it. For some reason 1
    # does not work.
    for y in range(2, height):
        for x in range(shade_width):
            image.putpixel((start_x + x, y), RASTER_WHITE)

# Clear the top "size" pixels of the image.
def clear_top(image, size):
    width, height = image.size

    for y in range(0, size):
        for x in range(width):
            image.putpixel((x, y), RASTER_BLACK)

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

# Return a list of 3D triangles.
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

# Return the first half of the list.
def half_list(lst):
    return lst[:len(lst)/2]

# Return a list of paths of Vector2() for this image.
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
    if not edges:
        print "Error: Found no pixels in image."
        sys.exit(1)

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

# Given points v1 and v2 and point v, returns the distance from v to the line v1,v2.
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

    return [transform.transformVector2(v) for v in vertices]

# Go to the spot that indicates to the hardware that it should advance to
# the next step.
def make_heat_sensor():
    x = 3.0*DPI
    y = 2.5*DPI
    radius = DPI/32.0
    pointCount = 10

    points = []

    points.append(Vector2(x, y - 1))
    points.append(Vector2(x, y))
#    for i in range(pointCount + 1):
#        t = float(i)/pointCount*math.pi*2
#        points.append(Vector2(x + math.cos(t)*radius, y + math.sin(t)*radius))

    return [points]

# Go far away to give the hardware a chance to rotate.
def make_time_waster():
    x = 10*DPI
    y = 2.5*DPI
    radius = DPI
    pointCount = 10

    points = []

    for i in range(pointCount + 1):
        t = float(i)/pointCount*math.pi*2
        points.append(Vector2(x + math.cos(t)*radius, y + math.sin(t)*radius))

    return [points]


def generate_svg(out, paths):
    out.write("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
"http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd" [
<!ENTITY ns_svg "http://www.w3.org/2000/svg">
]>
<svg xmlns="&ns_svg;" width="%d" height="%d" overflow="visible" style="background: %s">
""" % (SVG_WIDTH, SVG_HEIGHT, BACKGROUND_COLOR))
    for path in paths:
        out.write("""<polyline fill="none" stroke="%s" stroke-width="%g" points=" """ % (FOREGROUND_COLOR, STROKE_WIDTH))
        for vertex in path:
            out.write(" %g,%g" % (vertex.x, vertex.y))
        out.write(""" "/>\n""")
    out.write("""</svg>
""")

def generate_vector(out, paths):
    for path in paths:
        for index, vertex in enumerate(path):
            command = "M" if index == 0 else "L"
            x = int(vertex.x*VECTOR_DPI/DPI)
            y = int(vertex.y*VECTOR_DPI/DPI)
            out.write("%s%d,%d\n" % (command, y, x))
    out.write("X\n")

def generate_prn(out, paths, title):
    doc = Document(title)
    dpi = doc.getResolution()
    for path in paths:
        cut = Cut(4, 100, 50)
        # Convert to doc's resolution.
        cut.points = [Vector2(p.x*dpi/DPI, p.y*dpi/DPI) for p in path]
        doc.addCut(cut)

    epilog.generate_prn(out, doc)

def generate_file(basename, paths):
    filename = basename + "." + OUTPUT_EXTENSION

    out = open(filename, "w")
    if OUTPUT_EXTENSION == "svg":
        generate_svg(out, paths)
    elif OUTPUT_EXTENSION == "vector":
        generate_vector(out, paths)
    elif OUTPUT_EXTENSION == "prn":
        generate_prn(out, paths, basename)
    else:
        raise Exception("Unknown extension " + OUTPUT_EXTENSION)
    out.close()

    print "Generated \"%s\"." % filename

def main():
    filename = "data/new_knight_baseclean_sym.json"
    rotation_count = 3

    filename = "data/DNA.json"
    rotation_count = 2

    triangles = loadFile(filename)
    print "The model has %d triangles." % len(triangles)

    for i in range(rotation_count):
        # We need the model to be around Z. If it's around Y, transform the initial
        # geometry so that the rest of the program doesn't have to concern itself with it.
        triangles = [triangle.rotatex90() for triangle in triangles]

    # Single image.
    if False:
        img, _ = render(triangles, 1024, 1024, 0)
        add_base(img)
        img.save("out.png")

    # Animated GIF.
    if False:
        images = [render(triangles, IMAGE_SIZE, IMAGE_SIZE, angle)[0] for angle in angles(ANGLE_COUNT)]

        fp = open("out.gif", "wb")
        gifmaker.makedelta(fp, images)
        fp.close()

    # Single SVG.
    if False:
        image, _ = render(triangles, IMAGE_SIZE*RENDER_SCALE, IMAGE_SIZE*RENDER_SCALE, 0)
        paths = get_outlines(image)
        paths = [simplify_vertices(vertices, 1) for vertices in paths]
        generate_file("out", paths)

    # All SVGs.
    if True:
        bbox3d = BoundingBox3D()
        for triangle in triangles:
            bbox3d.addTriangle(triangle)

        center = bbox3d.center()

        # Move center to origin.
        triangles = [triangle - center for triangle in triangles]

        # Find scaling factor.
        size = bbox3d.size()
        max_size = max(size.x, size.y)
        scale = MODEL_DIAMETER / max_size * DPI

        # Light vector (to light).
        light = Vector3(-1, 1, 1).normalized()

        all_paths = []

        thetas_file = open("thetas.txt", "w")

        index = 0
        for pass_number, shade_percent in enumerate(PASS_SHADES):
            print "------------------ Making pass %d (%d%%)" % (pass_number, shade_percent)

            for angle in half_list(angles(ANGLE_COUNT)):
                # For now we use this format to make it easy to copy/paste into xcode.
                # Eventually we can send these via deep link or something.
                thetas_file.write("        @%g,\n" % angle)
                if GENERATE_LIT_VERSION:
                    image, _ = render(triangles, IMAGE_SIZE*RENDER_SCALE, IMAGE_SIZE*RENDER_SCALE, angle, light)
                    image.save("out%02d-lit.png" % index)
                image, transform = render(triangles, IMAGE_SIZE*RENDER_SCALE, IMAGE_SIZE*RENDER_SCALE, angle, None)
                image.save("out%02d-render.png" % index)
                add_base(image)

                # Add the shade (for spiraling). The "transform" converts from
                # model units to raster coordinates. "scale" converts from
                # model units to dots. DPI converts from inches to dots.
                shade_width = int(ROD_DIAMETER*shade_percent/100.0*transform.scale/scale*DPI)
                shade_center_x = int(transform.offx)
                add_shade(image, shade_width, shade_center_x)
                image.save("out%02d-shade.png" % index)

                # Expand to take into account the kerf.
                kerf_radius = KERF_RADIUS_IN*transform.scale/scale*DPI
                if shade_percent != 0:
                    # Rough cut, add some spacing so we don't char the wood.
                    kerf_radius += ROUGH_EXTRA_IN*transform.scale/scale*DPI
                image = add_kerf(image, kerf_radius)
                image.save("out%02d-kerf.png" % index)

                if GENERATE_SINGLE_PATH:
                    # Make sure the top is clear so that we don't split the path.
                    clear_top(image, 2)

                paths = get_outlines(image)
                paths = [simplify_vertices(vertices, 1) for vertices in paths]
                paths = [transform_vertices(vertices, transform, scale) for vertices in paths]
                if GENERATE_SINGLE_FILE:
                    if GENERATE_SINGLE_PATH:
                        # Assume no holes, append only first path. We could instead append
                        # the path that has the longest total distance.
                        if paths:
                            # Find the longest path (most number of vertices).
                            path = max(paths, key=lambda path: len(path))
                            all_paths.append(path)
                    else:
                        all_paths.extend(paths)
                        all_paths.extend(make_heat_sensor())
                        all_paths.extend(make_time_waster())
                else:
                    generate_file("out%02d" % index, paths)
                index += 1
                print

        if GENERATE_SINGLE_FILE:
            if GENERATE_SINGLE_PATH:
                # Find the top-most Y coordinate.
                top_y = sys.float_info.max
                for path in all_paths:
                    for vertex in path:
                        top_y = min(top_y, vertex.y)

                # Make some room.
                top_y -= DPI/8.0

                # Blend all paths into one.
                single_path = []
                for path in all_paths:
                    # Make sure all paths go left to right.
                    if path[0].x > path[-1].x:
                        path.reverse()

                    if single_path:
                        previous_vertex = single_path[-1]
                        next_vertex = path[0]

                        # Make return around the object. We must go from previous_vertex
                        # to next_vertex without touching the object. We do this by
                        # returning to a low Y value.
                        single_path.append(Vector2(previous_vertex.x, top_y))
                        single_path.append(Vector2(next_vertex.x, top_y))

                    single_path.extend(path)

                all_paths = [single_path]
                print "The single path has %d vertices." % len(single_path)

            generate_file("out", all_paths)

        thetas_file.close()

if __name__ == "__main__":
    main()
