
# Generate an Epilog PRN file for raw printing.
#
# Based on code from Ctrl-Cut by Amir Hassan <amir@viel-zu.org> and Marius
# kintel <kintel@kintel.net>.

import math


SEP = ";"

# PJL COMMANDS

# Printer job language header. Switch to PCL.
PJL_HEADER = "\x1B%%-12345X@PJL JOB NAME=%s\r\n\x1B\x45@PJL ENTER LANGUAGE=PCL \r\n"

# End job -> go back to PJL.
PJL_FOOTER = "\x1B%-12345X@PJL EOJ \r\n"


# PCL COMMANDS
# http://en.wikipedia.org/wiki/Printer_Command_Language

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

# Resolution of the print.
PCL_PRINT_RESOLUTION = "\x1B&u%dD"

# PCL resolution.
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
PCL_RESET = "\x1B\x45"


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
V_FREQUENCY = "XR%04d"

# Set laser power
V_POWER = "YP%03d"

# Set laser speed
V_SPEED = "ZS%03d"


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

    raster_power = 1
    raster_speed = 100
    width = doc.getWidth()
    height = doc.getHeight()
    autoFocus = doc.getAutoFocus()

    # Prthe printer job language header.
    out.write(PJL_HEADER % doc.getTitle())

    # Set autofocus on or off.
    out.write(PCL_AUTOFOCUS % autoFocus)

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

    # Raster power
    out.write(R_POWER % raster_power)

    # Raster speed
    out.write(R_SPEED % raster_speed)

    # Raster air assist.
    out.write(PCL_RASTER_AIR_ASSIST % (2 if airAssist else 0))

    # Size of the bed.
    out.write(R_BED_HEIGHT % height)
    out.write(R_BED_WIDTH % width)

    # Raster compression
    out.write(R_COMPRESSION % 2)

    if enableEngraving:
        # Not implemented.
        pass

    if enableCut:
        for cut in doc.getCuts():
            generate_cut(out, cut)

    out.write(HPGL_START)
    out.write(HPGL_PEN_UP)
    out.write(PCL_RESET)
    out.write(PJL_FOOTER)

    # Pad out the remainder of the file with spaces and footer.
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
        # Separate the spans.
        if spanIndex > 0:
            out.write(SEP)

        # Header for the cut.
        out.write(HPGL_START)
        out.write(V_INIT)
        out.write(SEP)
        out.write(V_POWER % power_set)
        out.write(SEP)
        out.write(V_SPEED % speed_set)
        out.write(SEP)
        out.write(V_FREQUENCY % freq_set)
        out.write(SEP)

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

        # Footer for the cut.
        out.write(HPGL_END)

