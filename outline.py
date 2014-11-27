
import sys
import json

# pip install Pillow
from PIL import Image

class Vertex3D(object):
    def __init__(self, x, y, z, nx, ny, nz):
        self.x = x
        self.y = y
        self.z = z
        self.nx = nx
        self.ny = ny
        self.nz = nz

class Triangle3D(object):
    def __init__(self, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.vertices = [v1, v2, v3]

def render(triangles, width, height):
    bbox_miny = sys.float_info.max
    bbox_minx = sys.float_info.max
    bbox_maxx = -sys.float_info.max
    bbox_maxy = -sys.float_info.max

    for triangle in triangles:
        for vertex in triangle.vertices:
            bbox_minx = min(bbox_minx, vertex.x)
            bbox_miny = min(bbox_miny, vertex.y)
            bbox_maxx = max(bbox_maxx, vertex.x)
            bbox_maxy = max(bbox_maxy, vertex.y)

    print bbox_minx, bbox_miny, bbox_maxx, bbox_maxy

    img = Image.new("1", (width, height))

    for x in range(width/3, width*2/3):
        for y in range(height/3, height*2/3):
            img.putpixel((x, y), 1)

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
