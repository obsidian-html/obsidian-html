''' This file contains all the types used for type hinting '''

from typing import Any

# SIDE-EFFECTS
# Main use of calling this function is to make something happen on the user's system
# Values might be returned, but this is more of a convenience thing, than the reason for 
# calling the function
SystemChange = Any

# STRINGS
# --------------------------------------------------------------------------
# "Relative to root"
# An "absolute" posx string that starts with / 
# It is absolute relative to a given root, whatever that might be (normally the input and/or output folder for a given operation)
RTRPosx = str

# Absolute file path, relative to the OS disk, e.g. C:\bla, /home/user/bla
OSAbsolutePosx = str