
# Encapsulates a single continuous cut to be printed to the laser printer.
class Cut(object):
    def __init__(self, speed, power, frequency):
        self.speed = speed
        self.power = power
        self.frequency = frequency

        # Array of Vector2D objects.
        self.points = []

    def getSpeed(self):
        return self.speed

    def getPower(self):
        return self.power

    def getFrequency(self):
        return self.frequency

    def getSpans(self, maxPoints):
        spans = []
        points = self.points[:]

        while points:
            spans.append(points[:maxPoints])

            # Overlap by one point.
            points = points[maxPoints - 1:]

        return spans

