"""create measurement data from .txt file
"""
import logging, traceback
import matplotlib.pyplot as plt
from nanoIndent import Indentation

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, ('png','jpg','svg'), dictionary of metadata
  """
  try:
    #if Hysitron/Fischer-Scope file
    i = Indentation(fileName, verbose=1)
    if i is not None:

      if doc['type'][-1] =='all':       #measurement type 'all'
        _, img = plt.subplots()
        while len(i.testList)>1:
          img.plot(i.h, i.p)
          i.nextTest()
        img.set_xlabel(r"depth [$\mu m$]")
        img.set_ylabel(r"force [$mN$]")
        measurementType = [ i.meta.pop('measurementType'),doc['type'][-1] ]

      else:                                #default
        i.analyse()
        img = i.plot(False,False)
        measurementType = [i.meta.pop('measurementType')]

      meta = {'measurementType':measurementType,
              'metaVendor':i.meta,
              'metaUser':i.getDictionary()}
      return img, 'svg', meta
    # other data routines follow here
    # .
    # .
    # .
    # if nothing successful
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
  except:
    logging.error('extractor txt: '+fileName+' not a measurement')
    #logging.error(traceback.format_exc())
    return None, None, {'measurementType':[],'metaVendor':{},'metaUser':{}}
