
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
MODE = "L"
WHITE = 255

# "Hairline" in AI.
STROKE_WIDTH = 0.001
STROKE_WIDTH = 1

class Transform(object):
    # The transform takes model coordinate (x,y) and computes (x*scale + offx,
    # y*scale+offy).
    def __init__(self, scale, offx, offy):
        self.scale = scale
        self.offx = offx
        self.offy = offy

    def transform(self, x, y):
        return x*self.scale + self.offx, y*self.scale + self.offy

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
    def __init__(self, x, y, z, nx, ny, nz):
        self.x = x
        self.y = y
        self.z = z
        self.nx = nx
        self.ny = ny
        self.nz = nz

    def project(self, transform, angle):
        # Rotate around Z axis.
        rx = math.cos(angle)*self.x - math.sin(angle)*self.y
        ry = math.sin(angle)*self.x + math.cos(angle)*self.y
        rz = self.z

        x, y = transform.transform(ry, -rz)

        return Vertex2D(x, y)

class Triangle2D(object):
    def __init__(self, vertices):
        self.vertices = vertices

class Triangle3D(object):
    def __init__(self, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.vertices = [v1, v2, v3]

    def project(self, transform, angle):
        return Triangle2D([vertex.project(transform, angle) for vertex in self.vertices])

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
        triangle2d = triangle.project(transform, 0)
        bbox.addTriangle(triangle2d)

    # print "Model bounding box:", bbox

    # Pad so we don't run into the edge of the image.
    bbox.addMargin(bbox.width()/20)

    transform = Transform.makeMap(bbox, width, height)

    # Render.
    img = Image.new(MODE, (width, height))
    draw = ImageDraw.Draw(img)

    for triangle in triangles:
        triangle2d = triangle.project(transform, angle)
        tbbox = BoundingBox()
        tbbox.addTriangle(triangle2d)
        draw.polygon([(v.x, v.y) for v in triangle2d.vertices], fill=WHITE, outline=WHITE)

    return img

def loadFile(filename):
    data = json.load(open(filename))

    vertices = []
    triangles = []

    for mesh in data["meshes"]:
        rawVertices = mesh["vertices"]
        rawNormals = mesh["normals"]
        rawFaces = mesh["faces"]

        vertexOffset = len(vertices)

        vertices.extend([Vertex3D(
            rawVertices[i*3 + 0],
            rawVertices[i*3 + 1],
            rawVertices[i*3 + 2],
            rawNormals[i*3 + 0],
            rawNormals[i*3 + 1],
            rawNormals[i*3 + 2]) for i in range(len(rawVertices)/3)])

        triangles.extend([Triangle3D(
            vertices[vertexOffset + face[0]],
            vertices[vertexOffset + face[1]],
            vertices[vertexOffset + face[2]]) for face in rawFaces])

    return triangles

def angles(count):
    return [angle*math.pi*2/count for angle in range(count)]

# Return a list of Vertex2D().
def get_outline(image):
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
    vertices = []
    edge = edges[0]
    vertices.append(edge.v1)
    vertex = edge.v2
    while True:
        edge.used = True
        vertices.append(vertex)
        connected_edges = [edge for edge in edgemap[vertex] if not edge.used]
        if not connected_edges:
            break
            edges = [edge for edge in edges if not edge.used]
            if not edges:
                break
            edge = edges[0]
        else:
            edge = connected_edges[0]
        if edge.v1 == vertex:
            vertex = edge.v2
        else:
            vertex = edge.v1
    edges = [edge for edge in edges if not edge.used]
    print "Sequence has %d vertices, with %d edges unused." % (len(vertices), len(edges))

    return vertices

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

def generate_svg(filename, image, vertices):
    width, height = image.size
    scale = 5
    out = open(filename, "w")
    out.write("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
"http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd" [
<!ENTITY ns_svg "http://www.w3.org/2000/svg">
]>
<svg xmlns="&ns_svg;" width="%d" height="%d" overflow="visible" style="background: black">
""" % (width*scale, height*scale))
    out.write("""<polyline fill="none" stroke="%s" stroke-width="%g" points=" """ % ("white", STROKE_WIDTH))
    for vertex in vertices:
        out.write(" %g,%g" % (vertex.x*scale, (height - vertex.y)*scale))
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

    if False:
        img = render(triangles, 1024, 1024)
        img.save("out.png")

    if False:
        images = [render(triangles, 256, 256, angle) for angle in angles(20)]

        fp = open("out.gif", "wb")
        gifmaker.makedelta(fp, images)
        fp.close()

        # Fails:
        ## images2gif.writeGif("out2.gif", images)

    if True:
        image = render(triangles, 256, 256, 0)
        vertices = get_outline(image)
        vertices = simplify_vertices(vertices, 1)
        print "Have %d vertices after simplification." % len(vertices)
        generate_svg("out.svg", image, vertices)

if __name__ == "__main__":
    main()
