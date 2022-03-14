"""extract data from .ser file
"""
import os, struct, traceback
import numpy as np
import matplotlib.pyplot as plt

def use(fileName, doc):
  """
  Args:
     fileName (string): full path file name
     doc (dict): supplied to guide image creation doc['-type']

  Returns:
    list: image|content  [('png'|'jpg'|'svg'|'text'), type, metaVendor, metaUser]
  """
  # my default
  if len(doc['-type']) <= 3:
    doc['-type'] = ['measurement', 'TEM', 'ser', 'crop overlight']

  try:
    fIn   = open(fileName,'br')
    header = fIn.read(562)
    #header has metadata saved in different dTypes
    #pixelSize might be also saved in 554 and 558
    dataSize = struct.unpack('i',header[15:19])[0]
    metaVendor = {'dataSize':dataSize}
    #data
    imageSize= int(np.sqrt(dataSize))
    formatString = str(dataSize)+'H'
    data = fIn.read(struct.calcsize(formatString))
    data = np.array(struct.unpack(formatString, data))
    data = np.reshape(data, (imageSize,imageSize))
    #the footer has more metadata

    mask = data>512 #crop above 512 as sensor might not be faulty
    metaUser = {'overLightPixel': len(mask[mask])}
    if doc['-type'][2:] == ['ser', 'crop overlight']: #: crop pixel that got too much intensity
      data[mask] = 512

    if doc['-type'][2:] == ['ser', 'default']:             #: default image, no change
      pass

    #plot
    ax = plt.subplot(111)
    ax.imshow(data, cmap='gray')
    ax.axis('off')
    return ax, ['jpg', [], metaVendor, metaUser]

    # else:
    #   raise ValueError  #if header has wrong format

  except:
    print(traceback.format_exc())
    pass

  # other data routines follow here
  # ....

  #final return if nothing successful
  return None, ['', [], {}, {}]
