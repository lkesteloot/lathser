
import sys
import json
import math

# pip install Pillow
from PIL import Image, ImageDraw

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

class Vertex3D(object):
    def __init__(self, x, y, z, nx, ny, nz):
        self.x = x
        self.y = y
        self.z = z
        self.nx = nx
        self.ny = ny
        self.nz = nz

    def project(self, transform):
        x, y = transform.transform(self.y, -self.z)
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

    def project(self, transform):
        return Triangle2D([vertex.project(transform) for vertex in self.vertices])

def render(triangles, width, height):
    bbox = BoundingBox()

    transform = Transform.makeIdentity()

    for triangle in triangles:
        triangle2d = triangle.project(transform)
        bbox.addTriangle(triangle2d)

    print "Model bounding box:", bbox

    # Pad so we don't run into the edge of the image.
    bbox.addMargin(bbox.width()/20)

    transform = Transform.makeMap(bbox, width, height)

    # Render.
    img = Image.new("1", (width, height))
    draw = ImageDraw.Draw(img)

    for triangle in triangles:
        triangle2d = triangle.project(transform)
        tbbox = BoundingBox()
        tbbox.addTriangle(triangle2d)
        draw.polygon([(v.x, v.y) for v in triangle2d.vertices], fill=1, outline=1)

    img.save("out.png", "PNG")

def loadFile(filename):
    data = json.load(open(filename))

    if len(data["meshes"]) != 1:
        print "Must have exactly one mesh."
        sys.exit(1)

    mesh = data["meshes"][0]
    rawVertices = mesh["vertices"]
    rawNormals = mesh["normals"]
    rawFaces = mesh["faces"]

    vertices = [Vertex3D(
        rawVertices[i*3 + 0],
        rawVertices[i*3 + 1],
        rawVertices[i*3 + 2],
        rawNormals[i*3 + 0],
        rawNormals[i*3 + 1],
        rawNormals[i*3 + 2]) for i in range(len(rawVertices)/3)]

    triangles = [Triangle3D(
        vertices[face[0]],
        vertices[face[1]],
        vertices[face[2]]) for face in rawFaces]

    return vertices, triangles

def main():
    filename = "data/LargeKnight.json"

    vertices, triangles = loadFile(filename)
    image = render(triangles, 1024, 1024)

if __name__ == "__main__":
    main()
