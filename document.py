
# Encapsulates a document to be printed to the laser printer.

class Document(object):
    def __init__(self, title):
        self.title = title
        self.cuts = []
        self.rasters = []

    # Object of the Cut class.
    def addCut(self, cut):
        self.cuts.append(cut)

    # Object of the Raster class.
    def addRaster(self, raster):
        self.rasters.append(raster)

    # Pixels per inch.
    def getResolution(self):
        # Max this out because we can only generate integer cut points.
        # return 1200

        # Match Fusion default.
        return 600

    # Whether this doc has engravings (raster).
    def getEnableEngraving(self):
        return len(self.rasters) > 0

    # Whether this doc has cuts (vector).
    def getEnableCut(self):
        return len(self.cuts) > 0

    def getCenterEngrave(self):
        # We never center anything automatically.
        return False

    def getAirAssist(self):
        # I assume we always want this on. If this is the air pipe aimed
        # right at the cut, then perhaps we could turn this off to reduce
        # charring.
        return True

    # Bed size.
    def getWidth(self):
        return 24*self.getResolution()

    # Bed size.
    def getHeight(self):
        return 18*self.getResolution()

    def getAutoFocus(self):
        # We never want this.
        return False

    def getTitle(self):
        return self.title

    def getCuts(self):
        return self.cuts

    def getRasters(self):
        return self.rasters

