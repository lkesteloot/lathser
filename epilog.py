
# Generate an Epilog PRN file for raw printing.
#
# Based on code from Ctrl-Cut by Amir Hassan <amir@viel-zu.org> and Marius
# kintel <kintel@kintel.net>.

import math

# Output for the Epilog Fusion. If false then it's the Epilog Helix.
FUSION = True


SEP = ";"

# PJL COMMANDS

# Printer job language header. Switch to PCL.
PJL_HEADER = "\x1B%%-12345X@PJL JOB NAME=%s\r\n\x1B\x45@PJL ENTER LANGUAGE=PCL \r\n"

# End job -> go back to PJL.
PJL_FOOTER = "\x1B%-12345X@PJL EOJ \r\n"


# PCL COMMANDS
# http://en.wikipedia.org/wiki/Printer_Command_Language

# Set color component one.
PCL_COLOR_COMPONENT_ONE = "\x1B*v%dA"

# I don't know what this is. It's not in the PCL manual I found.
PCL_MYSTERY1 = "\x1B&y130001300003220S"

# Probably a date, but also not in the manual. Hard-code the date,
# not much point in setting it correctly.
PCL_DATESTAMP = "\x1B&y20150311204531D"

# More mysteries.
PCL_MYSTERY2 = "\x1B&y0V\x1B&y0L\x1B&y0T\x1B&y0C\x1B&y0Z"
PCL_MYSTERY3 = "\x1B&z%dC"
PCL_MYSTERY4 = "\x1B&y%dR"

# Set autofocus on or off.
PCL_AUTOFOCUS = "\x1B&y%dA"

# Left (long-edge) offset registration.  Adjusts the position of the
# logical page across the width of the page.
PCL_OFF_X = "\x1B&l%dU"

# Top (short-edge) offset registration.  Adjusts the position of the
# logical page across the length of the page.
PCL_OFF_Y = "\x1B&l%dZ"

# Issued after a center engraving. Don't understand what it exactly does.
PCL_UPPERLEFT_X = "\x1B&l%dW"
PCL_UPPERLEFT_Y = "\x1B&l%dV"

# Resolution of the print (DPI).
PCL_PRINT_RESOLUTION = "\x1B&u%dD"

# PCL resolution for raster.
PCL_RESOLUTION = "\x1B*t%dR"

# enable center engraving
PCL_CENTER_ENGRAVE = "\x1B&y%dZ"

# enable global air assist
PCL_GLOBAL_AIR_ASSIST = "\x1B&y%dC"

# Enable air assist for raster
PCL_RASTER_AIR_ASSIST = "\x1B&z%dA"

# Position cursor absolute on the X-axis
PCL_POS_X = "\x1B*p%dX"

# Position cursor absolute on the Y-axis
PCL_POS_Y = "\x1B*p%dY"

# PCL section end
HPGL_START = "\x1B%1B"

# Reset PCL
PCL_RESET = "\x1BE"


# PCL RASTER COMMANDS

# Raster Orientation
R_ORIENTATION = "\x1B*r%dF"

# Raster power
R_POWER = "\x1B&y%dP"

# Raster speed
R_SPEED = "\x1B&z%dS"

# Bed height
R_BED_HEIGHT = "\x1B*r%dT"

# Bed width
R_BED_WIDTH = "\x1B*r%dS"

# Raster compression
R_COMPRESSION = "\x1B*b%dM"

# Raster direction (0 = down, 1 = up)
R_DIRECTION = "\x1B&y%dO"

# Start raster job
R_START = "\x1B*r1A"

# End raster job
R_END = "\x1B*rC"

# The number of unpacked bytes in the raster row
R_ROW_UNPACKED_BYTES = "\x1B*b%dA"

# The number of packed bytes in the raster row
R_ROW_PACKED_BYTES = "\x1B*b%dW"


# PCL VECTOR COMMANDS

# Initialize vector mode
V_INIT = "IN"

# Set laser pulse frequency
if FUSION:
    V_FREQUENCY = "XR%02d"
else:
    V_FREQUENCY = "XR%04d"

# Set laser power
V_POWER = "YP%03d"

# Set laser speed
V_SPEED = "ZS%03d"

# Unknown.
V_UNKNOWN1 = "XS0"
V_UNKNOWN2 = "XP1"

# HPGL COMMANDS
# http://en.wikipedia.org/wiki/HPGL

# Line Type
# NB! The Windows driver inserts a Line Type without a parameter or
# command terminator before the first Pen Up command. This doesn't
# conform to PCL/HPGL and is only used on the first issue of PU in a
# job. There seems to be no difference to using the standard command
# also for the first issue, so I use it only because the Windows
# driver does.

HPGL_LINE_TYPE = "LT"

# Pen up
HPGL_PEN_UP = "PU"

# Pen down
HPGL_PEN_DOWN = "PD"

# HPGL section end
HPGL_END = "\x1B%0B"


def generate_prn(out, doc):
    resolution = doc.getResolution()
    enableEngraving = doc.getEnableEngraving()
    enableCut = doc.getEnableCut()
    centerEngrave = doc.getCenterEngrave()
    airAssist = doc.getAirAssist()

    # Match my sample output. Doesn't matter right now anyway.
    raster_power = 50
    raster_speed = 50
    width = doc.getWidth()
    height = doc.getHeight()

    # Prthe printer job language header.
    out.write(PJL_HEADER % doc.getTitle())

    if FUSION:
        out.write(PCL_COLOR_COMPONENT_ONE % 1536)
        out.write(PCL_MYSTERY1)
        out.write(PCL_DATESTAMP)
        out.write(PCL_MYSTERY2)
    else:
        # Set autofocus on or off. For some reason off is -1. I don't
        # know what on is, but we're not supposed to use it anyway.
        out.write(PCL_AUTOFOCUS % -1)

        # Unknown purpose.
        out.write(PCL_GLOBAL_AIR_ASSIST % airAssist)

        # Enable or disable center engraving.
        out.write(PCL_CENTER_ENGRAVE % centerEngrave)

    # Left (long-edge) offset registration.  Adjusts the position of the
    # logical page across the width of the page.
    out.write(PCL_OFF_X % 0)

    # Top (short-edge) offset registration.  Adjusts the position of the
    # logical page across the length of the page.
    out.write(PCL_OFF_Y % 0)

    # Resolution of the print.
    out.write(PCL_PRINT_RESOLUTION % resolution)

    # X position = 0
    out.write(PCL_POS_X % 0)

    # Y position = 0
    out.write(PCL_POS_Y % 0)

    # PCL resolution.
    out.write(PCL_RESOLUTION % resolution)

    # Raster Orientation
    out.write(R_ORIENTATION % 0)

    if FUSION:
        out.write(PCL_MYSTERY3 % 0)

    # Raster power
    out.write(R_POWER % raster_power)

    # Raster speed
    out.write(R_SPEED % raster_speed)

    if FUSION:
        out.write(PCL_MYSTERY4 % 50)

        # Set autofocus on or off. For some reason off is -1. I don't
        # know what on is, but we're not supposed to use it anyway.
        out.write(PCL_AUTOFOCUS % -1)

    # Raster air assist.
    out.write(PCL_RASTER_AIR_ASSIST % (2 if airAssist else 0))

    # Size of the bed.
    if FUSION:
        bed_width = 32*resolution
        bed_height = 20*resolution
    else:
        bed_width = 24*resolution
        bed_height = 18*resolution
    out.write(R_BED_HEIGHT % bed_height)
    out.write(R_BED_WIDTH % bed_width)

    # Raster compression
    out.write(R_COMPRESSION % 2)

    if enableEngraving:
        # Not implemented.
        pass

    if enableCut:
        # Header for the cut.
        out.write(HPGL_START)
        out.write(V_INIT)
        out.write(SEP)

        for cut in doc.getCuts():
            generate_cut(out, cut)

        # Footer for the cut.
        out.write(HPGL_END)

    out.write(HPGL_START)
    out.write(HPGL_PEN_UP)
    out.write(PCL_RESET)
    out.write(PJL_FOOTER)

    # Pad out the remainder of the file with spaces and footer.
    if FUSION:
        out.write(" "*4090)
        out.write("FusionKYMC")
    else:
        out.write(" "*4092)
        out.write("Mini]\n")

    out.flush()

def generate_cut(out, cut):
    power_set = cut.getPower()
    speed_set = cut.getSpeed()
    freq_set = cut.getFrequency()

    # We cut the points into spans of at most 100 points.
    for spanIndex, points in enumerate(cut.getSpans(100)):
        print "Span %d with %d points" % (spanIndex, len(points))

        out.write(V_POWER % power_set)
        out.write(SEP)
        out.write(V_SPEED % speed_set)
        out.write(SEP)
        out.write(V_FREQUENCY % freq_set)
        out.write(SEP)
        out.write(V_UNKNOWN1)
        out.write(SEP)
        out.write(V_UNKNOWN2)
        out.write(SEP)
        out.write(HPGL_LINE_TYPE)

        # Move to the first point.
        firstPoint = points[0]
        out.write(HPGL_PEN_UP)
        out.write("%d,%d" % (firstPoint.x, firstPoint.y))
        out.write(SEP)

        # Draw the rest of the points.
        restPoints = points[1:]
        out.write(HPGL_PEN_DOWN)
        out.write(",".join("%d,%d" % (p.x, p.y) for p in restPoints))
        out.write(SEP)

