# Define a procedure which generates a rectangular reinforced concrete section
# with one layer of steel evenly distributed around the perimeter and a confined core.
# 
#                       y
#                       |
#                       |
#                       |    
#             ---------------------
#             |\                 /|
#             | \---------------/ |
#             | |               | |
#             | |               | |
#  z ---------| |               | |  h
#             | |               | |
#             | |               | |
#             | /---------------\ |
#             |/                 \|
#             ---------------------
#                       b
#
# Formal arguments
#    id - tag for the section that is generated by this procedure
#    h - overall height of the section (see above)
#    b - overall width of the section (see above)
#    cover - thickness of the cover patches
#    coreID - material tag for the core patch
#    coverID - material tag for the cover patches
#    steelID - material tag for the reinforcing steel
#    numBars - number of reinforcing bars on any given side of the section
#    barArea - cross-sectional area of each reinforcing bar
#    nfCoreY - number of fibers in the core patch in the y direction
#    nfCoreZ - number of fibers in the core patch in the z direction
#    nfCoverY - number of fibers in the cover patches with long sides in the y direction
#    nfCoverZ - number of fibers in the cover patches with long sides in the z direction
#
# Notes
#    The thickness of cover concrete is constant on all sides of the core.
#    The number of bars is the same on any given side of the section.
#    The reinforcing bars are all the same size.
#    The number of fibers in the short direction of the cover patches is set to 1.
# 
# Written: Andreas Schellenberg (andreas.schellenberg@gmail.com)
# Date: June 2017

from opensees.openseespy import *

def create(id, h, b, cover, coreID, coverID, steelID, numBars, barArea, nfCoreY, nfCoreZ, nfCoverY, nfCoverZ, GJ):
    
    # The distance from the section z-axis to the edge of the cover concrete
    # in the positive y direction
    coverY = h/2.0
    
    # The distance from the section y-axis to the edge of the cover concrete
    # in the positive z direction
    coverZ = b/2.0
    
    # Determine the corresponding values from the respective axes to the
    # edge of the core concrete
    coreY = coverY - cover
    coreZ = coverZ - cover
    
    # Define the fiber section
    section("Fiber", id, "-GJ", GJ)
    
    # Define the core patch
    patch("quad", coreID, nfCoreZ, nfCoreY, -coreY, coreZ, -coreY, -coreZ, coreY, -coreZ, coreY, coreZ)
    
    # Define the four cover patches
    patch("quad", coverID, 1,        nfCoverY, -coverY,  coverZ, -coreY,   coreZ,   coreY,   coreZ,   coverY,  coverZ)
    patch("quad", coverID, 1,        nfCoverY, -coreY,  -coreZ,  -coverY, -coverZ,  coverY, -coverZ,  coreY,  -coreZ)
    patch("quad", coverID, nfCoverZ, 1,        -coverY,  coverZ, -coverY, -coverZ, -coreY,  -coreZ,  -coreY,   coreZ)
    patch("quad", coverID, nfCoverZ, 1,         coreY,   coreZ,   coreY,  -coreZ,   coverY, -coverZ,  coverY,  coverZ)
    
    # Define the steel along constant values of y (in the z direction)
    layer("straight", steelID, numBars, barArea, -coreY, coreZ, -coreY, -coreZ)
    layer("straight", steelID, numBars, barArea,  coreY, coreZ,  coreY, -coreZ)
    
    # Determine the spacing for the remaining bars in the y direction
    spacingY = (2.0*coreY)/(numBars-1)
    
    # Avoid double counting bars
    numBars = numBars-2
    
    # Define remaining steel in the y direction
    layer("straight", steelID, numBars, barArea, (coreY-spacingY),  coreZ, (-coreY+spacingY),  coreZ)
    layer("straight", steelID, numBars, barArea, (coreY-spacingY), -coreZ, (-coreY+spacingY), -coreZ)