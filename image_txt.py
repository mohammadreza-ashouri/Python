"""create measurement data from .tif file
"""
import logging, traceback
from nanoIndent import Indentation


def getImage(fileName):
  try:
    #if Hysitron file
    i = Indentation(fileName)
    if i is not None:
      i.updateSlopes()
      img = i.plot(False,False)
      return img, 'line', i.meta
    # other data routines follow here
    # .
    # .
    # .
    # if nothing successful
    return None, None, None
  except:
    logging.error("image_tif: Tif "+fileName)
    logging.error(traceback.format_exc())
    return None, None, None