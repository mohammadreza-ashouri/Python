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
    list: image, [('png'|'jpg'|'svg'), type, metaVendor, metaUser]
  """
  #if Hysitron/Fischer-Scope file
  try:
    i = Indentation(fileName, verbose=1)
    if i is None:
      raise ValueError
    if doc['type'][2:] == ['indentation', 'procedure']:#: plot indentation procedure
      ax1 = plt.subplot(111)
      ax2 = ax1.twinx()
      ax1.plot(i.t, i.p, c='C0', label='force')
      ax2.plot(i.t, i.h, c='C1', label='depth')
      ax1.legend(loc=2)
      ax2.legend(loc=1)
      ax1.set_xlabel(r"time [$\mathrm{s}$]")
      ax1.set_ylabel(r"force [$\mathrm{mN}$]")
      ax2.set_ylabel(r"depth [$\mathrm{\mu m}$]")
      ax1.set_ylim(bottom=0)
      ax2.set_ylim(bottom=0)
      return ax1, ['svg', doc['type'],                  {}, i.meta]

    else:                                               #default: plot force-depth curve
      i.analyse()
      img = i.plot(False,False)
      return img, ['svg', doc['type']+['indentation'], {}, i.meta]
  except:
    pass

  #other datatypes follow here
  #...

  #final return if nothing successful
  return None, ['', [], {}, {}]
