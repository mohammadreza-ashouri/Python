"""create measurement data from .tif file
"""
import logging, traceback
from Tif import Tif

def getMeasurement(fileName, doc):
  """
  Args:
     fileName: full path file name
     doc: supplied to guide image creation doc['type']
  """
  try:
    # try Steffen's Tif library
    i = Tif(fileName)
    if i is not None:
      if not 'no_autoCrop' in doc['type'][-1]:
        i.autoCrop()
      if "adaptive" in doc['type'][-1]:
        i.enhance("adaptive")
      else:
        i.enhance()
      if not 'no_scale' in doc['type'][-1]:
        i.addScaleBar()
      measurementType = [i.meta.pop('measurementType')] + doc['type'][2:]
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
    print("Image failure")
    print(traceback.format_exc())
    print(doc)
    logging.error("image_tif: Tif "+fileName)
    logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}