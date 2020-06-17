"""create measurement data from .txt file
"""
import logging, traceback
from nanoIndent import Indentation
import matplotlib.pyplot as plt

def getMeasurement(fileName, dataType):
  """
  Args:
     fileName: full path file name
     dataType: supplied to guide image creation dataType['type']
  """
  try:
    #if Hysitron/Fischer-Scope file
    i = Indentation(fileName, verbose=1)
    if i is not None:

      if dataType['type'][-1] =='all':
        f, img = plt.subplots()
        while len(i.testList)>1:
          img.plot(i.h, i.p)
          i.nextTest()
        img.set_xlabel("depth [$\mu m$]")
        img.set_ylabel("force [$mN$]")
        measurementType = [ i.meta.pop('measurementType'),dataType['type'][-1] ]

      else:                                #default
        i.analyse()
        img = i.plot(False,False)
        measurementType = [i.meta.pop('measurementType')]

      meta = {'measurementType':measurementType,
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