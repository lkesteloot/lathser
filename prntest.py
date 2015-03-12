
from document import Document
from cut import Cut
import epilog
from vector import Vector2

def main():
    doc = Document("Untitled-1")
    dpi = doc.getResolution()

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

    out = open("out.prn", "wb")
    epilog.generate_prn(out, doc)
    out.close()

if __name__ == "__main__":
    main()
