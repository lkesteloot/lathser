
import sys
import json
import math
import collections

# pip install Pillow (https://python-pillow.github.io/)
from PIL import Image, ImageDraw
from PIL.GifImagePlugin import getheader, getdata

# https://code.google.com/p/visvis/source/browse/#hg/vvmovie
import images2gif

# https://raw.githubusercontent.com/python-pillow/Pillow/master/Scripts/gifmaker.py
import gifmaker

# What kind of image to make. Use "L" for GIF compatibility.
RASTER_MODE = "L"
RASTER_WHITE = 255

# Diameter in inches.
ROD_DIAMETER = 0.8
# Total margin as a fraction of the diameter.
MARGIN = 0.1
MODEL_DIAMETER = ROD_DIAMETER*(1 - MARGIN)

ANGLE_COUNT = 16

# What we're targeting (viewing in Chrome or cutting on the laser cutter).
TARGET_VIEW, TARGET_CUT = range(2)
TARGET = TARGET_CUT

# Final position in inches.
FINAL_X = 1.25 - 0.045
FINAL_Y = 1

RENDER_SCALE = 5

DPI = 72
SVG_WIDTH = 32*DPI
SVG_HEIGHT = 20*DPI

# "Hairline" in AI.
if TARGET == TARGET_CUT:
    STROKE_WIDTH = 0.001
    FOREGROUND_COLOR = "black"
    BACKGROUND_COLOR = "white"
else:
    STROKE_WIDTH = 1
    FOREGROUND_COLOR = "white"
    BACKGROUND_COLOR = "black"

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
        return sqrt(self.dot(self))

    def normalized(self):
        return self/self.length()

    def min(self, other):
        return Vector3(min(self.x, other.x), min(self.y, other.y), min(self.z, other.z))

    def max(self, other):
        return Vector3(max(self.x, other.x), max(self.y, other.y), max(self.z, other.z))

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
        return Vertex2D(x, y)

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
        if bbox.width()/bbox.height() < float(width)/height:
            # Left/right margins. Fit height.
            scale = height/bbox.height()
        else:
            # Bottom/top margins. Fit width.
            scale = width/bbox.width()

        offx = width/2.0 - bbox.centerx()*scale
        offy = height/2.0 - bbox.centery()*scale

        return Transform(scale, offx, offy)

    @staticmethod
    def makeIdentity():
        return Transform(1, 0, 0)

class BoundingBox(object):
    def __init__(self):
        self.miny = sys.float_info.max
        self.minx = sys.float_info.max
        self.maxx = -sys.float_info.max
        self.maxy = -sys.float_info.max

    def addPoint(self, x, y):
        self.minx = min(self.minx, x)
        self.miny = min(self.miny, y)
        self.maxx = max(self.maxx, x)
        self.maxy = max(self.maxy, y)

    def addVertex(self, vertex):
        self.addPoint(vertex.x, vertex.y)

    def addTriangle(self, triangle):
        for vertex in triangle.vertices:
            self.addVertex(vertex)

    def addMargin(self, margin):
        self.minx -= margin
        self.miny -= margin
        self.maxx += margin
        self.maxy += margin

    def width(self):
        return self.maxx - self.minx

    def height(self):
        return self.maxy - self.miny

    def centerx(self):
        return self.minx + self.width()/2

    def centery(self):
        return self.miny + self.height()/2

    def rangex(self):
        return range(int(math.floor(self.minx)), int(math.floor(self.maxx)) + 1)

    def rangey(self):
        return range(int(math.floor(self.miny)), int(math.floor(self.maxy)) + 1)

    def __str__(self):
        return "BBOX([%g,%g] - [%g,%g])" % (self.minx, self.miny, self.maxx, self.maxy)

class BoundingBox3D(object):
    def __init__(self):
        self.min = Vector3(sys.float_info.max, sys.float_info.max, sys.float_info.max)
        self.max = Vector3(sys.float_info.min, sys.float_info.min, sys.float_info.min)

    def addPoint(self, v):
        self.min = self.min.min(v)
        self.max = self.max.max(v)

    def addVertex(self, vertex):
        self.addPoint(vertex.p)

    def addTriangle(self, triangle):
        for vertex in triangle.vertices:
            self.addVertex(vertex)

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

class Vertex2D(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __str__(self):
        return "(%g,%g)" % (self.x, self.y)

    def __repr__(self):
        return str(self)

    def __neg__(self):
        return Vertex2D(-self.x, -self.y)

    def __add__(self, other):
        return Vertex2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vertex2D(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vertex2D(self.x*other, self.y*other)

    def __div__(self, other):
        return Vertex2D(self.x/other, self.y/other)

    def dot(self, other):
        return self.x*other.x + self.y*other.y

    def length(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalized(self):
        return self/self.length()

    # Angle is in radians.
    def rotated(self, angle):
        return Vertex2D(self.x*math.cos(angle) - self.y*math.sin(angle),
                      self.x*math.sin(angle) + self.y*math.cos(angle))

    # Rotated 90 counter-clockwise.
    def reciprocal(self):
        return Vertex2D(-self.y, self.x)

    # Returns angle in radians.
    def angle(self):
        return atan2(self.y, self.x)

    def flipX(self):
        return Vertex2D(-self.x, self.y)

    def flipY(self):
        return Vertex2D(self.x, -self.y)

    def to_pair(self):
        return self.x, self.y

class Vertex3D(object):
    def __init__(self, p):
        self.p = p

    def project(self, transform, angle):
        # Rotate around Z axis.
        rx = math.cos(angle)*self.p.x - math.sin(angle)*self.p.y
        ry = math.sin(angle)*self.p.x + math.cos(angle)*self.p.y
        rz = self.p.z

        x, y = transform.transform(ry, rz)

        return Vertex2D(x, y)

    def translate(self, vector3):
        return Vertex3D(self.p + vector3)

class Triangle2D(object):
    def __init__(self, vertices):
        self.vertices = vertices

class Triangle3D(object):
    def __init__(self, vertices):
        self.vertices = vertices

    def project(self, transform, angle):
        return Triangle2D([vertex.project(transform, angle) for vertex in self.vertices])

    def translate(self, vector3):
        return Triangle3D([v.translate(vector3) for v in self.vertices])

class Edge(object):
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
        self.used = False

    def __hash__(self):
        return hash((self.v1, self.v2))

    def __eq__(self, other):
        return (self.v1, self.v2) == (other.v1, other.v2)

def render(triangles, width, height, angle):
    print "Rendering at angle %g" % int(angle*180/math.pi)

    bbox = BoundingBox()

    transform = Transform.makeIdentity()

    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)
        bbox.addTriangle(triangle2d)

    # print "Model bounding box:", bbox

    # Pad so we don't run into the edge of the image.
    bbox.addMargin(bbox.width()/20)

    transform = Transform.makeMap(bbox, width, height)

    # Render.
    img = Image.new(RASTER_MODE, (width, height))
    draw = ImageDraw.Draw(img)

    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)
        tbbox = BoundingBox()
        tbbox.addTriangle(triangle2d)
        draw.polygon([(v.x, v.y) for v in triangle2d.vertices], fill=RASTER_WHITE, outline=RASTER_WHITE)

    return img, transform

def get_base_height(image):
    width, height = image.size

    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, height - 1 - y))
            if pixel != 0:
                return y

    raise Exception("base not found")

def add_base(image):
    width, height = image.size
    base_height = get_base_height(image)

    for y in range(base_height):
        for x in range(width):
            image.putpixel((x, height - 1 - y), RASTER_WHITE)

    return image

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

        vertices.extend([Vertex3D(
                Vector3(rawVertices[i*3 + 0], rawVertices[i*3 + 1], rawVertices[i*3 + 2])
                ## Vector3(rawNormals[i*3 + 0], rawNormals[i*3 + 1], rawNormals[i*3 + 2])
            ) for i in range(len(rawVertices)/3)])

        triangles.extend([Triangle3D([
            vertices[vertexOffset + face[0]],
            vertices[vertexOffset + face[1]],
            vertices[vertexOffset + face[2]]]) for face in rawFaces])

    return triangles

def angles(count):
    return [angle*math.pi*2/count for angle in range(count)]

# Return a list of paths of Vertex2D().
def get_outlines(image):
    edges = []

    # Generate edges for each pixel.
    print "Generating edges..."
    width, height = image.size
    for x in range(width - 1):
        for y in range(height - 1):
            this = image.getpixel((x, y))
            right = image.getpixel((x + 1, y))
            down = image.getpixel((x, y + 1))

            if this != right:
                edges.append(Edge(Vertex2D(x + 1, y), Vertex2D(x + 1, y + 1)))
            if this != down:
                edges.append(Edge(Vertex2D(x, y + 1), Vertex2D(x + 1, y + 1)))
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
                break
            vertices = []
            paths.append(vertices)
            edge = edges[0]
        else:
            edge = connected_edges[0]
        if edge.v1 == vertex:
            vertex = edge.v2
        else:
            vertex = edge.v1
    edges = [edge for edge in edges if not edge.used]
    print "Sequence has %d vertices, with %d edges unused." % (len(vertices), len(edges))

    return paths

def shortest_distance_to_segment(v, v1, v2):
    segment = v1 - v2
    n = segment.reciprocal().normalized()
    return math.fabs((v - v1).dot(n))

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
            dist = shortest_distance_to_segment(vertices[i], vertices[first], vertices[last])
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
    # filename = "data/My_Scan_1.json"
    filename = "data/knight.json"

    triangles = loadFile(filename)
    print "The model has %d triangles." % len(triangles)

    # Single image.
    if False:
        img, _ = render(triangles, 1024, 1024, 0)
        img = add_base(img)
        img.save("out.png")

    # Animated GIF.
    if False:
        images = [render(triangles, 256, 256, angle)[0] for angle in angles(ANGLE_COUNT)]

        fp = open("out.gif", "wb")
        gifmaker.makedelta(fp, images)
        fp.close()

        # Fails:
        ## images2gif.writeGif("out2.gif", images)

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
        triangles = [triangle.translate(-center) for triangle in triangles]

        # Find scaling factor.
        size = bbox3d.size()
        max_size = max(size.x, size.y)
        scale = MODEL_DIAMETER / max_size * DPI

        for index, angle in enumerate(angles(ANGLE_COUNT)):
            image, transform = render(triangles, 256*RENDER_SCALE, 256*RENDER_SCALE, angle)
            image = add_base(image)
            paths = get_outlines(image)
            paths = [simplify_vertices(vertices, 1) for vertices in paths]
            paths = [transform_vertices(vertices, transform, scale) for vertices in paths]
            generate_svg("out%02d.svg" % index, paths)

if __name__ == "__main__":
    main()
