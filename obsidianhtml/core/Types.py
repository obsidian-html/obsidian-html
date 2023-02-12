""" This file contains all the types used for type hinting """

from typing import Any

# SIDE-EFFECTS
# Main use of calling this function is to make something happen on the user's system
# Values might be returned, but this is more of a convenience thing, rather than the reason for
# calling the function
SystemChange = Any

# Main use of calling this function is to change a value in the picknickbasket.
# Values might be returned, but this is more of a convenience thing, rather than the reason for
# calling the function
PBChange = Any

# Main use of calling this function is to write one or multiple files to the output directory.
# Values might be returned, but this is more of a convenience thing, rather than the reason for
# calling the function
WriteExportFile = Any

# STRINGS
# --------------------------------------------------------------------------
# "Relative to root"
# An "absolute" posx string that starts with /
# It is absolute relative to a given root, whatever that might be (normally the input and/or output folder for a given operation)
RTRPosx = str

# Absolute file path, relative to the OS disk, e.g. C:\bla, /home/user/bla
OSAbsolutePosx = str
