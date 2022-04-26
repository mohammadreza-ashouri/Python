"""extract data from .hdf5 file
"""
import matplotlib.pyplot as plt
import numpy as np
import h5py

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

  hdf = h5py.File(fileName)
  converter = None
  if 'converter' in hdf:
    converter = hdf['converter'].attrs['uri']
    if isinstance(converter, bytes):
      converter = converter.decode('utf-8')
    converter = converter.split('/')[-1]


  if converter in ['Micromaterials2hdf.cwl','nmd2hdf.cwl']:
    # Micromaterials indentation file
    hdf.close()
    from nanoindentation import Indentation
    i = Indentation(fileName, nuMat=0.3)
    if doc['-type'][2:] == ['indentation', 'procedure']:#: plot indentation procedure
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
      return ax1, ['svg', doc['-type'],                  i.metaVendor, i.metaUser]
    elif doc['-type'][2:] == ['indentation', 'one indent']:#: plot one indentation
      i.analyse()
      img = i.plot(False,False)
      return img, ['svg', doc['-type']+['indentation'], i.metaVendor, i.metaUser]
    else:                                               #default: plot all force-depth curves
      ax1 = plt.subplot(111)
      while True:
        i.analyse()
        ax1.plot(i.h,i.p,'-')
        if len(i.testList)==0:
          break
        i.nextTest()
      ax1.set_xlabel(r"depth [$\mathrm{\mu m}$]")
      ax1.set_ylabel(r"force [$\mathrm{mN}$]")
      ax1.set_xlim(left=0)
      ax1.set_ylim(bottom=0)
      return ax1, ['svg', doc['-type']+['indentation'], i.metaVendor, i.metaUser]


  elif converter == 'mvl2hdf.cwl':
    #Doli mvl -> hdf5 file
    ax1 = plt.subplot(111)
    if 'stacked' in hdf['converter'].attrs:
      print('stacked hdf file of multiple measurements')
      for branch in hdf:
        if branch == 'converter':
          continue
        displacement = np.array(hdf[branch].get("displacement"))
        force = np.array( hdf[branch].get("force") )
        ax1.plot(displacement, force, label=branch)
        metaVendor = {}
        for key in hdf[branch]['metadata'].attrs:  #use last branch, others overwritten
          if hdf[branch]['metadata'].attrs[key]==h5py.Empty('S1'):
            metaVendor[key] = ''
          elif isinstance(hdf[branch]['metadata'].attrs[key], np.bytes_):
            metaVendor[key] = hdf[branch]['metadata'].attrs[key].decode('UTF-8')
          else:
            metaVendor[key] = hdf[branch]['metadata'].attrs[key]
      metaUser = {'measurementType': 'Doli mvl to HDF5 file: stacked files'}
    else:
      print('hdf file of one measurement')
      displacement = np.array(hdf.get("displacement"))
      force = np.array( hdf.get("force") )
      ax1.plot(displacement, force, label=fileName)
      metaVendor = {}
      for key in hdf['metadata'].attrs:
        metaVendor[key] = hdf['metadata'].attrs[key]
      metaUser = {'measurementType': 'Doli mvl to HDF5 file'}
    ax1.set_xlabel("displacement [mm]")
    ax1.set_ylabel("force [N]")
    return ax1, ['svg', doc['-type']+['tensileTest'],  metaVendor, metaUser]


  else:
    #other datatypes follow here
    print("Unknown hdf5 file")
    if 'converter' in hdf:
      print("  Converter:", hdf['converter'].attrs['uri'])

  #final return if nothing successful
  return None, ['', [], {}, {}]
