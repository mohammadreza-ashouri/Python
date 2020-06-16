"""create measurement data from .tif file
"""
import logging, traceback
from nanoIndent import Indentation


def getMeasurement(fileName, dataType):
  """
  Args:
     fileName: full path file name
     dataType: supplied to guide image creation dataType['type']
  """
  try:
    #if Hysitron file
    i = Indentation(fileName, verbose=1)
    if i is not None:
      i.analyse()
      img = i.plot(False,False)
      measurementType = i.meta.pop('measurementType')
      meta = {'measurementType':[measurementType],
              'metaVendor':i.meta,
              'metaUser':{}}
      return img, 'svg', meta
    # other data routines follow here
    # .
    # .
    # .
    # if nothing successful
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
  except:
    logging.error("image_tif: Tif "+fileName)
    logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}