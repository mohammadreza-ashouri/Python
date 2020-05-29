"""create measurement data from .tif file
"""
import logging, traceback
from nanoIndent import Indentation


def getImage(fileName, dataType):
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
              'metaSystem':i.meta,
              'metaUser':{}}
      return img, 'line', meta
    # other data routines follow here
    # .
    # .
    # .
    # if nothing successful
    return None, None, {'measurementType':[],'metaSystem':{},'metaUser':{}}
  except:
    logging.error("image_tif: Tif "+fileName)
    logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaSystem':{},'metaUser':{}}