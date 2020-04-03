"""create measurement data from .tif file
"""
from nanoIndent import Indentation


def getImage(fileName):
  #if Hysitron file
  i = Indentation(fileName)
  i.updateSlopes()
  img = i.plot(False,False)
  return img, 'line', i.meta
