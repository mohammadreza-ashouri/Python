"""create measurement data from .tif file
"""
import logging, traceback
from Tif import Tif

def getImage(fileName, metaData):
  """
  Args:
     fileName: full path file name
     metaData: can be supplied to guide image creation metaData['measurementType'],metaData['plotType']
  """
  try:
    # try Steffen's Tif library
    i = Tif(fileName)
    if i is not None:
      i.enhance()
      i.addScaleBar()
      return i.image, 'waves', i.meta
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