"""create measurement data from .tif file
"""
import logging, traceback
from Tif import Tif

def getMeasurement(fileName, dataType):
  """
  Args:
     fileName: full path file name
     dataType: supplied to guide image creation dataType['type']
  """
  try:
    # try Steffen's Tif library
    i = Tif(fileName)
    if i is not None:
      if dataType['type'][-1] =='maximum Contrast':
        i.enhance('a')
        measurementType = dataType['type'][1:]
      else:                                #default
        i.enhance()
        i.addScaleBar()
        measurementType = [i.meta.pop('measurementType')]
      meta = {'measurementType':measurementType,
              'metaVendor':i.meta,
              'metaUser':{}}
      return i.image, 'jpg', meta
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