"""create measurement data from .txt file
"""
import matplotlib.pyplot as plt
from nanoIndent import Indentation

def getMeasurement(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['type']

  Returns:
    list: image, [('png'|'jpg'|'svg'), type, metaVendor, metaCustom]
  """
  #if Hysitron/Fischer-Scope file
  try:
    i = Indentation(fileName, verbose=1)
    if i is None:
      raise ValueError
    if doc['type'][2:] == ['indentation', 'all']:         #: plot all curves as force-depth
      ax = plt.subplot(111)
      while len(i.testList)>1:
        ax.plot(i.h, i.p)
        i.nextTest()
      ax.set_xlabel(r"depth [$\mathrm{\mu m}$]")
      ax.set_ylabel(r"force [$\mathrm{mN}$]")
      return ax, ['svg', doc['type'],                  {}, i.meta]

    else:                                               #default: plot first force-depth curve
      i.analyse()
      img = i.plot(False,False)
      return img, ['svg', doc['type']+['indentation'], {}, i.meta]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
