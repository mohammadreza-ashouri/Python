"""extract data from .xls file
- MTS, Agilent, Keysight, KLA, NanomechanicsInc nanoindentation exported data
"""
import matplotlib.pyplot as plt
from nanoIndent import Indentation

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content, [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  if '-type' not in doc:
    doc['-type'] = []
  #if MTS,... nanoindentation file
  try:
    i = Indentation(fileName, verbose=1)
    if i is None:
      raise ValueError
    if doc['-type'][2:] == ['indentation', 'all']:         #: plot all curves as force-depth
      ax = plt.subplot(111)
      while len(i.testList)>1:
        ax.plot(i.h, i.p)
        i.nextTest()
      ax.set_xlabel(r"depth [$\mathrm{\mu m}$]")
      ax.set_ylabel(r"force [$\mathrm{mN}$]")
      return ax, ['svg', doc['-type'],                 i.metaVendor, i.metaUser]

    else:                                               #default: plot first force-depth curve
      i.analyse()
      img = i.plot(False,False)
      return img, ['svg', doc['-type']+['indentation'], i.metaVendor, i.metaUser]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
