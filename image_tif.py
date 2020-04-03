"""create measurement data from .tif file
"""
from Tif import Tif

#TODO structure with try: except: and that i is not none
def getImage(fileName):
  i = Tif(fileName)
  i.enhance()
  i.addScaleBar()
  return i.image, 'waves', i.meta
