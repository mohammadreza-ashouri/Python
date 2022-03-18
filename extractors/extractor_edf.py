"""extract data from .edf file
"""
import os, struct, traceback
import numpy as np
import matplotlib.pyplot as plt
import mne

def use(fileName, doc={}):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content  [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  if len(doc['-type']) <= 3:
    doc['-type'] = ['measurement', 'edf', 'ecg', 'heart']

  try:
    data = mne.io.read_raw_edf(fileName)
    metaVendor = {'frequency':data.info['sfreq'], 'date': data.info['meas_date'].isoformat()}
    print(metaVendor)
    metaUser = {}

    rawData = data.get_data()
    startData = 10000
    endData =   rawData.shape[1]-15000
    ax = None
    # it has to have the same line as following, and ecg is the general type which has to be the same here
    if doc['-type'][2:] == ['ecg', 'both']: #: show heart and breathing rate
      ax = plt.subplot(211)
      ax.plot(rawData[1,startData:endData], label='heart rate')
      ax.text(0.1,0.8,'heart rate',transform=ax.transAxes, fontsize=16)
      ax.set_xticks([],[])
      ax = plt.subplot(212)
      ax.plot(rawData[2,startData:endData], label='breathing rate')
      ax.text(0.1,0.8,'breathing rate',transform=ax.transAxes, fontsize=16)
      ax.set_xticks([],[])
    if doc['-type'][2:] == ['ecg', 'heart']: #: show heart rate
      ax = plt.subplot(111)
      ax.plot(rawData[1,startData:endData], label='heart rate')
      ax.text(0.1,0.8,'heart rate',transform=ax.transAxes, fontsize=16)
      ax.set_xticks([],[])
    if doc['-type'][2:] == ['ecg', 'breath']: #: show breathing rate
      ax = plt.subplot(111)
      ax.plot(rawData[2,startData:endData], label='breathing rate')
      ax.text(0.1,0.8,'breathing rate',transform=ax.transAxes, fontsize=16)
      ax.set_xticks([],[])
    return ax, ['svg', doc['-type'], metaVendor, metaUser]

    # else:
    #   raise ValueError  #if header has wrong format

  except:
    print(traceback.format_exc())

  # other data routines follow here
  # ....

  #final return if nothing successful
  return None, ['', [], {}, {}]
