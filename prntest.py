
from document import Document
from cut import Cut
from raster import Raster
import epilog
from vector import Vector2
from PIL import Image, ImageDraw

def draw_circle(draw, x, y, r, c):
    draw.ellipse([x - r, y - r, x + r, y + r], c)

def vector_test():
    doc = Document("Untitled-1")

    cut = Cut(4, 100, 50)
    cut.points = [
        Vector2(1200, 1300),
        Vector2(1400, 1500),
    ]
    doc.addCut(cut)

    cut = Cut(4, 100, 50)
    cut.points = [
        Vector2(1200 + 600*10, 1300 + 200),
        Vector2(1400 + 600*10, 1500 + 200),
    ]
    doc.addCut(cut)

    cut = Cut(50, 100, 50)
    cut.points = [
        Vector2(1200 + 200, 1300 + 200),
        Vector2(1400 + 200, 1500 + 200),
    ]
    doc.addCut(cut)

    return doc

def raster_test():
    doc = Document("Untitled-1")

    width = 100
    height = 100
    image = Image.new("L", (width, height))
    draw = ImageDraw.Draw(image)
    draw_circle(draw, width/2, height/2, width/2 - 10, 255)
    draw_circle(draw, width*3/4, height/4, width/5, 0)
    image.save("prntest.png")

    raster = Raster(image, 100, 100, 100, 100)
    doc.addRaster(raster)

    return doc

def main():
    # doc = vector_test()
    doc = raster_test()

    out = open("prntest.prn", "wb")
    epilog.generate_prn(out, doc)
    out.close()

if __name__ == "__main__":
    main()
