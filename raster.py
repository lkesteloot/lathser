
# Encapsulates an image to be engraved in raster mode.
class Raster(object):
    # Pass in a PIL Image object, its upper-left position, and power/frequency the
    # same way specified for Cut.
    def __init__(self, image, x, y, speed, power):
        self.image = image
        self.x = x
        self.y = y

        # XXX These are currently ignored. They're set at the start of the whole
        # document. I don't know if I can set them between rasters.
        self.speed = speed
        self.power = power

